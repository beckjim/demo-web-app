# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install uv and openssl
RUN pip install --no-cache-dir uv && apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY docker-entrypoint.sh /app/entrypoint.sh

# Install dependencies
RUN uv pip install --system .

# Create instance directory for SQLite database and certs directory
RUN mkdir -p instance certs

# Generate self-signed certificate
RUN openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

RUN chmod +x /app/entrypoint.sh

# Expose ports 5000 and 443
EXPOSE 5000 443

# Set environment variables
ENV FLASK_APP=employee_dialogue
ENV PYTHONUNBUFFERED=1

# Run both HTTP and HTTPS servers
ENTRYPOINT ["/app/entrypoint.sh"]
