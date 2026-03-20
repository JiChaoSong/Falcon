import json
from typing import Any


def parse_json_body(body: str | None) -> Any | None:
    if not body:
        return None
    try:
        return json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return None


def extract_path(data: Any, path: str) -> Any:
    normalized_path = (path or "").strip()
    if not normalized_path:
        raise ValueError("提取路径不能为空")

    if normalized_path.startswith("$."):
        normalized_path = normalized_path[2:]
    elif normalized_path == "$":
        return data

    current = data
    for part in normalized_path.split("."):
        part = part.strip()
        if not part:
            continue

        if isinstance(current, dict):
            if part not in current:
                raise KeyError(part)
            current = current[part]
            continue

        if isinstance(current, list):
            index = int(part)
            current = current[index]
            continue

        raise KeyError(part)

    return current


def apply_extractions(body: str | None, extract_rules: dict[str, str] | None) -> dict[str, Any]:
    if not extract_rules:
        return {}

    json_body = parse_json_body(body)
    if json_body is None:
        raise ValueError("响应不是合法 JSON，无法执行提取")

    extracted: dict[str, Any] = {}
    for variable_name, path in extract_rules.items():
        extracted[variable_name] = extract_path(json_body, str(path))
    return extracted


def evaluate_assertion(assertion: str | None, body: str | None) -> tuple[bool, str | None]:
    if not assertion:
        return True, None

    text_body = body or ""
    rule = assertion.strip()
    if not rule:
        return True, None

    if rule.startswith("contains:"):
        expected = rule.split(":", 1)[1]
        if expected in text_body:
            return True, None
        return False, f"Assertion failed: response does not contain '{expected}'"

    if rule.startswith("not_contains:"):
        expected = rule.split(":", 1)[1]
        if expected not in text_body:
            return True, None
        return False, f"Assertion failed: response should not contain '{expected}'"

    if rule.startswith("json:"):
        payload = parse_json_body(text_body)
        if payload is None:
            return False, "Assertion failed: response is not valid JSON"

        expression = rule.split(":", 1)[1]
        if "=" not in expression:
            return False, "Assertion failed: json assertion must use path=value"

        path, expected = expression.split("=", 1)
        try:
            actual = extract_path(payload, path.strip())
        except (KeyError, IndexError, ValueError) as exc:
            return False, f"Assertion failed: {exc}"

        if str(actual) == expected.strip():
            return True, None
        return False, f"Assertion failed: expected {path.strip()}={expected.strip()}, got {actual}"

    if rule.startswith("equals:"):
        expected = rule.split(":", 1)[1]
        if text_body == expected:
            return True, None
        return False, "Assertion failed: response body does not exactly match expected text"

    if rule in text_body:
        return True, None

    return False, f"Assertion failed: response does not contain '{rule}'"
