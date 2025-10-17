@echo off
REM SmartRoommate+ Microservices Startup Script for Windows

echo 🚀 Starting SmartRoommate+ Microservices Architecture
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are available

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data\postgres" mkdir data\postgres
if not exist "data\redis" mkdir data\redis

REM Set environment variables
set COMPOSE_PROJECT_NAME=smartroommate
set POSTGRES_PASSWORD=smartroommate123
set JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

echo 🔧 Environment variables set

REM Build and start services
echo 🏗️  Building and starting services...
docker-compose up --build -d

REM Wait for services to be healthy
echo ⏳ Waiting for services to be healthy...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...

REM Check each service
docker-compose ps redis | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ redis is healthy
) else (
    echo ❌ redis is not healthy
)

docker-compose ps postgres | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ postgres is healthy
) else (
    echo ❌ postgres is not healthy
)

docker-compose ps auth-service | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ auth-service is healthy
) else (
    echo ❌ auth-service is not healthy
)

docker-compose ps profile-service | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ profile-service is healthy
) else (
    echo ❌ profile-service is not healthy
)

docker-compose ps matching-service | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ matching-service is healthy
) else (
    echo ❌ matching-service is not healthy
)

docker-compose ps api-gateway | findstr "healthy" >nul
if %errorlevel% equ 0 (
    echo ✅ api-gateway is healthy
) else (
    echo ❌ api-gateway is not healthy
)

REM Display service URLs
echo.
echo 🌐 Service URLs:
echo ================
echo API Gateway:     http://localhost:8000
echo Auth Service:    http://localhost:8001
echo Profile Service: http://localhost:8002
echo Matching Service: http://localhost:8003
echo Frontend:        http://localhost:3000
echo.

REM Display API documentation
echo 📚 API Documentation:
echo ===================
echo Gateway API Docs: http://localhost:8000/docs
echo Auth API Docs:    http://localhost:8001/docs
echo Profile API Docs: http://localhost:8002/docs
echo Matching API Docs: http://localhost:8003/docs
echo.

REM Display health check URLs
echo 🏥 Health Check URLs:
echo ====================
echo Gateway Health:  http://localhost:8000/health
echo Auth Health:     http://localhost:8001/health
echo Profile Health:  http://localhost:8002/health
echo Matching Health: http://localhost:8003/health
echo.

echo 🎉 SmartRoommate+ Microservices are running!
echo.
echo 📋 Quick Commands:
echo =================
echo View logs:        docker-compose logs -f [service-name]
echo Stop services:    docker-compose down
echo Restart service:  docker-compose restart [service-name]
echo Scale service:    docker-compose up -d --scale [service-name]=[count]
echo.

REM Test API Gateway
echo 🧪 Testing API Gateway...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API Gateway is responding
) else (
    echo ❌ API Gateway is not responding
)

echo.
echo 🎯 Ready to use SmartRoommate+!
echo Visit http://localhost:8000 to get started

pause

