#!/bin/bash
set -e

echo "Initializing Cumpair PostgreSQL database..."

# Read password from Docker secret
if [ -f /run/secrets/db_password ]; then
    export POSTGRES_PASSWORD=$(cat /run/secrets/db_password)
fi

# Create Cumpair database schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable required extensions for Cumpair
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    
    -- Create indexes for performance (will be created by Alembic migrations)
    -- This script just ensures the database is ready for Cumpair
    
    -- Log initialization
    INSERT INTO information_schema.sql_features (feature_id, feature_name) 
    VALUES ('CUMPAIR_INIT', 'Cumpair Database Initialized') 
    ON CONFLICT DO NOTHING;
    
EOSQL

echo "Cumpair database initialization completed successfully"
