# 📝 TÀI LIỆU TỔNG HỢP: BÀI LAB 4 - GIÁM SÁT DATA DRIFT & VẬN HÀNH MÔ HÌNH

## 1. Bản chất của Data Drift trong MLOps
* **Khái niệm:** Là hiện tượng phân phối dữ liệu đầu vào trên môi trường Production thay đổi so với dữ liệu lịch sử (Reference Data) dùng để huấn luyện mô hình ban đầu.
* **Hậu quả:** Mô hình AI sẽ đưa ra các dự đoán sai lệch nghiêm trọng (sai lầm mang tính hệ thống) dù mã nguồn và tham số không hề thay đổi.

## 2. Giải pháp Giám sát Tự động (Custom Monitoring Script)
Thay vì phụ thuộc vào các thư viện bên thứ ba dễ bị lỗi tương thích phiên bản Python, một kỹ sư DevSecOps/MLOps hoàn toàn có thể tự viết script kiểm tra độ lệch phân phối thống kê (Mean, Standard Deviation) định kỳ.

### Kịch bản giám sát chuẩn (`monitor_drift.py`):
```python
import pandas as pd
import numpy as np

# 1. Dữ liệu lịch sử (Reference Data)
reference_data = pd.DataFrame({
    'area': np.random.normal(80, 10, 1000),
    'rooms': np.random.randint(2, 5, 1000)
})

# 2. Dữ liệu thực tế trên Production (Current Data)
current_data = pd.DataFrame({
    'area': np.random.normal(140, 15, 1000),
    'rooms': np.random.randint(3, 7, 1000)
})

# 3. Kiểm tra ngưỡng lệch (Threshold Check)
for column in reference_data.columns:
    ref_mean = reference_data[column].mean()
    cur_mean = current_data[column].mean()
    
    diff_percent = abs(cur_mean - ref_mean) / ref_mean * 100
    
    if diff_percent > 15:
        print(f"[ALERT] Phát hiện Data Drift trên cột '{column}': lệch {diff_percent:.2f}%")
        # Tại đây: Tự động bắn thông báo Slack/Webhook hoặc kích hoạt Retraining Pipeline
```

## 3. Tư duy Vận hành (MLOps / SecOps Mindset)
* **Phát hiện sớm:** Giám sát Data Drift giống như phát hiện xâm nhập (IDS) trong bảo mật mạng — phát hiện bất thường trước khi nó gây ra sự cố lớn cho hệ thống.
* **Auto-Retraining:** Khi phát hiện drift, hệ thống nên kích hoạt pipeline huấn luyện lại tự động với dữ liệu mới cập nhật để đảm bảo mô hình luôn thích ứng với thực tế.
