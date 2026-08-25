# 🚀 Dự Án MLOps Thực Chiến: Từ Mã Nguồn Đến Production & CI/CD Pipeline

Tài liệu này ghi lại toàn bộ quy trình thiết kế, xây dựng và tự động hóa một hệ thống **Machine Learning Operations (MLOps)** chuẩn hóa, được thiết kế từ góc nhìn của một kỹ sư **DevSecOps**.

> ⚡ **Lab 2 đã nâng cấp project thành pipeline end-to-end.** Kiến trúc mới: train → quality gate → Model Registry (alias `champion`) → serving từ artifact đã kiểm định → giám sát drift. Chi tiết lộ trình xem `../../ROADMAP.md`.

---

## 📂 Cấu trúc Thư mục Dự án

```text
mlops-lab1/
├── .github/
│   └── workflows/
│       └── mlops-ci.yml      # CI/CD 3 job: code-quality -> train-and-register -> build-scan-smoke
├── app.py                    # FastAPI serving: load model từ Registry/artifact, /health, /predict
├── train.py                  # Train + QUALITY GATE + register alias champion + xuất artifacts/
├── monitor_drift.py          # Drift monitoring: Evidently (fallback KS-test) + alert webhook
├── tests/
│   └── test_app.py           # 7 unit test API chạy với model thật
├── artifacts/                # Output của train.py: model serving + reference_data.csv + model_meta.json
├── reports/                  # Báo cáo drift (HTML/JSON) từ monitor_drift.py
├── Dockerfile                # Image slim, non-root, HEALTHCHECK
├── .dockerignore             # Loại trừ tracking store/secrets khỏi image
├── .flake8                   # Cấu hình lint (max-line-length=127)
├── requirements.txt          # Runtime: fastapi, uvicorn, sklearn, mlflow...
└── requirements-dev.txt      # Dev/CI: pytest, bandit, pip-audit, evidently...
```

---

## 🛠️ Bước 1: Huấn luyện Mô hình & Tracking (MLflow)

1. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements-dev.txt
   ```
2. **Chạy kịch bản huấn luyện (kèm quality gate):**
   ```bash
   python train.py --accuracy-threshold 0.90
   ```
   * Accuracy < ngưỡng → exit code 1, model KHÔNG được đăng ký.
   * Accuracy đạt → model đăng ký vào Registry với alias `champion` và xuất `artifacts/`.
3. **Kiểm thử API với model thật:**
   ```bash
   pytest tests -v
   ```

Xem lịch sử thí nghiệm bằng MLflow UI: `mlflow ui` → `http://127.0.0.1:5000`, hoặc xem model registry qua `mlflow models` / giao diện UI.

---

## 🐳 Bước 2: Model Serving & Container hóa (Docker)

Container load model từ `MLFLOW_LOCAL_MODEL_PATH=/app/artifacts/iris_model` (artifact đã qua kiểm định), không tự train lại.

```bash
docker build -t mlops-iris-api:v2 .
docker run -d -p 8000:8000 mlops-iris-api:v2
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"sepal_length_cm":5.1,"sepal_width_cm":3.5,"petal_length_cm":1.4,"petal_width_cm":0.2}'
```

Chạy local không cần Docker:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

## 📉 Bước 3: Giám sát Data Drift

```bash
python monitor_drift.py --shift-strength 0.8   # mô phỏng drift -> exit code 1
python monitor_drift.py --shift-strength 0     # dữ liệu ổn định -> exit code 0
```

* Engine chính: **Evidently** (báo cáo HTML trong `reports/`); fallback tự động sang **KS-test** nếu môi trường không tương thích.
* Có dữ liệu production thật: `python monitor_drift.py --current path/to/current.csv`
* Cấu hình `ALERT_WEBHOOK_URL` để đẩy cảnh báo lên Slack/Teams.
* Exit code 1 cho phép cron/Airflow tự trigger retrain.

---

## 🔄 Bước 4: Tự động hóa CI/CD & Bảo mật (GitHub Actions)

Pipeline `.github/workflows/mlops-ci.yml` gồm 3 job tuần tự:

| Job | Nội dung | Điều kiện đi tiếp |
|---|---|---|
| `code-quality` | flake8 + Bandit (SAST) + pip-audit (CVE dependencies) | Không lỗi lint/SAST/CVE |
| `train-and-register` | Train → quality gate → register → pytest → upload artifacts | Accuracy ≥ ngưỡng |
| `build-scan-smoke` | Build image → Trivy (CVE Critical/High + secret) → smoke test API | Image sạch + API đúng |

---

## 🏁 Tổng kết Giá trị MLOps & DevSecOps
* **Reproducibility**: mọi thí nghiệm, model version, dataset tham chiếu đều được quản lý qua MLflow Registry + artifacts.
* **Quality Gate**: model kém chất lượng bị chặn ngay ở CI, không bao giờ tới production.
* **Security-First**: SAST, dependency audit, container scanning, secret scanning, non-root container.
* **Monitoring**: phát hiện data drift và cảnh báo trước khi chất lượng dự đoán suy giảm.
