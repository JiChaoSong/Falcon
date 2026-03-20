import json
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from sqlalchemy import Select, false
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.models import Case, CaseStatusEnum, Project
from app.schemas import case as schemas
from app.services.access_control_service import AccessControlService
from app.services.base_service import BaseService


class CaseImportService:
    def __init__(self, db: Session):
        self.db = db
        self.access_control = AccessControlService(db)
        self.base_service = BaseService(db, Case)

    def preview(self, data: schemas.CaseImportPreviewRequest) -> dict[str, Any]:
        project = self._get_project(data.project_id)
        items = self._parse_items(data)
        enriched_items = self._attach_duplicate_flags(data.project_id, items)
        duplicate_count = sum(1 for item in enriched_items if item["exists"])

        return {
            "project_id": project.id,
            "project_name": project.name,
            "source_type": data.source_type.value,
            "total_count": len(enriched_items),
            "duplicate_count": duplicate_count,
            "importable_count": len(enriched_items) - duplicate_count,
            "results": enriched_items,
        }

    def commit(self, data: schemas.CaseImportCommitRequest) -> dict[str, Any]:
        project = self._get_project(data.project_id)
        if not data.items:
            raise ParamException("请至少选择一个待导入用例")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        created_case_ids: list[int] = []
        failed_items: list[dict[str, str]] = []

        for item in data.items:
            try:
                existing_case = self._find_existing_case(data.project_id, item.method, item.url)
                if existing_case:
                    if data.conflict_policy == schemas.CaseImportConflictPolicyEnum.SKIP:
                        skipped_count += 1
                        continue

                    self._update_existing_case(existing_case, project.name, item, data.default_status)
                    updated_count += 1
                    continue

                new_case = Case(
                    name=item.name,
                    type="http",
                    project_id=project.id,
                    project=project.name,
                    method=item.method,
                    url=item.url,
                    description=item.description,
                    status=data.default_status,
                    headers=item.headers,
                    body=item.body,
                    expected_status=item.expected_status,
                )
                self.db.add(new_case)
                self.db.flush()
                created_count += 1
                created_case_ids.append(new_case.id)
            except Exception as exc:
                failed_count += 1
                failed_items.append({
                    "name": item.name,
                    "method": item.method,
                    "url": item.url,
                    "reason": str(exc),
                })

        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise ParamException(f"导入用例失败: {str(exc)}")

        return {
            "project_id": project.id,
            "project_name": project.name,
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "created_case_ids": created_case_ids,
            "failed_items": failed_items,
        }

    def _get_project(self, project_id: int) -> Project:
        self.access_control.ensure_project_manage_access(project_id)
        project = self.db.execute(
            Select(Project).where(
                Project.id == project_id,
                Project.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not project:
            raise ParamException("项目不存在")
        return project

    def _parse_items(self, data: schemas.CaseImportPreviewRequest) -> list[dict[str, Any]]:
        document = self._load_document(data)
        items = self._parse_openapi_document(document)
        if not items:
            raise ParamException("未解析到可导入的接口")
        return items

    def _load_document(self, data: schemas.CaseImportPreviewRequest) -> dict[str, Any]:
        raw_content = ""

        if data.source_type == schemas.CaseImportSourceEnum.OPENAPI_URL:
            if not data.source_url:
                raise ParamException("请输入 OpenAPI 文档地址")
            try:
                with urlopen(data.source_url, timeout=10) as response:
                    raw_content = response.read().decode("utf-8")
            except URLError as exc:
                raise ParamException(f"读取 OpenAPI 文档失败: {str(exc)}")
        else:
            raw_content = (data.document_content or "").strip()
            if not raw_content:
                raise ParamException("请输入 OpenAPI 文档内容")

        try:
            return json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ParamException(f"OpenAPI 文档解析失败: {str(exc)}")

    def _parse_openapi_document(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        paths = document.get("paths")
        if not isinstance(paths, dict) or not paths:
            raise ParamException("OpenAPI 文档缺少有效的 paths 配置")

        base_url = self._resolve_base_url(document)
        items: list[dict[str, Any]] = []
        http_methods = {"get", "post", "put", "delete", "patch", "head", "options"}

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if method.lower() not in http_methods or not isinstance(operation, dict):
                    continue

                name = (
                    operation.get("summary")
                    or operation.get("operationId")
                    or f"{method.upper()} {path}"
                )
                description = operation.get("description") or operation.get("summary")
                tags = [str(tag) for tag in operation.get("tags", []) if tag]
                headers = self._extract_headers(path_item, operation)
                body = self._extract_request_body(operation)
                expected_status = self._extract_expected_status(operation)

                items.append({
                    "name": str(name).strip(),
                    "method": method.upper(),
                    "url": self._build_request_url(base_url, path),
                    "description": str(description).strip() if description else None,
                    "tags": tags,
                    "headers": headers,
                    "body": body,
                    "expected_status": expected_status,
                })

        return items

    def _resolve_base_url(self, document: dict[str, Any]) -> str:
        servers = document.get("servers")
        if isinstance(servers, list) and servers:
            first_server = servers[0]
            if isinstance(first_server, dict) and first_server.get("url"):
                return str(first_server["url"]).rstrip("/")

        host = document.get("host")
        base_path = str(document.get("basePath") or "").rstrip("/")
        schemes = document.get("schemes") or ["http"]
        if host:
            scheme = schemes[0] if isinstance(schemes, list) and schemes else "http"
            return f"{scheme}://{host}{base_path}"

        return ""

    def _build_request_url(self, base_url: str, path: str) -> str:
        normalized_path = path if str(path).startswith("/") else f"/{path}"
        if not base_url:
            return normalized_path
        return f"{base_url}{normalized_path}"

    def _extract_headers(self, path_item: dict[str, Any], operation: dict[str, Any]) -> list[dict[str, str]]:
        parameters = []
        for source in (path_item.get("parameters"), operation.get("parameters")):
            if isinstance(source, list):
                parameters.extend(source)

        headers: list[dict[str, str]] = []
        for parameter in parameters:
            if not isinstance(parameter, dict) or parameter.get("in") != "header":
                continue
            headers.append({
                "name": str(parameter.get("name") or ""),
                "value": self._stringify_example(
                    parameter.get("example") or parameter.get("default") or ""
                ),
            })
        return [item for item in headers if item["name"]]

    def _extract_request_body(self, operation: dict[str, Any]) -> str | None:
        request_body = operation.get("requestBody")
        if isinstance(request_body, dict):
            content = request_body.get("content")
            if isinstance(content, dict):
                for media_type in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
                    media_config = content.get(media_type)
                    if isinstance(media_config, dict):
                        example = media_config.get("example")
                        if example is not None:
                            return self._serialize_body(example)
                        examples = media_config.get("examples")
                        if isinstance(examples, dict):
                            for example_item in examples.values():
                                if isinstance(example_item, dict) and example_item.get("value") is not None:
                                    return self._serialize_body(example_item["value"])
                        schema = media_config.get("schema")
                        generated = self._generate_schema_example(schema)
                        if generated is not None:
                            return self._serialize_body(generated)

        parameters = operation.get("parameters")
        if isinstance(parameters, list):
            for parameter in parameters:
                if not isinstance(parameter, dict) or parameter.get("in") != "body":
                    continue
                if parameter.get("example") is not None:
                    return self._serialize_body(parameter["example"])
                generated = self._generate_schema_example(parameter.get("schema"))
                if generated is not None:
                    return self._serialize_body(generated)

        return None

    def _extract_expected_status(self, operation: dict[str, Any]) -> str | None:
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            return None

        prioritized = [code for code in responses.keys() if str(code).startswith("2")]
        if prioritized:
            return str(sorted(prioritized)[0])

        for code in responses.keys():
            return str(code)
        return None

    def _generate_schema_example(self, schema: Any) -> Any:
        if not isinstance(schema, dict):
            return None

        if schema.get("example") is not None:
            return schema.get("example")

        schema_type = schema.get("type")
        if schema_type == "object":
            properties = schema.get("properties") or {}
            return {
                str(key): self._generate_schema_example(value)
                for key, value in properties.items()
            }
        if schema_type == "array":
            item_example = self._generate_schema_example(schema.get("items") or {})
            return [item_example] if item_example is not None else []
        if schema_type == "integer":
            return 0
        if schema_type == "number":
            return 0
        if schema_type == "boolean":
            return False
        if schema_type == "string":
            return ""
        return None

    def _serialize_body(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)

    def _stringify_example(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    def _attach_duplicate_flags(self, project_id: int, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched_items: list[dict[str, Any]] = []
        for item in items:
            existing_case = self._find_existing_case(project_id, item["method"], item["url"])
            enriched_items.append({
                **item,
                "exists": existing_case is not None,
                "duplicate_case_id": existing_case.id if existing_case else None,
                "duplicate_case_name": existing_case.name if existing_case else None,
            })
        return enriched_items

    def _find_existing_case(self, project_id: int, method: str, url: str) -> Case | None:
        return self.db.execute(
            Select(Case).where(
                Case.project_id == project_id,
                Case.method == method,
                Case.url == url,
                Case.is_deleted == false(),
            )
        ).scalar_one_or_none()

    def _update_existing_case(
        self,
        existing_case: Case,
        project_name: str,
        item: schemas.CaseImportItem,
        default_status: CaseStatusEnum,
    ) -> None:
        existing_case.name = item.name
        existing_case.type = "http"
        existing_case.project = project_name
        existing_case.method = item.method
        existing_case.url = item.url
        existing_case.description = item.description
        existing_case.status = default_status
        existing_case.headers = item.headers
        existing_case.body = item.body
        existing_case.expected_status = item.expected_status
