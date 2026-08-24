# Sử dụng Python slim image chính thức để tối ưu dung lượng và bảo mật
FROM python:3.10-slim

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Cài đặt các gói hệ thống tối thiểu
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn ứng dụng (app.py) vào container
COPY app.py .

# Expose cổng mà ứng dụng sẽ chạy
EXPOSE 8000

# Lệnh khởi chạy ứng dụng khi container start
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]