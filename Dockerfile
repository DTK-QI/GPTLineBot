# 使用 Python 官方映像檔作為基礎
FROM python:3.9-slim-buster

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

# 指定 Cloud Run 啟動應用程式的指令
CMD ["gunicorn", "--bind=0.0.0.0:8000", "main:app"]
