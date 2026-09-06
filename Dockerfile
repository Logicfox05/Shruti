# Multi-stage production Python build
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Production Image
FROM python:3.11-slim

WORKDIR /app

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy project backend and frontend
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .

# Create uploads directory with write permissions
RUN mkdir -p /app/backend/uploads

EXPOSE 8000

# Single worker: SQLite is a single-writer file database, so multiple workers cause
# "database is locked" errors. Binds to $PORT (Render provides it) or 8000 locally.
# Shell form so ${PORT} is expanded at runtime.
CMD gunicorn backend.app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
