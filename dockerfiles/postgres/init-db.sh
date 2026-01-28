#!/bin/bash
set -e

# This script runs after PostgreSQL starts
# It creates the application database if it doesn't exist

echo "=== Database Initialization Script ==="
echo "Checking if database '$POSTGRES_DB' exists..."

# Check if database exists, create if it doesn't
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'Database $POSTGRES_DB already exists' 
    WHERE EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB');
    
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB') THEN
            CREATE DATABASE "$POSTGRES_DB";
            RAISE NOTICE 'Database $POSTGRES_DB created successfully';
        END IF;
    END
    \$\$;
EOSQL

echo "=== Database initialization complete ==="


