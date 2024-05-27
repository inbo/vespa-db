#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Migrate the database
mkdir -p /workspaces/vespadb/logs
touch /workspaces/vespadb/logs/django.log
chmod -R 755 /workspaces/vespadb/logs

mkdir -p /workspaces/vespadb/static

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
exec /opt/vespadb-env/bin/poe "$@"

# Start server
echo "Starting server..."