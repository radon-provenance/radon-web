#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Exécute la commande passée au conteneur (gunicorn, etc.)
exec "$@"