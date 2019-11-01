#!/bin/sh

# Start Gunicorn processes 
echo Starting Gunicorn.
exec gunicorn project.wsgi:application 
  --bind 0.0.0.0:8000 