# Phase II Part 3: Docker, Makefile, and Deployment

In this final part of Phase II, we'll containerize our application and prepare it for production deployment. We'll cover Docker configuration, a Makefile for common tasks, and deployment to Render.

## Table of Contents

1. [Docker Configuration](#docker-configuration)
2. [Makefile for Development](#makefile-for-development)
3. [Environment Configuration](#environment-configuration)
4. [Deployment to Render](#deployment-to-render)
5. [Testing the Production Setup](#testing-the-production-setup)

---

## Docker Configuration

Docker ensures our application runs consistently across different environments - developer machines, CI/CD pipelines, and production servers.

### Dockerfile

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

**Key decisions:**

1. **Python 3.11-slim**: Smaller image size while maintaining compatibility
2. **curl**: Added for health checks
3. **Layer caching**: Requirements copied first to cache dependencies
4. **Data directory**: Created for SQLite database persistence

### docker-compose.yml

```yaml
version: '3.8'

services:
  trip-planner:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - AMADEUS_API_KEY=${AMADEUS_API_KEY}
      - AMADEUS_API_SECRET=${AMADEUS_API_SECRET}
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
      - DAILY_API_LIMIT=${DAILY_API_LIMIT:-200}
      - DATABASE_PATH=/app/data/trip_planner.db
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Key features:**

1. **Volume mount**: `./data:/app/data` persists SQLite database
2. **Environment variables**: Injected from `.env` file
3. **Health check**: Verifies app is responding every 30 seconds
4. **Auto-restart**: Container restarts automatically on failure

### .dockerignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp

# Git
.git/
.gitignore

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Testing
.pytest_cache/
.coverage
htmlcov/

# Misc
*.log
*.md
blog/
.claude/
cookies.txt
data/
```

---

## Makefile for Development

A Makefile provides a consistent interface for common development tasks.

```makefile
# Trip Planner Makefile
# Common commands for development, testing, and deployment

.PHONY: help install run run-docker build test clean lint format deploy

# Default target
help:
	@echo "Trip Planner - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install        Install Python dependencies"
	@echo "  run            Run the app locally (port 5000)"
	@echo "  run-dev        Run with auto-reload (port 8000)"
	@echo ""
	@echo "Docker:"
	@echo "  build          Build Docker image"
	@echo "  run-docker     Run in Docker container"
	@echo "  stop-docker    Stop Docker container"
	@echo "  logs           Show Docker logs"
	@echo ""
	@echo "Quality:"
	@echo "  test           Run tests"
	@echo "  lint           Run linter (pylint)"
	@echo "  format         Format code (black)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Remove cache and temp files"
	@echo "  clean-docker   Remove Docker images and volumes"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy         Deploy to Render (requires render CLI)"
	@echo ""

# Development
install:
	pip install -r requirements.txt

run:
	python -m uvicorn app:app --host 0.0.0.0 --port 5000

run-dev:
	python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Docker
build:
	docker compose build

run-docker:
	docker compose up --build

stop-docker:
	docker compose down

logs:
	docker compose logs -f

# Quality
test:
	python -m pytest tests/ -v --cov=trip_planner --cov-report=html

lint:
	python -m pylint trip_planner/ app.py

format:
	python -m black trip_planner/ app.py
	python -m isort trip_planner/ app.py

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

clean-docker:
	docker compose down -v --rmi local

# Deployment
deploy:
	render blueprint deploy
```

### Common Commands

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run locally with auto-reload
make run-dev

# Build and run in Docker
make run-docker

# View Docker logs
make logs

# Stop Docker container
make stop-docker

# Clean up cache files
make clean
```

---

## Environment Configuration

### .env.example (Updated)

```env
# Required: Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Amadeus API (for flight search)
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret

# Rate Limiting (defaults shown)
DAILY_API_LIMIT=200
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100
ANONYMOUS_FREE_LIMIT=5

# Session Security (generate a random string for production)
SECRET_KEY=your-secret-key-here

# Database (default shown)
DATABASE_PATH=data/trip_planner.db
```

---

## Deployment to Render

Render is a cloud platform that supports Docker deployments with persistent storage - perfect for our SQLite-based application.

### render.yaml

```yaml
services:
  - type: web
    name: trip-planner
    runtime: docker
    dockerfilePath: ./Dockerfile
    plan: free  # Upgrade to starter/standard for production
    
    # Persistent disk for SQLite database
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 1
    
    # Environment variables
    envVars:
      - key: GOOGLE_API_KEY
        sync: false  # Set manually in Render dashboard
      - key: SECRET_KEY
        generateValue: true  # Auto-generated secure key
      - key: DATABASE_PATH
        value: /app/data/trip_planner.db
      - key: DAILY_API_LIMIT
        value: "200"
      - key: ANONYMOUS_FREE_LIMIT
        value: "5"
    
    # Health check
    healthCheckPath: /health
    
    # Auto-deploy on push to main
    autoDeploy: true
```

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add production deployment configuration"
   git push origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up (free tier available)

3. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect the `render.yaml` file

4. **Set Environment Variables**
   - In Render dashboard, set `GOOGLE_API_KEY`
   - Other variables are configured automatically

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (~2-3 minutes)
   - Your app will be available at `https://your-app-name.onrender.com`

### Why Render?

| Feature | Render | Google Cloud Run | Heroku |
|---------|--------|------------------|--------|
| Free Tier | Yes | Yes | No |
| SQLite Support | Persistent Disk | Ephemeral | Add-on |
| Docker Support | Native | Native | Native |
| Auto-deploy | GitHub integration | Cloud Build | GitHub |
| SSL | Automatic | Automatic | Automatic |

---

## Testing the Production Setup

### Local Docker Testing

```bash
# Build and run
make run-docker

# Test health endpoint
curl http://localhost:5000/health

# Test query endpoint
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"I want to plan a trip to Paris"}'

# Check rate limit headers
curl -I -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

### Verifying Persistence

```bash
# Register a user
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Restart container
make stop-docker
make run-docker

# Login should still work (data persisted)
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

---

## CI/CD Considerations

For now, we're using Render's built-in auto-deploy feature. A full CI/CD pipeline could be added later with:

1. **GitHub Actions** for:
   - Running tests on every PR
   - Linting and formatting checks
   - Security scanning

2. **Staging Environment** for:
   - Testing before production
   - Manual approval workflow

3. **Database Backups** for:
   - Daily SQLite backups
   - Point-in-time recovery

This is reserved for Phase III when we move to a more robust infrastructure.

---

## Summary

In this part, we:

1. Created a **Dockerfile** for containerized deployment
2. Set up **docker-compose.yml** for local development
3. Added a **Makefile** for common commands
4. Configured **render.yaml** for one-click deployment
5. Tested the complete production setup

## Next Steps

1. Start Docker Desktop
2. Run `make run-docker` to test locally
3. Push to GitHub
4. Deploy to Render
5. Share your public URL with users!

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Local Docker orchestration |
| `.dockerignore` | Exclude files from build |
| `Makefile` | Development commands |
| `render.yaml` | Render deployment config |
| `.env.example` | Environment template |

---

**Previous**: [Part 2: Authentication](part2-authentication.md)
