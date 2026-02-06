# Use Python 3.14 slim image as base
FROM python:3.14-slim

# Install system dependencies including git for version control
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=employee_dialogue \
    FLASK_ENV=development

# Expose Flask default port
EXPOSE 5000
