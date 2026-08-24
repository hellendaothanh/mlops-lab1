import os
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

def main():
    # 1. Thiết lập MLflow Experiment
    # MLflow sẽ lưu trữ dữ liệu tracking vào thư mục cục bộ tên là "mlruns"
    mlflow.set_experiment("mlops_lab1_iris_classification")
    
    with mlflow.start_run() as run:
        print(f"--- Đang chạy MLflow Run ID: {run.info.run_id} ---")

        # 2. Chuẩn bị dữ liệu (Data Preparation)
        iris = load_iris()
        X, y = iris.data, iris.target

        # Định nghĩa các hyperparameter (những tham số cấu hình mô hình)
        n_estimators = 50
        max_depth = 5
        random_state = 42

        # Log parameters lên MLflow (giống như lưu cấu hình phiên bản)
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("random_state", random_state)

        # Chia tập train / test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=random_state
        )

        # 3. Huấn luyện mô hình (Model Training)
        print("Đang huấn luyện mô hình Random Forest...")
        model = RandomForestClassifier(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            random_state=random_state
        )
        model.fit(X_train, y_train)

        # 4. Đánh giá mô hình (Model Evaluation)
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions, average='weighted')
        recall = recall_score(y_test, predictions, average='weighted')

        print(f"Kết quả đánh giá:")
        print(f" - Accuracy : {accuracy:.4f}")
        print(f" - Precision: {precision:.4f}")
        print(f" - Recall   : {recall:.4f}")

        # Log các chỉ số (metrics) lên MLflow
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)

        # 5. Lưu trữ mô hình (Artifact Logging)
        # MLflow sẽ đóng gói mô hình và lưu vào thư mục mlruns/
        mlflow.sklearn.log_model(model, "random_forest_model")
        print("Huấn luyện hoàn tất và đã lưu model artifact vào MLflow!")

if __name__ == "__main__":
    main()