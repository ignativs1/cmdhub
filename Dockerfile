FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CMDHUB_PORT=8080 \
    CMDHUB_HOST=0.0.0.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY cmdhub_cli.py .

EXPOSE 8080

VOLUME ["/app/data"]

CMD ["python", "app.py"]
