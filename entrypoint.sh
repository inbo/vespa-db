#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Migrate the database
mkdir -p /workspaces/vespadb/logs
touch /workspaces/vespadb/logs/django.log
chmod -R 755 /workspaces/vespadb/logs

# Ensure static directory exists
mkdir -p /workspaces/vespadb/static
mkdir -p /workspaces/vespadb/collected_static

echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Load initial data if required
echo "Loading municipalities, provinces and anb areas..."
python manage.py load_municipalities
python manage.py load_provinces
python manage.py load_anb

echo "Assign provinces to municipalities..."
python manage.py assign_provinces_to_municipalities

echo "Create django admin user with python manage.py createsuperuser"
echo "Load waarnemingen observation data via: python manage.py load_waarnemingen_observations"

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --workers 3 \
         --timeout 1800 \
         --keep-alive 65 \
         --bind 0.0.0.0:8000 \
         vespadb.wsgi:application &
         
# Wait for Gunicorn to start
sleep 5

# Start Celery worker
echo "Starting Celery worker..."
celery -A vespadb worker --loglevel=info &

# Start Celery beat scheduler
echo "Starting Celery beat scheduler..."
celery -A vespadb beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Start Nginx
echo "Starting Nginx..."
nginx -g "daemon off;"
exec "$@"
