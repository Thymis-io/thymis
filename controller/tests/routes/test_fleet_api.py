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


def test_fleet_metrics_accepts_90_day_range(test_client):
    resp = test_client.get("/api/fleet/metrics?hours=2160&granularity=1d")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_fleet_availability_endpoint_returns_object(test_client):
    resp = test_client.get("/api/fleet/availability?hours=24&buckets=12")
    assert resp.status_code == 200
    body = resp.json()
    assert "timestamps" in body and "devices" in body
    assert len(body["timestamps"]) == 13


def test_fleet_alerts_endpoint_returns_list(test_client):
    resp = test_client.get("/api/fleet/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
