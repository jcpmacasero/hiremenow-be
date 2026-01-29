#!/bin/bash
set -e

echo "Waiting for postgres to be ready..."

# Wait for postgres to be available
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - running migrations..."

# Run database migrations
alembic upgrade head

echo "Migrations complete - seeding admin user..."

# Seed admin user
python -m scripts.seed_admin

echo "Seeding complete - starting server..."

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
