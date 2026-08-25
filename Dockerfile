# Image serving tối ưu bảo mật: slim, non-root, không công cụ build dư thừa
FROM python:3.10-slim

WORKDIR /app

# Không cài build-essential: mọi dependency đều có wheel chính thức.
# Gỡ thêm build-tool dư thừa mà base image có thể mang theo (wheel, jaraco.*)
# — không dùng lúc runtime nhưng lại là bề mặt tấn công trong report Trivy.
# Dấu || true: một số biến thể base image không chứa chúng, uninstall sẽ lỗi.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    (pip uninstall -y --no-input wheel jaraco.context 2>/dev/null || true)

# Copy ứng dụng và artifact model đã được CI train + kiểm định trước đó
# (job build-and-scan tải artifacts/ từ bước train-and-register)
COPY app.py .
COPY artifacts/iris_model ./artifacts/iris_model
COPY artifacts/model_meta.json ./artifacts/model_meta.json

# Chạy bằng user thường, không phải root (giảm thiểu tác động nếu bị chiếm quyền)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV MLFLOW_LOCAL_MODEL_PATH=/app/artifacts/iris_model \
    MLFLOW_META_PATH=/app/artifacts/model_meta.json

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
