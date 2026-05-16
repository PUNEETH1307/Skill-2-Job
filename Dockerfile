# Skill2Job Backend - Production Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for SpaCy and PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

# Copy application code
COPY backend/ .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Production server
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "run:app"]
