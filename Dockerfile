# Use Python 3.9 as base image for compatibility
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies required for PyMuPDF and Pillow
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads && chmod 755 uploads

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 4 --timeout 120