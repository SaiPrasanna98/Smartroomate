#!/bin/bash
# SmartRoommate+ Microservices Startup Script

echo "🚀 Starting SmartRoommate+ Microservices Architecture"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Set environment variables
export COMPOSE_PROJECT_NAME=smartroommate
export POSTGRES_PASSWORD=smartroommate123
export JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

echo "🔧 Environment variables set"

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

services=("redis" "postgres" "auth-service" "profile-service" "matching-service" "api-gateway")

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "healthy"; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not healthy"
    fi
done

# Display service URLs
echo ""
echo "🌐 Service URLs:"
echo "================"
echo "API Gateway:     http://localhost:8000"
echo "Auth Service:    http://localhost:8001"
echo "Profile Service: http://localhost:8002"
echo "Matching Service: http://localhost:8003"
echo "Frontend:        http://localhost:3000"
echo ""

# Display API documentation
echo "📚 API Documentation:"
echo "==================="
echo "Gateway API Docs: http://localhost:8000/docs"
echo "Auth API Docs:    http://localhost:8001/docs"
echo "Profile API Docs: http://localhost:8002/docs"
echo "Matching API Docs: http://localhost:8003/docs"
echo ""

# Display health check URLs
echo "🏥 Health Check URLs:"
echo "===================="
echo "Gateway Health:  http://localhost:8000/health"
echo "Auth Health:     http://localhost:8001/health"
echo "Profile Health:  http://localhost:8002/health"
echo "Matching Health: http://localhost:8003/health"
echo ""

echo "🎉 SmartRoommate+ Microservices are running!"
echo ""
echo "📋 Quick Commands:"
echo "================="
echo "View logs:        docker-compose logs -f [service-name]"
echo "Stop services:    docker-compose down"
echo "Restart service:  docker-compose restart [service-name]"
echo "Scale service:    docker-compose up -d --scale [service-name]=[count]"
echo ""

# Test API Gateway
echo "🧪 Testing API Gateway..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API Gateway is responding"
else
    echo "❌ API Gateway is not responding"
fi

echo ""
echo "🎯 Ready to use SmartRoommate+!"
echo "Visit http://localhost:8000 to get started"

