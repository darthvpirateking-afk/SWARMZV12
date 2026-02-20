# SWARMZ Runtime Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8012

CMD ["sh", "-c", "python run_server.py --host 0.0.0.0 --port ${PORT:-8012}"]