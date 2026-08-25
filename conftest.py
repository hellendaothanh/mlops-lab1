"""conftest.py đặt ở project root để pytest thêm thư mục gốc vào sys.path.

Nhờ vậy `from app import app` trong tests/ hoạt động bất kể cách gọi:
  - pytest tests          (console script - không tự thêm CWD vào sys.path)
  - python -m pytest tests (thêm CWD vào sys.path)
"""
