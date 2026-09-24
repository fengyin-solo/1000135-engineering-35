FROM python:3.12-slim
WORKDIR /srv/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 容器必须监听 0.0.0.0；端口由 APP_PORT 控制，默认仍是 8000
ENV APP_HOST=0.0.0.0
EXPOSE 8000
# 与本地 run.sh 走同一份配置来源：先校验配置，再按生效的 host/port 启动
CMD ["sh", "-c", "python -m app.run_config check && set -- $(python -m app.run_config listen) && exec uvicorn app.main:app --host \"$1\" --port \"$2\"", "run"]
