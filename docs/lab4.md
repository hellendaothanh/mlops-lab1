**Data Drift (Sự trôi dạt dữ liệu)** là vấn đề đau đầu nhất của các hệ thống AI trên Production. Việc bạn kiểm soát được "khi nào mô hình bị ngu đi do dữ liệu thay đổi" là kỹ năng cực kỳ giá trị của một MLOps/DevSecOps Engineer mà **không cần đến Cloud phức tạp**.

Chúng ta sẽ bước vào **Bài Lab 4: Giám sát Data Drift và Sức khỏe Mô hình bằng Evidently AI (Chạy hoàn toàn trên máy local)**.

---

# 📚 TÀI LIỆU HƯỚNG DẪN BÀI LAB 4: GIÁM SÁT DATA DRIFT & MODEL MONITORING

## Mục tiêu bài Lab:
* Hiểu hiện tượng **Data Drift** (Khi dữ liệu đưa vào dự đoán ở production khác biệt so với dữ liệu dùng để train ban đầu).
* Sử dụng thư viện **Evidently AI** để tự động sinh ra một báo cáo HTML kiểm tra độ lệch dữ liệu.
* Tích hợp kiểm tra Drift vào quy trình vận hành.

---

### BƯỚC 1: Cài đặt thư viện Evidently AI
Evidently AI là công cụ mã nguồn mở hàng đầu giúp đánh giá, kiểm tra và giám sát dữ liệu và mô hình ML.

Mở terminal và cài đặt:
```bash
pip install evidently pandas scikit-learn
```

---

### BƯỚC 2: Viết kịch bản mô phỏng Data Drift (`monitor_drift.py`)

Hãy tưởng tượng: 
* **Tập dữ liệu gốc (Reference Data):** Dữ liệu nhà cửa lúc bạn huấn luyện mô hình (Diện tích trung bình từ 50m² đến 120m²).
* **Tập dữ liệu mới trên Production (Current Data):** Sau vài tháng, khách hàng toàn tìm mua nhà siêu lớn hoặc siêu nhỏ (Diện tích thay đổi từ 150m² đến 300m²). Mô hình lúc này sẽ bắt đầu dự đoán sai lệch.

Tạo file `monitor_drift.py` tại thư mục dự án:

```python
import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

# 1. Tạo tập dữ liệu Gốc (Reference Data - lúc train mô hình)
np.random.seed(42)
reference_data = pd.DataFrame({
    'area': np.random.normal(80, 10, 1000),      # Diện tích trung bình quanh 80m2
    'rooms': np.random.randint(2, 5, 1000)       # Số phòng từ 2-4
})

# 2. Tạo tập dữ liệu Mới trên Production (Current Data - sau khi deploy)
# Giả sử hành vi người dùng thay đổi: Nhà to hơn hẳn (Data Drift xảy ra!)
current_data = pd.DataFrame({
    'area': np.random.normal(140, 15, 1000),     # Diện tích dịch chuyển lên quanh 140m2
    'rooms': np.random.randint(3, 7, 1000)       # Số phòng từ 3-6
})

print("Đang khởi tạo báo cáo Data Drift...")

# 3. Sử dụng Evidently AI để sinh báo cáo kiểm tra độ trôi dạt dữ liệu
drift_report = Report(metrics=[
    DataDriftPreset(),
])

drift_report.run(reference_data=reference_data, current_data=current_data)

# 4. Lưu kết quả ra file HTML trực quan
report_path = "data_drift_report.html"
drift_report.save_html(report_path)

print(f"Báo cáo giám sát Data Drift đã được lưu thành công tại: {report_path}")
print("Bạn hãy mở file HTML này trên trình duyệt để xem biểu đồ phân tích chi tiết độ lệch dữ liệu!")
```

---

### BƯỚC 3: Chạy kịch bản và xem kết quả

Thực thi lệnh sau trong terminal:
```python
python monitor_drift.py
```

Sau khi chạy xong, thư mục của bạn sẽ xuất hiện một file tên là **`data_drift_report.html`**. 

Hãy mở file HTML này bằng trình duyệt web. Bạn sẽ thấy một giao diện cực kỳ trực quan hiển thị:
* Tỷ lệ các cột dữ liệu bị "Drift" (Lệch).
* Biểu đồ phân phối so sánh giữa dữ liệu cũ và dữ liệu mới.
* Cảnh báo rõ ràng liệu mô hình có đang gặp nguy hiểm do dữ liệu đầu vào thay đổi hay không.

---

### 🛡️ Góc nhìn MLOps / DevSecOps:
* **Continuous Monitoring (Giám sát liên tục):** Thay vì đợi hệ thống sập hoặc khách hàng phàn nàn, các kỹ sư MLOps thiết lập cronjob hoặc pipeline chạy định kỳ báo cáo này. 
* **Automated Retraining Trigger:** Khi tỷ lệ Data Drift vượt ngưỡng cảnh báo (ví dụ > 50%), hệ thống tự động kích hoạt pipeline huấn luyện lại mô hình với dữ liệu mới nhất.
