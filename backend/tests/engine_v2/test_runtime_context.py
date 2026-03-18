from app.engine_v2.runtime.context import RuntimeContext


def test_runtime_context_renders_nested_values():
    context = RuntimeContext(
        task_id=1,
        task_run_id=2,
        host="http://localhost",
        task_variables={"token": "abc"},
        scenario_variables={"user_id": 42},
    )

    rendered = context.render_value(
        {
            "Authorization": "Bearer {{token}}",
            "payload": {
                "user": "{{user_id}}",
                "tags": ["{{token}}", "raw"],
            },
        }
    )

    assert rendered == {
        "Authorization": "Bearer abc",
        "payload": {
            "user": "42",
            "tags": ["abc", "raw"],
        },
    }
