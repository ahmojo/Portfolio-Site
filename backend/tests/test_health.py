from fastapi.testclient import TestClient


def test_fastapi_health_smoke(monkeypatch, tmp_path):
    """Boot the real app with isolated runtime state and check its public probe."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PORTFOLIO_ENV", "development")

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/api/health")
        head_response = client.head("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "portfolio-api"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert head_response.status_code == 200
