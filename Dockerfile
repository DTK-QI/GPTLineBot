# 使用 Python 官方映像檔作為基礎
FROM python:3.10-slim
# 設定工作目錄
WORKDIR /app

# 安裝 git
RUN apt-get update && apt-get install -y git

# 複製 requirements.txt
COPY requirements.txt .

# 安裝相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY . .

# 指定執行應用程式的端口
ENV PORT=8000
EXPOSE 8000

# 啟動應用程式（這裡假設你使用 FastAPI 或 Flask）
CMD ["uvicorn", "app:main", "--host", "0.0.0.0", "--port", "8000"]
