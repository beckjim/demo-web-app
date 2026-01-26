# Use Python 3.11 slim image
FROM python:3.11-slim

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

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
