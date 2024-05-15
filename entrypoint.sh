#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Wait for the PostgreSQL database to be ready
echo "Waiting for PostgreSQL database..."
while ! pg_isready -h db -p 5432 -U vespauser; do
  sleep 1
done
echo "Database is up!"

# Migrate the database
echo "Applying database migrations..."
python manage.py migrate --noinput

# Load initial data if required
echo "Loading municipalities, provinces and anb areas..."
python manage.py load_municipalities
python manage.py load_provinces
python manage.py load_anb

echo "Assign provinces to municipalities..."
python manage.py assign_provinces_to_municipalities

echo "Sync with waarnemingen.be..."
python manage.py load_waarnemingen_observations

exec /opt/vespadb-env/bin/poe "$@"
