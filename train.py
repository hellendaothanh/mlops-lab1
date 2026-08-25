"""Huấn luyện mô hình Iris với MLflow Tracking + Model Registry + Quality Gate.

Luồng: train -> evaluate -> QUALITY GATE (chặn theo accuracy) ->
register model -> gán alias "champion" -> xuất artifact di động cho serving.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Đảm bảo in được tiếng Việt trên Windows console (cp1252)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.tracking import MlflowClient
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

# Tên cột chuẩn hóa (khớp với app.py và monitor_drift.py)
FEATURE_NAMES = [
    "sepal_length_cm",
    "sepal_width_cm",
    "petal_length_cm",
    "petal_width_cm",
]
TARGET_NAME = "species"

ARTIFACTS_DIR = "artifacts"


def parse_args():
    parser = argparse.ArgumentParser(description="Train + Register Iris model")
    parser.add_argument(
        "--accuracy-threshold",
        type=float,
        default=0.90,
        help="Ngưỡng chất lượng tối thiểu để được đăng ký (quality gate)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="mlops_lab1_iris_classifier",
        help="Tên model trong MLflow Model Registry",
    )
    parser.add_argument(
        "--champion-alias",
        type=str,
        default="champion",
        help="Alias đánh dấu phiên bản đang phục vụ production",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Thiết lập Tracking Server (env MLFLOW_TRACKING_URI nếu có, mặc định SQLite cục bộ)
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("mlops_lab1_iris_classification")

    with mlflow.start_run() as run:
        print(f"--- MLflow Run ID: {run.info.run_id} ---")

        # 2. Chuẩn bị dữ liệu
        iris = load_iris()
        X = pd.DataFrame(iris.data, columns=FEATURE_NAMES)
        y = iris.target

        n_estimators = 50
        max_depth = 5
        random_state = 42

        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("random_state", random_state)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state, stratify=y
        )

        # 3. Huấn luyện
        print("Đang huấn luyện mô hình Random Forest...")
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
        )
        model.fit(X_train, y_train)

        # 4. Đánh giá
        predictions = model.predict(X_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions, average="weighted")),
            "recall": float(recall_score(y_test, predictions, average="weighted")),
        }
        for name, value in metrics.items():
            mlflow.log_metric(name, value)
            print(f" - {name:<10}: {value:.4f}")

        mlflow.log_metric("accuracy_threshold", args.accuracy_threshold)

        # Tag nguồn gốc (provenance) — phục vụ truy vết trong CI/CD
        mlflow.set_tag("git_sha", os.environ.get("GITHUB_SHA", "local"))
        mlflow.set_tag("trained_at", datetime.now(timezone.utc).isoformat())
        mlflow.set_tag("accuracy_threshold", str(args.accuracy_threshold))

        # Log source code + dataset làm bằng chứng tái lập (reproducibility)
        mlflow.log_artifact(__file__, artifact_path="source")
        X_train.assign(**{TARGET_NAME: y_train}).to_csv("train_data_tmp.csv", index=False)
        mlflow.log_artifact("train_data_tmp.csv", artifact_path="data")
        os.remove("train_data_tmp.csv")

        # Log model vào run hiện tại
        mlflow.sklearn.log_model(model, name="model")

        # 5. QUALITY GATE — chặn trước khi đăng ký, không model kém chất lượng lọt qua
        if metrics["accuracy"] < args.accuracy_threshold:
            print(
                f"\n❌ QUALITY GATE THẤT BẠI: accuracy={metrics['accuracy']:.4f} "
                f"< ngưỡng={args.accuracy_threshold}. Model KHÔNG được đăng ký."
            )
            sys.exit(1)

        # 6. Đăng ký vào Model Registry + gán alias champion
        model_uri = f"runs:/{run.info.run_id}/model"
        registered = mlflow.register_model(model_uri, args.model_name)
        client = MlflowClient()
        client.set_registered_model_alias(
            args.model_name, args.champion_alias, registered.version
        )
        print(
            f"✅ Đã đăng ký {args.model_name} version={registered.version} "
            f"với alias '{args.champion_alias}'"
        )

        # 7. Xuất artifact di động cho serving (container không cần truy cập Registry)
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        model_path = os.path.join(ARTIFACTS_DIR, "iris_model")
        mlflow.sklearn.save_model(model, path=model_path)

        X_train.to_csv(os.path.join(ARTIFACTS_DIR, "reference_data.csv"), index=False)

        meta = {
            "model_name": args.model_name,
            "model_version": registered.version,
            "alias": args.champion_alias,
            "run_id": run.info.run_id,
            "tracking_uri": tracking_uri,
            "metrics": metrics,
            "accuracy_threshold": args.accuracy_threshold,
            "feature_names": FEATURE_NAMES,
            "classes": iris.target_names.tolist(),
            "git_sha": os.environ.get("GITHUB_SHA", "local"),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(os.path.join(ARTIFACTS_DIR, "model_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        print(f"✅ Đã xuất artifact serving tại '{model_path}/' + model_meta.json")


if __name__ == "__main__":
    main()
