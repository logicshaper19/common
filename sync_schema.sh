#!/bin/bash

# Schema Sync Script for PostgreSQL Consolidation
# Syncs schema between different PostgreSQL databases

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
PG_USER="elisha"
PG_HOST="localhost"
PG_PORT="5432"

# Source and target databases
SOURCE_DB="common_db"
DEV_DB="common_dev"
TEST_DB="common_test"

echo -e "${BLUE}🔄 PostgreSQL Schema Sync Script${NC}"
echo "=================================="

# Function to sync schema from source to target
sync_schema() {
    local source_db=$1
    local target_db=$2
    local description=$3
    
    echo -e "${YELLOW}📋 Syncing schema: ${source_db} → ${target_db} (${description})${NC}"
    
    # Create schema dump
    pg_dump -h $PG_HOST -p $PG_PORT -U $PG_USER -d $source_db --schema-only > /tmp/schema_${source_db}.sql
    
    # Apply schema to target
    psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $target_db -f /tmp/schema_${source_db}.sql
    
    # Clean up
    rm /tmp/schema_${source_db}.sql
    
    echo -e "${GREEN}✅ Schema synced successfully${NC}"
}

# Function to check if database exists
check_database() {
    local db_name=$1
    if psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d postgres -c "SELECT 1 FROM pg_database WHERE datname='$db_name';" | grep -q 1; then
        return 0
    else
        return 1
    fi
}

# Main sync process
main() {
    echo "Checking databases..."
    
    # Check if source database exists
    if ! check_database $SOURCE_DB; then
        echo -e "${RED}❌ Source database '$SOURCE_DB' does not exist${NC}"
        exit 1
    fi
    
    # Sync to development database
    if check_database $DEV_DB; then
        sync_schema $SOURCE_DB $DEV_DB "Development"
    else
        echo -e "${YELLOW}⚠️  Development database '$DEV_DB' does not exist, skipping...${NC}"
    fi
    
    # Sync to test database
    if check_database $TEST_DB; then
        sync_schema $SOURCE_DB $TEST_DB "Testing"
    else
        echo -e "${YELLOW}⚠️  Test database '$TEST_DB' does not exist, skipping...${NC}"
    fi
    
    echo
    echo -e "${GREEN}🎉 Schema sync completed!${NC}"
    echo
    echo "Current database status:"
    echo "======================="
    psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d postgres -c "\l" | grep common
}

# Run main function
main "$@"
