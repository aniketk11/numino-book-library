#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE library_test;
    GRANT ALL PRIVILEGES ON DATABASE library_test TO $POSTGRES_USER;
EOSQL
