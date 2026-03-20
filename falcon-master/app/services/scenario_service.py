#!/user/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum
from typing import Any, Dict, List, Optional

import logging
from sqlalchemy import Delete, Select, String, Text, cast, false, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.models import Case, Scenario, ScenarioCase
from app.schemas import scenario as schemas
from app.services.access_control_service import AccessControlService
from app.services.base_service import BaseService


class ScenarioService(BaseService[Scenario, schemas.ScenarioCreate, schemas.ScenarioUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, Scenario)
        self.logger = logging.getLogger(__name__)
        self.access_control = AccessControlService(db)

    def _get_scenario_by_id(self, scenario_id: int) -> Optional[Scenario]:
        scenario = self.db.execute(
            Select(Scenario).where(
                Scenario.id == scenario_id,
                Scenario.is_deleted == false(),
            )
        ).scalar_one_or_none()

        if not scenario:
            self.logger.error(f"Scenario not found: {scenario_id}")
            raise ParamException("场景不存在")

        self.access_control.ensure_project_view_access(scenario.project_id)
        return scenario

    def _validate_scenario_name_unique(
        self,
        name: str,
        exclude_scenario_id: int | None = None,
        project_id: int | None = None,
    ) -> None:
        if not name:
            return

        query = Select(Scenario).where(
            Scenario.name == name,
            Scenario.is_deleted == false(),
        )

        if project_id:
            query = query.where(Scenario.project_id == project_id)

        if exclude_scenario_id:
            query = query.where(Scenario.id != exclude_scenario_id)

        existing_scenario = self.db.execute(query).scalar_one_or_none()
        if existing_scenario:
            raise ParamException("场景名称已存在")

    def _build_cases_map(
        self,
        scenario_ids: List[int],
        include_details: bool = False,
    ) -> Dict[int, List[Dict[str, Any]]]:
        if not scenario_ids:
            return {}

        scenario_cases = self.db.execute(
            Select(ScenarioCase).where(
                ScenarioCase.scenario_id.in_(scenario_ids),
                ScenarioCase.is_deleted == false(),
            ).order_by(ScenarioCase.scenario_id.asc(), ScenarioCase.order.asc(), ScenarioCase.id.asc())
        ).scalars().all()

        cases_map: Dict[int, List[Dict[str, Any]]] = {scenario_id: [] for scenario_id in scenario_ids}
        case_ids = sorted({item.case_id for item in scenario_cases})
        case_detail_map: Dict[int, Dict[str, Any]] = {}

        if case_ids:
            cases = self.db.execute(
                Select(Case).where(
                    Case.id.in_(case_ids),
                    Case.is_deleted == false(),
                )
            ).scalars().all()
            case_detail_map = {item.id: item.to_dict() for item in cases}

        for relation in scenario_cases:
            detail = case_detail_map.get(relation.case_id, {})
            payload = {
                "id": relation.case_id,
                "case_id": relation.case_id,
                "name": detail.get("name") or f"Case {relation.case_id}",
                "method": detail.get("method"),
                "url": detail.get("url") or "",
                "status": detail.get("status") or "draft",
                "order": relation.order,
                "weight": relation.weight,
            }

            if include_details:
                payload.update(
                    {
                        "type": detail.get("type") or "http",
                        "project_id": detail.get("project_id") or 0,
                        "project": detail.get("project") or "",
                        "description": detail.get("description"),
                        "headers": detail.get("headers"),
                        "body": detail.get("body"),
                        "expected_status": detail.get("expected_status"),
                        "expected_response_time": detail.get("expected_response_time"),
                        "assertion": detail.get("assertion"),
                        "pre_request_script": detail.get("pre_request_script"),
                        "post_request_script": detail.get("post_request_script"),
                        "extract": detail.get("extract"),
                    }
                )

            cases_map.setdefault(relation.scenario_id, []).append(payload)

        return cases_map

    def _update_scenario_cases(self, scenario_id: int, cases: List[schemas.ScenarioCaseBind]) -> None:
        try:
            self.db.execute(
                Delete(ScenarioCase).where(ScenarioCase.scenario_id == scenario_id)
            )

            scenario = self.db.execute(
                Select(Scenario).where(Scenario.id == scenario_id)
            ).scalar_one()

            if cases:
                for case_bind in cases:
                    self.db.add(
                        ScenarioCase(
                            scenario_id=scenario_id,
                            case_id=case_bind.case_id,
                            order=case_bind.order,
                            weight=case_bind.weight,
                        )
                    )
                scenario.total_testcases = len(cases)
            else:
                scenario.total_testcases = 0
        except SQLAlchemyError as exc:
            self.logger.error(f"Update scenario cases failed: {exc}")
            raise ParamException("更新场景用例关联失败")

    def get(self, id: int) -> Dict[str, Any] | None:
        scenario = self._get_scenario_by_id(id)
        result = scenario.to_dict()
        result["cases"] = self._build_cases_map([id], include_details=True).get(id, [])
        return result

    def delete(self, id: int) -> Optional[bool]:
        scenario = self._get_scenario_by_id(id)
        self.access_control.ensure_project_manage_access(scenario.project_id)

        if getattr(scenario, "is_deleted", False):
            raise ParamException("场景已被删除")

        if not hasattr(scenario, "is_deleted"):
            raise ParamException(f"{self.model_class.__name__}不支持删除")

        scenario.soft_delete()

        try:
            self.db.execute(
                Delete(ScenarioCase).where(ScenarioCase.scenario_id == id)
            )
        except SQLAlchemyError as exc:
            self.logger.warning(f"Delete scenario cases failed: {exc}")

        self._commit(
            scenario,
            success_msg=f"Scenario deleted: {id}, {scenario.name}",
            fail_msg="删除场景失败",
            operation="scenario_delete",
        )
        return True

    def create(self, data: schemas.ScenarioCreate) -> Dict[str, Any] | None:
        create_data = data.model_dump()
        self.access_control.ensure_project_manage_access(create_data.get("project_id"))

        name = create_data.get("name")
        project_id = create_data.get("project_id")
        cases = data.cases
        create_data.pop("cases", None)

        self._validate_scenario_name_unique(name=name, project_id=project_id)

        new_scenario = Scenario(**create_data)
        new_scenario.total_testcases = len(cases)
        self.db.add(new_scenario)
        self.db.flush()

        try:
            for case_bind in cases:
                self.db.add(
                    ScenarioCase(
                        scenario_id=new_scenario.id,
                        case_id=case_bind.case_id,
                        order=case_bind.order,
                        weight=case_bind.weight,
                    )
                )

            self._commit(
                new_scenario,
                success_msg=f"Scenario created: {name}",
                fail_msg=f"创建场景{name}失败",
                operation="scenario_create",
            )

            result = new_scenario.to_dict()
            result["cases"] = self._build_cases_map([new_scenario.id], include_details=True).get(new_scenario.id, [])
            return result
        except SQLAlchemyError as exc:
            self.db.rollback()
            self.logger.error(f"Create scenario failed: {exc}")
            raise ParamException("创建场景失败")

    def update(self, data: schemas.ScenarioUpdate) -> Dict[str, Any] | None:
        update_data = data.model_dump(exclude_unset=True)
        scenario_id = update_data.get("id")
        cases = data.cases if "cases" in update_data else None
        update_data.pop("cases", None)

        if not scenario_id:
            raise ParamException("场景ID不能为空")

        scenario = self._get_scenario_by_id(scenario_id)
        self.access_control.ensure_project_manage_access(scenario.project_id)
        if "project_id" in update_data and update_data["project_id"] != scenario.project_id:
            self.access_control.ensure_project_manage_access(update_data["project_id"])

        if "name" in update_data:
            self._validate_scenario_name_unique(
                update_data["name"],
                exclude_scenario_id=scenario_id,
                project_id=update_data.get("project_id", scenario.project_id),
            )

        for field, value in update_data.items():
            if field in {
                "id",
                "created_at",
                "updated_at",
                "created_by",
                "updated_by",
                "is_deleted",
                "created_by_name",
                "updated_by_name",
                "deleted_by_name",
            }:
                continue
            if hasattr(scenario, field) and getattr(scenario, field) != value:
                setattr(scenario, field, value)

        if cases is not None:
            self._update_scenario_cases(scenario_id, cases)

        self._commit(
            scenario,
            success_msg=f"Scenario updated: {scenario_id}, {scenario.name}",
            fail_msg="更新场景失败",
            operation="scenario_update",
            extra={"updated_fields": list(update_data.keys())},
        )

        result = scenario.to_dict()
        result["cases"] = self._build_cases_map([scenario_id], include_details=True).get(scenario_id, [])
        return result

    def list(self, page: int = 1, page_size: int = 10, **kwargs):
        accessible_project_ids = self.access_control.get_accessible_project_ids()
        if accessible_project_ids is not None:
            if not accessible_project_ids:
                return {
                    "results": [],
                    "total": 0,
                    "total_pages": 0,
                    "page": page,
                    "page_size": page_size,
                }

            project_id = kwargs.get("project_id")
            if project_id is not None and project_id not in accessible_project_ids:
                return {
                    "results": [],
                    "total": 0,
                    "total_pages": 0,
                    "page": page,
                    "page_size": page_size,
                }

            query = self.db.query(Scenario).filter(
                Scenario.is_deleted == false(),
                Scenario.project_id.in_(accessible_project_ids),
            )

            valid_query = {
                key: val
                for key, val in kwargs.items()
                if val is not None and not (isinstance(val, str) and not val.strip())
            }
            valid_query.pop("page", None)
            valid_query.pop("page_size", None)

            for field_name, value in valid_query.items():
                if not hasattr(Scenario, field_name):
                    continue

                field = getattr(Scenario, field_name)
                if isinstance(value, Enum):
                    enum_candidates = {
                        value.value,
                        value.name,
                        str(value.value).lower(),
                        str(value.name).lower(),
                        str(value.value).upper(),
                        str(value.name).upper(),
                    }
                    query = query.filter(
                        or_(*[
                            func.lower(cast(field, String)) == str(candidate).lower()
                            for candidate in enum_candidates
                        ])
                    )
                elif isinstance(field.type, (String, Text)):
                    query = query.filter(field.ilike(f"%{value}%"))
                else:
                    query = query.filter(field == value)

            total = query.count()
            total_pages = (total + page_size - 1) // page_size if total else 0
            offset_num = (page - 1) * page_size
            results = query.order_by(Scenario.created_at.desc()).offset(offset_num).limit(page_size).all()

            cases_map = self._build_cases_map([item.id for item in results], include_details=False)
            payload_results = []
            for item in results:
                scenario_payload = item.to_dict()
                scenario_payload["cases"] = cases_map.get(item.id, [])
                payload_results.append(scenario_payload)

            return {
                "results": payload_results,
                "total": total,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
            }

        result = super().list(page=page, page_size=page_size, **kwargs)
        scenario_items = result.get("results", [])
        cases_map = self._build_cases_map([item.id for item in scenario_items], include_details=False)
        result["results"] = [
            {
                **item.to_dict(),
                "cases": cases_map.get(item.id, []),
            }
            for item in scenario_items
        ]
        return result
