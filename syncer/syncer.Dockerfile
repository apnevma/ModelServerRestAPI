# syncer.Dockerfile
FROM python:3.12-slim

WORKDIR /syncer
COPY syncer.py .

RUN pip install watchdog

CMD ["python", "-u", "syncer.py"]