#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

# Load initial data if required
echo "After deployment check if municipalities, provinces, anb areas are loaded in. If not run following commands..."
echo "python manage.py load_municipalities , python manage.py load_provinces, python manage.py load_anb, python manage.py assign_provinces_to_municipalities"
echo "Need to update observations? Run python manage.py update_observations..."

echo "If observations need to be reloaded, to update location after new municipality data is loaded (or other changes), run:"
echo "python manage.py update_observations"

echo "Create django admin user with python manage.py createsuperuser"
echo "Load waarnemingen observation data via: python manage.py load_waarnemingen_observations"

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --workers 3 \
         --worker-class gthread \
         --threads 4 \
         --worker-connections 1000 \
         --timeout 1800 \
         --graceful-timeout 300 \
         --keep-alive 65 \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --bind 0.0.0.0:8000 \
         vespadb.wsgi:application &
         
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