# 🚀 Dự Án MLOps Thực Chiến: Từ Mã Nguồn Đến Production & CI/CD Pipeline

Tài liệu này ghi lại toàn bộ quy trình thiết kế, xây dựng và tự động hóa một hệ thống **Machine Learning Operations (MLOps)** chuẩn hóa, được thiết kế từ góc nhìn của một kỹ sư **DevSecOps**.

---

## 📂 Cấu trúc Thư mục Dự án

```text
mlops-lab1/
├── .github/
│   └── workflows/
│       └── mlops-ci.yml      # GitHub Actions CI/CD Pipeline & Security Scanning
├── app.py                    # Ứng dụng FastAPI phục vụ Model Serving
├── Dockerfile                # Cấu hình đóng gói Container an toàn và tối ưu
├── requirements.txt          # Danh sách thư viện Python phụ thuộc
├── train.py                  # Kịch bản huấn luyện mô hình kết hợp MLflow Tracking
└── README.md                 # Tài liệu hướng dẫn dự án (Docs)
```

---

## 🛠️ Bước 1: Huấn luyện Mô hình & Tracking (MLflow)

Mục tiêu của bước này là tách biệt rõ ràng code huấn luyện và dữ liệu, đồng thời ghi nhận lại toàn bộ thông số thí nghiệm (Experiment Tracking) thay vì lưu trữ thủ công.

1. **Cài đặt thư viện:**
   ```bash
   pip install mlflow scikit-learn pandas numpy fastapi uvicorn
   ```
2. **Chạy kịch bản huấn luyện:**
   ```bash
   python train.py
   ```
   * *Kết quả:* Mô hình được huấn luyện, các chỉ số (`Accuracy`, `Precision`, `Recall`) được ghi nhận và artifact được lưu trữ an toàn.
3. **Xem giao diện quản lý thí nghiệm (MLflow UI):**
   ```bash
   mlflow ui
   ```
   * Truy cập trình duyệt tại: `http://127.0.0.1:5000`

---

## 🐳 Bước 2: Model Serving & Container hóa (Docker)

Đóng gói mô hình và API vào bên trong một Container bất biến (Immutable Artifact) để đảm bảo tính nhất quán giữa môi trường Local và Production.

1. **API Serving (`app.py`):** Sử dụng `FastAPI` để tạo endpoint `/predict` nhận dữ liệu đầu vào và trả về kết quả dự đoán từ mô hình.
2. **Chạy thử API Local:**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   * Truy cập tài liệu API tương tác tại: `http://127.0.0.1:8000/docs`
3. **Build Docker Image:**
   ```bash
   docker build -t mlops-house-api:v1 .
   ```
4. **Chạy Docker Container:**
   ```bash
   docker run -d -p 8000:8000 --name house-api-container mlops-house-api:v1
   ```

---

## 🔄 Bước 3: Tự động hóa CI/CD & Bảo mật (GitHub Actions & Trivy)

Tích hợp tư duy **DevSecOps** vào chuỗi cung ứng phần mềm AI (ML Supply Chain) thông qua GitHub Actions.

### Nội dung cấu hình Pipeline (`.github/workflows/mlops-ci.yml`):
* **Linting (Flake8):** Kiểm tra lỗi cú pháp và chuẩn định dạng code Python.
* **SAST (Bandit):** Quét các lỗ hổng bảo mật tiềm ẩn trong mã nguồn.
* **Container Build Test:** Tự động build Docker image theo từng commit SHA để đảm bảo tính truy xuất nguồn gốc (Traceability).
* **Vulnerability Scanning (Trivy):** Quét các lỗ hổng (CVEs) trong các thư viện hệ thống và package Python bên trong Docker Image.

---

## 🏁 Tổng kết Giá trị MLOps & DevSecOps
* **Reproducibility (Tính tái lập):** Mọi thí nghiệm và mô hình đều được quản lý phiên bản rõ ràng qua MLflow.
* **Security-First (Bảo mật hàng đầu):** Phát hiện sớm lỗi code và lỗ hổng container ngay từ giai đoạn CI trước khi đưa lên Production.
* **Automation (Tự động hóa):** Rút ngắn thời gian từ lúc viết code đến lúc sẵn sàng deploy xuống chỉ bằng một câu lệnh `git push`.