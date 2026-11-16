# Nexus 로컬 실행 이미지 (D-053: 개인 노트북 Docker + n8n)
FROM python:3.11-slim
# libgomp1: lightgbm 런타임
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY docker/jobs.py /opt/jobs.py
WORKDIR /repo
ENV PYTHONPATH=/repo PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "/opt/jobs.py"]
