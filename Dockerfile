# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv and openssl
RUN pip install --no-cache-dir uv && apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY app.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Create instance directory for SQLite database and certs directory
RUN mkdir -p instance certs

# Generate self-signed certificate
RUN openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Create entrypoint script to run both HTTP and HTTPS
RUN echo '#!/bin/bash\n\
gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class sync --timeout 120 --access-logfile - --error-logfile - app:app &\n\
gunicorn --bind 0.0.0.0:443 --certfile certs/cert.pem --keyfile certs/key.pem --workers 2 --worker-class sync --timeout 120 --access-logfile - --error-logfile - app:app\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose ports 5000 and 443
EXPOSE 5000 443

# Set environment variables
ENV FLASK_APP=app
ENV PYTHONUNBUFFERED=1

# Run both HTTP and HTTPS servers
ENTRYPOINT ["/app/entrypoint.sh"]
