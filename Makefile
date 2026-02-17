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
