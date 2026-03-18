from app.engine_v2.metrics.local_aggregator import LocalMetricsAggregator


def test_local_metrics_aggregator_collects_error_metadata():
    aggregator = LocalMetricsAggregator()

    aggregator.record(
        method="GET",
        name="Scenario / Case",
        response_time_ms=120,
        success=False,
        status_code=500,
        error_type="unexpected_status",
        error_message="HTTP 500",
        content_length=32,
    )

    snapshot = aggregator.build_snapshot(active_users=3, latest_error="HTTP 500")

    assert snapshot["total_requests"] == 1
    assert snapshot["fail_count"] == 1
    assert snapshot["status_code_counts"]["500"] == 1
    assert snapshot["error_type_counts"]["unexpected_status"] == 1
    assert snapshot["failure_samples"][0]["message"] == "HTTP 500"
    assert snapshot["stats"][0]["latest_error"] == "HTTP 500"
