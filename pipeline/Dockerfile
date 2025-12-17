# DSRP Knowledge Ingestion Pipeline
# Processes documents and extracts DSRP patterns

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline code
COPY . .

# Create directories for documents
RUN mkdir -p /documents/inbox /documents/processed

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command: process inbox
CMD ["python", "ingest.py"]
