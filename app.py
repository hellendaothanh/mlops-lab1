from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.linear_model import LinearRegression
import numpy as np

# 1. Huấn luyện trước một mô hình Linear Regression trong bộ nhớ khi khởi động
X = np.array([[50], [60], [80], [100], [120]])
y = np.array([[1.5], [1.8], [2.4], [3.0], [3.6]])
model = LinearRegression()
model.fit(X, y)

# 2. Khởi tạo FastAPI app
app = FastAPI(
    title="MLOps Demo API", 
    description="API dự đoán giá nhà đơn giản theo chuẩn MLOps",
    version="1.0.0"
)

class HouseInput(BaseModel):
    area: float

@app.get("/")
def home():
    return {"message": "MLOps Service is running securely!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
def predict(data: HouseInput):
    prediction = model.predict(np.array([[data.area]]))
    return {
        "input_area": data.area,
        "predicted_price_billion": round(float(prediction[0][0]), 2)
    }