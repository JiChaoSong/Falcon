from app.engine_v2.runtime.response_utils import apply_extractions, evaluate_assertion


def test_apply_extractions_uses_dot_path():
    body = '{"data":{"token":"abc123","user":{"id":42}}}'

    extracted = apply_extractions(body, {
        "token": "$.data.token",
        "user_id": "data.user.id",
    })

    assert extracted == {
        "token": "abc123",
        "user_id": 42,
    }


def test_evaluate_assertion_supports_contains_and_json():
    ok, error = evaluate_assertion("contains:success", '{"message":"success"}')
    assert ok is True
    assert error is None

    ok, error = evaluate_assertion("json:$.code=200", '{"code":200}')
    assert ok is True
    assert error is None

    ok, error = evaluate_assertion("json:$.code=201", '{"code":200}')
    assert ok is False
    assert "expected $.code=201" in error
