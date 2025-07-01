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
         
# Wait for Gunicorn to start
sleep 5

# Start Celery worker
echo "Starting Celery worker..."
celery -A vespadb worker --loglevel=info &

# Start Celery beat scheduler
echo "Starting Celery beat scheduler..."
celery -A vespadb beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Wait for celery to start
sleep 10

# Trigger initial celery tasks using Django management command
echo "Triggering initial cache warm-up tasks..."
python manage.py shell << EOF
from vespadb.observations.tasks.generate_geojson_task import generate_geojson_task
from vespadb.observations.tasks.generate_export import generate_hourly_export

print('Triggering GeoJSON cache warm-up...')
try:
    generate_geojson_task.delay({'visible': 'true', 'min_observation_datetime': '2024-04-01'})
    print('GeoJSON task queued successfully')
except Exception as e:
    print(f'Error queueing GeoJSON task: {e}')

print('Triggering hourly export generation...')
try:
    generate_hourly_export.delay()
    print('Export task queued successfully')
except Exception as e:
    print(f'Error queueing export task: {e}')

print('Initial tasks triggered.')
EOF

# Start Nginx
echo "Starting Nginx..."
nginx -g "daemon off;"
exec "$@"