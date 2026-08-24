# 📘 CẨM NANG MLOPS THỰC CHIẾN: TỪ MÃ NGUỒN ĐẾN VẬN HÀNH & BẢO MẬT
**Tác giả:** Kỹ sư MLOps & DevSecOps  
**Mục tiêu:** Xây dựng, đóng gói, tự động hóa và giám sát một hệ thống Machine Learning theo tiêu chuẩn kỹ nghệ phần mềm hiện đại.

---

## 📂 MỤC LỤC
1. [Tổng quan về MLOps qua lăng kính DevSecOps](#1-tổng-quan-về-mlops-qua-lăng-kính-devsecops)
2. [Bài Lab 1: Quản lý Thí nghiệm & Tracking Mô hình với MLflow](#2-bài-lab-1-quản-lý-thí-nghiệm--tracking-mô-hình-với-mlflow)
3. [Bài Lab 2: Đóng gói Ứng dụng & Container hóa với Docker](#3-bài-lab-2-đóng-gói-ứng-dụng--container-hóa-với-docker)
4. [Bài Lab 3: Tự động hóa CI/CD & Bảo mật với GitHub Actions](#4-bài-lab-3-tự-động-hóa-cicd--bảo-mật-với-github-actions)
5. [Bài Lab 4: Giám sát Data Drift & Vận hành Model Monitoring](#5-bài-lab-4-giám-sát-data-drift--vận-hành-model-monitoring)

---

## 1. Tổng quan về MLOps qua lăng kính DevSecOps
Trong phát triển phần mềm truyền thống, DevOps giúp tự động hóa chu trình phát triển (CI/CD). Trong lĩnh vực Trí tuệ Nhân tạo, **MLOps** giải quyết bài toán phức tạp hơn khi hệ thống phụ thuộc vào cả **Mã nguồn (Code)** lẫn **Dữ liệu (Data)**.
* **Đặc thù:** Mô hình AI không cố định theo thời gian; dữ liệu thay đổi gây ra hiện tượng *Data Drift*, làm giảm độ chính xác của mô hình dù code không thay đổi.
* **Triết lý:** Tự động hóa, tính tái lập (Reproducibility), tính minh bạch (Traceability) và bảo mật từ gốc (Security-by-Design).

---

## 2. Bài Lab 1: Quản lý Thí nghiệm & Tracking Mô hình với MLflow
Mục tiêu bài lab này là loại bỏ hoàn toàn cách lưu trữ mô hình thủ công (như đặt tên file `model_v1_final.pkl`), thay vào đó sử dụng công cụ tracking chuyên nghiệp.

* **Công cụ:** `MLflow`, `Scikit-Learn`, `Python`.
* **Kịch bản huấn luyện (`train.py`):**
```python
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

with mlflow.start_run() as run:
    # 1. Load dữ liệu & chia tập train/test
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)

    # 2. Định nghĩa tham số & Log lên MLflow
    n_estimators = 50
    mlflow.log_param("n_estimators", n_estimators)

    # 3. Huấn luyện mô hình
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)

    # 4. Đánh giá & Log metrics
    acc = accuracy_score(y_test, model.predict(X_test))
    mlflow.log_metric("accuracy", acc)

    # 5. Lưu model artifact
    mlflow.sklearn.log_model(model, "random_forest_model")
    print(f"Huấn luyện thành công! Run ID: {run.info.run_id}")
```
* **Cách xem kết quả:** Chạy lệnh `mlflow ui` và truy cập `http://127.0.0.1:5000`.

---

## 3. Bài Lab 2: Đóng gói Ứng dụng & Container hóa với Docker
Đảm bảo mô hình và mã nguồn dịch vụ hoạt động nhất quán trên mọi môi trường thông qua Container.

* **API Serving (`app.py` sử dụng FastAPI):**
```python
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression
import numpy as np

# Huấn luyện mô hình cơ bản khi khởi động
X = np.array([[50], [60], [80], [100], [120]])
y = np.array([[1.5], [1.8], [2.4], [3.0], [3.6]])
model = LinearRegression().fit(X, y)

app = FastAPI(title="MLOps Demo API", version="1.0.0")

class HouseInput(BaseModel):
    area: float

@app.post("/predict")
def predict(data: HouseInput):
    prediction = model.predict(np.array([[data.area]]))
    return {"input_area": data.area, "predicted_price_billion": round(float(prediction[0][0]), 2)}
```

* **Dockerfile chuẩn bảo mật & tối ưu:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. Bài Lab 3: Tự động hóa CI/CD & Bảo mật với GitHub Actions
Tự động hóa toàn bộ quy trình kiểm tra mã nguồn, quét lỗ hổng bảo mật container và đóng gói ứng dụng.

* **Cấu hình Pipeline (`.github/workflows/mlops-ci.yml`):**
```yaml
name: MLOps CI/CD Pipeline

on:
  push:
    branches: [ "main", "master" ]

jobs:
  mlops-pipeline:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python 3.10
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

    - name: Build Docker image
      run: |
        docker build -t mlops-house-api:${{ github.sha }} .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'mlops-house-api:${{ github.sha }}'
        format: 'table'
        exit-code: '0'
        severity: 'CRITICAL,HIGH'
```

---

## 5. Bài Lab 4: Giám sát Data Drift & Vận hành Model Monitoring
Phát hiện sớm sự thay đổi của dữ liệu đầu vào trên môi trường Production để ngăn chặn tình trạng suy giảm chất lượng mô hình.

* **Kịch bản giám sát tùy chỉnh (`monitor_drift.py`):**
```python
import pandas as pd
import numpy as np

# Dữ liệu huấn luyện gốc (Reference) & Dữ liệu thực tế (Current)
reference_data = pd.DataFrame({'area': np.random.normal(80, 10, 1000)})
current_data = pd.DataFrame({'area': np.random.normal(140, 15, 1000)})

# Kiểm tra độ lệch trung bình (Mean Shift)
ref_mean = reference_data['area'].mean()
cur_mean = current_data['area'].mean()
diff_percent = abs(cur_mean - ref_mean) / ref_mean * 100

print(f"Tỷ lệ lệch dữ liệu: {diff_percent:.2f}%")
if diff_percent > 15:
    print("⚠️ CẢNH BÁO: Phát hiện Data Drift đáng kể! Cần kích hoạt quy trình huấn luyện lại mô hình (Retraining).")
```