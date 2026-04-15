#!/bin/bash
echo "Starting Redis..."
brew services start redis

echo "Starting Daphne..."
daphne -p 8000 exammonitor.asgi:application &

echo "Starting Celery worker..."
celery -A exammonitor worker --loglevel=info &

echo "Starting Celery Beat..."
celery -A exammonitor beat --loglevel=info &

echo "All services running. Visit http://127.0.0.1:8000"
wait