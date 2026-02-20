#!/bin/bash
set -e

python -c "import employee_dialogue"
export SKIP_DB_INIT=1

gunicorn --bind 0.0.0.0:5000 --workers 2 --worker-class sync --timeout 120 --access-logfile - --error-logfile - "employee_dialogue:app" &
gunicorn --bind 0.0.0.0:443 --certfile certs/cert.pem --keyfile certs/key.pem --workers 2 --worker-class sync --timeout 120 --access-logfile - --error-logfile - "employee_dialogue:app"
