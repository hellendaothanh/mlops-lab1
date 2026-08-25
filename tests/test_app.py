"""Kiểm thử API serving bằng dữ liệu thật từ artifacts (chạy sau khi train)."""
import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="module")
def client():
    # TestClient chạy lifespan -> model được tải trước các test
    with TestClient(app) as c:
        yield c


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "MLOps Iris Classifier API"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("healthy", "degraded")
    assert "model_loaded" in body


def test_health_has_model_loaded(client):
    """Model phải tồn tại sau bước train trong pipeline."""
    body = client.get("/health").json()
    assert body["model_loaded"] is True, "Model chưa được tải - hãy chạy train.py trước"
    assert body["status"] == "healthy"


def test_predict_valid_sample(client):
    payload = {
        "sepal_length_cm": 5.1,
        "sepal_width_cm": 3.5,
        "petal_length_cm": 1.4,
        "petal_width_cm": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["prediction"], int)
    assert body["predicted_class"] in ("setosa", "versicolor", "virginica")
    assert 0.0 <= sum(body["probabilities"].values()) <= 1.001
    assert "latency_ms" in body


def test_predict_rejects_out_of_range(client):
    payload = {
        "sepal_length_cm": 9999.0,
        "sepal_width_cm": 3.5,
        "petal_length_cm": 1.4,
        "petal_width_cm": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_rejects_missing_field(client):
    payload = {"sepal_length_cm": 5.1}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_setosa_expected(client):
    """Mẫu setosa điển hình phải được dự đoán đúng."""
    payload = {
        "sepal_length_cm": 5.0,
        "sepal_width_cm": 3.3,
        "petal_length_cm": 1.4,
        "petal_width_cm": 0.2,
    }
    assert client.post("/predict", json=payload).json()["predicted_class"] == "setosa"
