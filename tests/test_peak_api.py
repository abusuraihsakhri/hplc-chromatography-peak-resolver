"""API contract checks for the HPLC endpoint and restricted audit logs."""
import math

from fastapi.testclient import TestClient
from agents.api import app
from hplc_resolver.server import create_app


def example_samples():
    return [
        [i * 0.1, 2 + 15 * math.exp(-0.5 * ((i * 0.1 - 5) / 0.6) ** 2)
         + 12 * math.exp(-0.5 * ((i * 0.1 - 12) / 0.7) ** 2)]
        for i in range(171)
    ]


def test_primary_peak_endpoint():
    client = TestClient(app)
    response = client.post("/api/peaks", json={"samples": example_samples(), "min_prominence": 0.05})
    assert response.status_code == 200
    payload = response.json()
    assert payload["points"] == 171
    assert len(payload["peaks"]) == 2
    assert payload["peaks"][1]["resolutionFromPrevious"] > 1
    assert client.post("/api/peaks", json={"samples": [[0, 1], [1, 2]]}).status_code == 422


def test_alternative_server_peak_endpoint():
    alternative = create_app()
    assert alternative is not None
    result = TestClient(alternative).post("/api/peaks", json={"samples": example_samples()})
    assert result.status_code == 200
    assert len(result.json()["peaks"]) == 2


def test_audit_logs_require_admin_token(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("API_ADMIN_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 503
    secret = "test-admin-token-" + "a" * 40
    monkeypatch.setenv("API_ADMIN_TOKEN", secret)
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"X-Admin-Token": "wrong"}).status_code == 403
    allowed = client.get("/api/audit/logs", headers={"X-Admin-Token": secret})
    assert allowed.status_code == 200
    assert allowed.json()["verified"] is True
