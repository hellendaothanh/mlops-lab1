import pandas as pd
import numpy as np

# 1. Tạo tập dữ liệu Gốc (Reference Data - lúc train mô hình)
np.random.seed(42)
reference_data = pd.DataFrame({
    'area': np.random.normal(80, 10, 1000),      # Diện tích trung bình quanh 80m2
    'rooms': np.random.randint(2, 5, 1000)       # Số phòng từ 2-4
})

# 2. Tạo tập dữ liệu Mới trên Production (Current Data - hành vi thay đổi, nhà to hơn)
current_data = pd.DataFrame({
    'area': np.random.normal(140, 15, 1000),     # Diện tích dịch chuyển lên quanh 140m2
    'rooms': np.random.randint(3, 7, 1000)       # Số phòng từ 3-6
})

print("=== BÁO CÁO GIÁM SÁT DATA DRIFT (CUSTOM PYTHON SCRIPT) ===\n")

# 3. Thuật toán phát hiện Drift đơn giản bằng cách so sánh Mean (Giá trị trung bình) và Std (Độ lệch chuẩn)
for column in reference_data.columns:
    ref_mean = reference_data[column].mean()
    cur_mean = current_data[column].mean()
    
    ref_std = reference_data[column].std()
    cur_std = current_data[column].std()
    
    # Tính độ chênh lệch phần trăm của giá trị trung bình
    diff_percent = abs(cur_mean - ref_mean) / ref_mean * 100
    
    print(f"Đặc trưng (Feature): '{column}'")
    print(f" - Mean lúc Train (Reference) : {ref_mean:.2f}")
    print(f" - Mean trên Production (Current): {cur_mean:.2f}")
    print(f" - Tỷ lệ lệch trung bình       : {diff_percent:.2f}%")
    
    # Ngưỡng cảnh báo drift: Nếu lệch > 15% thì cảnh báo
    if diff_percent > 15:
        print(f" ⚠️ CẢNH BÁO: Phát hiện Data Drift đáng kể trên cột '{column}'! Cần xem xét retrain mô hình.\n")
    else:
        print(f" ✅ Trạng thái: Ổn định.\n")

print("Hoàn thành quá trình kiểm tra Data Drift!")