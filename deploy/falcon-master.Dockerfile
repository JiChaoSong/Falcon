FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY falcon-shared /srv/falcon-shared
RUN pip install --no-cache-dir /srv/falcon-shared

COPY falcon-master/requirements.txt /srv/falcon-master/requirements.txt
RUN pip install --no-cache-dir -r /srv/falcon-master/requirements.txt

COPY falcon-master /srv/falcon-master

WORKDIR /srv/falcon-master

EXPOSE 8008
EXPOSE 50051

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008", "--loop", "asyncio", "--workers", "1"]
