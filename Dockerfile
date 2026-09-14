FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first for better Docker layer caching
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only backend application files
COPY backend/ /app/

# Run pytest during container build (build fails if tests fail)
RUN pytest

EXPOSE 8000

CMD ["python", "main.py"]