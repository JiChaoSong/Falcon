FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv

COPY falcon-shared /srv/falcon-shared
RUN pip install --no-cache-dir /srv/falcon-shared

COPY falcon-worker/requirements.txt /srv/falcon-worker/requirements.txt
RUN pip install --no-cache-dir -r /srv/falcon-worker/requirements.txt

COPY falcon-worker /srv/falcon-worker

WORKDIR /srv/falcon-worker

EXPOSE 50061

CMD ["python", "worker.py", "--env-file", ".env.worker"]
