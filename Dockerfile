# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Create instance directory for SQLite database
RUN mkdir -p instance

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app
ENV PYTHONUNBUFFERED=1

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
