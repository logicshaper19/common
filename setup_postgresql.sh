#!/bin/bash

# PostgreSQL Setup Script for Common DB
echo "Setting up PostgreSQL for Common DB application..."

# Check if PostgreSQL is running
if ! brew services list | grep postgresql@15 | grep started > /dev/null; then
    echo "Starting PostgreSQL service..."
    brew services start postgresql@15
fi

# Create the database and user
psql postgres << EOF
-- Create the database
CREATE DATABASE common_db;

-- Create the user 'elisha' with a password
CREATE USER elisha WITH ENCRYPTED PASSWORD 'password123';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE common_db TO elisha;

-- Grant usage on schema and create permissions
GRANT USAGE, CREATE ON SCHEMA public TO elisha;

-- Grant all privileges on all tables in the public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO elisha;

-- Grant all privileges on all sequences in the public schema
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO elisha;

-- Make sure the user can create tables and other objects
ALTER USER elisha CREATEDB;

-- Exit
\q
EOF

echo "✅ PostgreSQL setup completed!"
echo "Database: common_db"
echo "User: elisha"
echo "Connection string: postgresql://elisha:password123@localhost:5432/common_db"
