FROM python:3.12-slim
WORKDIR /srv/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 容器里监听所有网卡；端口等其余配置与本地共用同一来源（环境变量，见 app/config.py）
ENV HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "-m", "app"]
