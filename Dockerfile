# Media Organizer - Docker 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY *.py ./

# 创建数据目录
RUN mkdir -p /app/data /app/config

# 默认命令
CMD ["python", "main.py", "--config", "/app/config/config.yaml"]
