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

RUN chmod 444 main.py
RUN chmod 444 requirements.txt

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ENV PORT 8000

# Run the web service on container startup.
CMD [ "python", "main.py" ]
