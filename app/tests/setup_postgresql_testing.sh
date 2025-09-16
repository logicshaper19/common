#!/bin/bash
# PostgreSQL Testing Setup Script

echo "🐳 Setting up PostgreSQL testing with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   - Open Docker Desktop from Applications"
    echo "   - Wait for it to show 'Docker Desktop is running'"
    exit 1
fi

echo "✅ Docker is running"

# Create PostgreSQL test container
echo "📦 Creating PostgreSQL test container..."
docker run --name test-postgres \
    -e POSTGRES_PASSWORD=test \
    -e POSTGRES_DB=common_test \
    -p 5433:5432 \
    -d postgres:13

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 10

# Check if container is running
if docker ps | grep -q test-postgres; then
    echo "✅ PostgreSQL test container is running"
    echo "📊 Database details:"
    echo "   - Host: localhost"
    echo "   - Port: 5433"
    echo "   - Database: common_test"
    echo "   - Username: postgres"
    echo "   - Password: test"
    echo ""
    echo "🚀 You can now run tests with PostgreSQL!"
    echo "   Run: python tests/run_postgresql_tests.py"
else
    echo "❌ Failed to start PostgreSQL container"
    exit 1
fi
