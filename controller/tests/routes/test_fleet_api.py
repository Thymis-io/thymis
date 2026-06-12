def test_fleet_metrics_endpoint_returns_list(test_client):
    resp = test_client.get("/api/fleet/metrics?hours=24&granularity=1h")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_fleet_connectivity_endpoint_returns_list(test_client):
    resp = test_client.get("/api/fleet/connectivity?hours=24&buckets=24")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 25  # buckets + 1 sample points


def test_fleet_latest_endpoint_returns_list(test_client):
    resp = test_client.get("/api/fleet/device_metrics_latest")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
