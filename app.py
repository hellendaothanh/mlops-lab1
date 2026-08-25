"""Model Serving API (FastAPI).

Nguồn model theo thứ tự ưu tiên:
  1. MLFLOW_LOCAL_MODEL_PATH (đặt trong Docker image)
  2. artifacts/iris_model (xuất bởi train.py khi chạy local)
  3. Model Registry qua URI "models:/<name>@<alias>" (cần MLflow server)

Nếu không tải được model, API vẫn khởi động ở trạng thái "degraded"
(/predict trả 503) thay vì sập — giúp health check và rollback hoạt động đúng.
"""
import json
import os
import sys
import time
from contextlib import asynccontextmanager

# Đảm bảo in được tiếng Việt trên Windows console (cp1252)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL_NAME = os.environ.get("MLFLOW_MODEL_NAME", "mlops_lab1_iris_classifier")
ALIAS = os.environ.get("MLFLOW_MODEL_ALIAS", "champion")
REGISTRY_URI = f"models:/{MODEL_NAME}@{ALIAS}"
LOCAL_DEFAULT = os.path.join("artifacts", "iris_model")
META_PATH = os.environ.get(
    "MLFLOW_META_PATH", os.path.join("artifacts", "model_meta.json")
)

# Trạng thái dùng chung của tiến trình
state = {"model": None, "meta": {}, "source": None}


def _load_meta():
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def _load_model():
    """Tải model từ nguồn khả dụng; trả về (model, nguồn)."""
    candidates = []

    env_path = os.environ.get("MLFLOW_LOCAL_MODEL_PATH")
    if env_path:
        candidates.append((env_path, f"local:{env_path}"))
    candidates.append((LOCAL_DEFAULT, f"local:{LOCAL_DEFAULT}"))
    candidates.append((REGISTRY_URI, f"registry:{REGISTRY_URI}"))

    for path, source in candidates:
        is_local = source.startswith("local:")
        if is_local and not os.path.exists(path):
            continue
        try:
            if not is_local:
                mlflow.set_tracking_uri(
                    os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
                )
            model = mlflow.sklearn.load_model(path)
            print(f"[model] Loaded from {source}")
            return model, source
        except Exception as exc:  # noqa: BLE001 - thử nguồn kế tiếp
            print(f"[model] Không tải được từ {source}: {exc}")
    return None, None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    state["meta"] = _load_meta()
    state["model"], state["source"] = _load_model()
    yield
    state["model"] = None


app = FastAPI(
    title="MLOps Iris Classifier API",
    description="Serving mô hình phân loại Iris theo chuẩn MLOps + MLSecOps",
    version="2.0.0",
    lifespan=lifespan,
)


class IrisInput(BaseModel):
    """Đầu vào gồm 4 đặc trưng hoa iris — validate chặt để chặn input độc hại."""

    sepal_length_cm: float = Field(..., ge=0, le=15, description="Dài đài hoa (cm)")
    sepal_width_cm: float = Field(..., ge=0, le=10, description="Rộng đài hoa (cm)")
    petal_length_cm: float = Field(..., ge=0, le=15, description="Dài cánh hoa (cm)")
    petal_width_cm: float = Field(..., ge=0, le=10, description="Rộng cánh hoa (cm)")


def _to_dataframe(item: IrisInput) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump()])


@app.get("/")
def home():
    return {
        "service": "MLOps Iris Classifier API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    loaded = state["model"] is not None
    meta = state["meta"]
    return {
        "status": "healthy" if loaded else "degraded",
        "model_loaded": loaded,
        "detail": {
            "source": state["source"],
            "model_name": meta.get("model_name"),
            "model_version": meta.get("model_version"),
            "alias": meta.get("alias"),
            "accuracy": meta.get("metrics", {}).get("accuracy"),
            "trained_at": meta.get("trained_at"),
            "git_sha": meta.get("git_sha"),
        },
    }


@app.post("/predict")
def predict(data: IrisInput):
    if state["model"] is None:
        raise HTTPException(status_code=503, detail="Model chưa sẵn sàng (degraded mode)")

    start = time.perf_counter()
    features_df = _to_dataframe(data)
    prediction = state["model"].predict(features_df)[0]
    probabilities = state["model"].predict_proba(features_df)[0]
    latency_ms = round((time.perf_counter() - start) * 1000, 3)

    classes = state["meta"].get("classes") or ["setosa", "versicolor", "virginica"]
    return {
        "prediction": int(prediction),
        "predicted_class": str(classes[int(prediction)]),
        "probabilities": {
            str(name): round(float(p), 4) for name, p in zip(classes, np.asarray(probabilities))
        },
        "latency_ms": latency_ms,
        "model_version": state["meta"].get("model_version"),
        "git_sha": state["meta"].get("git_sha"),
    }
