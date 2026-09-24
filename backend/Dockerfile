# 使用官方稳定轻量 Python 3.12 基础镜像
FROM python:3.12-slim

WORKDIR /app

# 设置 Python 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

# 优先安装依赖，利用 Docker 构建缓存
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY app /app/app
COPY .env.example /app/.env.example

EXPOSE 8000

# 使用 Python 标准库进行容器健康检查，无需额外安装系统级 curl
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
