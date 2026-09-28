# docker build --platform linux/amd64 -t sottorabin/discord_timer ./frontend
# docker push sottorabin/discord_timer:latest

FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Tokyo

# requirements.txtをコピーしてパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Botのファイルをコピー
COPY . .

# コンテナ起動時にmain.pyを実行
CMD ["python3", "main.py"]
