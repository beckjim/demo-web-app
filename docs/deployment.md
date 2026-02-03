# Deployment

Deploy Employee Dialogue to production.

## Pre-Deployment Checklist

- ✅ All tests passing
- ✅ Code reviewed
- ✅ Version bumped in pyproject.toml
- ✅ CHANGELOG updated
- ✅ Database backed up
- ✅ Environment variables prepared
- ✅ SSL certificates ready
- ✅ Monitoring configured

## Environment Variables

### Required (All Environments)

```env
# Flask
SECRET_KEY=<cryptographically-random-string>
FLASK_ENV=production

# Microsoft Entra
AZURE_AD_CLIENT_SECRET=<from-azure-portal>
```

### Optional

```env
# Database (default: sqlite:///app.db)
DATABASE_URL=sqlite:///app.db

# Logging level (default: INFO)
LOG_LEVEL=INFO
```

## Deployment Methods

### Option 1: Traditional Server

#### Prerequisites
- Python 3.9+
- pip or uv
- Gunicorn
- Nginx (reverse proxy)
- SQLite or PostgreSQL

#### Steps

```bash
# 1. SSH to server
ssh user@server.com

# 2. Clone repository
git clone https://github.com/beckjim/employee-dialogue.git
cd employee-dialogue

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 5. Initialize database
python -c "from employee_dialogue import database; database.create_all()"

# 6. Create systemd service
sudo nano /etc/systemd/system/employee-dialogue.service
```

#### Systemd Service File

```ini
[Unit]
Description=Employee Dialogue Flask Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/employee-dialogue
ExecStart=/var/www/employee-dialogue/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:5000 \
    employee_dialogue:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable employee-dialogue
sudo systemctl start employee-dialogue
sudo systemctl status employee-dialogue
```

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Session handling
        proxy_set_header Cookie $http_cookie;
        proxy_cookie_path / "/";
    }
}
```

### Option 2: Docker

#### Prerequisites
- Docker
- Docker Compose

#### Steps

```bash
# 1. Build image
docker build -t employee-dialogue:latest .

# 2. Create .env file
cp .env.example .env
# Edit .env with production values

# 3. Start with compose
docker compose up -d

# 4. Check logs
docker compose logs -f web
```

#### Production Docker Compose

```yaml
version: '3.8'

services:
  web:
    image: employee-dialogue:latest
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - AZURE_AD_CLIENT_SECRET=${AZURE_AD_CLIENT_SECRET}
    volumes:
      - ./instance:/app/instance  # Database persistence
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/login"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped
```

### Option 3: Cloud Platform

#### Heroku

```bash
# 1. Create Procfile
echo "web: gunicorn employee_dialogue:app" > Procfile

# 2. Deploy
heroku create your-app-name
git push heroku main

# 3. Set environment variables
heroku config:set SECRET_KEY=your-secret
heroku config:set AZURE_AD_CLIENT_SECRET=your-secret
```

#### AWS Elastic Beanstalk

```bash
# 1. Install EB CLI
pip install awseb-cli

# 2. Initialize
eb init -p python-3.11 employee-dialogue

# 3. Create environment
eb create production

# 4. Set environment variables
eb setenv SECRET_KEY=your-secret AZURE_AD_CLIENT_SECRET=your-secret

# 5. Deploy
eb deploy
```

#### Google Cloud Run

```bash
# 1. Build container
docker build -t gcr.io/your-project/employee-dialogue .

# 2. Push to registry
docker push gcr.io/your-project/employee-dialogue

# 3. Deploy
gcloud run deploy employee-dialogue \
  --image gcr.io/your-project/employee-dialogue \
  --platform managed \
  --region us-central1 \
  --set-env-vars SECRET_KEY=your-secret
```

## Database Configuration

### SQLite (Development/Small Deployments)

Default configuration:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
```

**Pros:**
- No additional setup
- Single file
- Sufficient for small teams

**Cons:**
- Limited concurrency
- Single user at a time
- Not recommended for >50 concurrent users

### PostgreSQL (Production)

```python
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "postgresql://user:password@host:5432/database"
```

**Steps:**

1. Install PostgreSQL
2. Create database
3. Update DATABASE_URL environment variable
4. Run migrations

```bash
# Create database
createdb employee_dialogue

# Set in .env
DATABASE_URL=postgresql://user:pass@localhost/employee_dialogue
```

## Monitoring & Logging

### Application Logging

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Log Aggregation

Send logs to external service:

```bash
# With Papertrail
export PAPERTRAIL_API_TOKEN=your-token

# With ELK Stack
# Configure logstash to forward logs
```

### Monitoring Tools

- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Application Monitoring:** New Relic, Datadog
- **Error Tracking:** Sentry, Rollbar

## Backup & Recovery

### Database Backup

```bash
# SQLite
cp app.db app.db.backup.$(date +%Y%m%d_%H%M%S)

# PostgreSQL
pg_dump -U user database_name > backup.sql

# Automated backup (cron)
0 2 * * * /path/to/backup.sh
```

### Data Recovery

```bash
# Restore SQLite
cp app.db.backup app.db

# Restore PostgreSQL
psql -U user database_name < backup.sql
```

## Security Hardening

### HTTPS/SSL

```bash
# Generate self-signed certificate (testing)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Use Let's Encrypt (production)
certbot certonly --webroot -w /var/www -d yourdomain.com
```

### Security Headers

```nginx
add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt update && sudo apt upgrade

# Restart application
sudo systemctl restart employee-dialogue
```

## Scaling

### Horizontal Scaling

Run multiple instances behind load balancer:

```nginx
upstream app {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    location / {
        proxy_pass http://app;
    }
}
```

### Vertical Scaling

Increase gunicorn workers:

```bash
gunicorn --workers 8 --worker-class sync employee_dialogue:app
```

## Troubleshooting

### Application won't start

```bash
# Check logs
sudo journalctl -u employee-dialogue -n 50

# Test locally
python -c "from employee_dialogue import app; app.run()"
```

### Database connection issues

```bash
# Verify DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from sqlalchemy import create_engine; create_engine(environ['DATABASE_URL']).connect()"
```

### High memory usage

```bash
# Reduce gunicorn workers
gunicorn --workers 2 employee_dialogue:app

# Enable profiling
python -m flask --app employee_dialogue profile
```

## Next Steps

- [Development](development/building.md) - Build process
- [Configuration](configuration.md) - Configure application
