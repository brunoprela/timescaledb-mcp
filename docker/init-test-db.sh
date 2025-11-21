#!/bin/bash
set -e

# This script runs after the database is initialized
# Ensure the password is set correctly for external connections

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Set password explicitly (will use current password_encryption setting)
    ALTER USER postgres WITH PASSWORD 'postgres';
EOSQL

# Update pg_hba.conf to allow password authentication from all hosts
# Keep scram-sha-256 as it's more secure, just ensure password is set
# The default pg_hba.conf already has: host all all all scram-sha-256
# So we just need to make sure the password is correct

# Reload configuration to ensure changes take effect
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "SELECT pg_reload_conf();"

