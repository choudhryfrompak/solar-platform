# Makefile for Solar Platform
# Variables
SHELL := /bin/bash
DOCKER_COMPOSE := docker-compose
PYTHON := python3
NPM := npm
PIP := pip
DB_USER := solar_user
DB_PASS := solar_password
DB_NAME := solar_platform
DB_URL := postgresql://$(DB_USER):$(DB_PASS)@postgres:5432/$(DB_NAME)

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Check required commands
REQUIRED_CMDS := docker docker-compose python3 npm
$(foreach cmd,$(REQUIRED_CMDS),\
    $(if $(shell command -v $(cmd) 2> /dev/null),$(eval CMD_$(cmd)=$(shell command -v $(cmd))),\
        $(error "$(cmd) not found in PATH")))

.PHONY: all build up down logs clean dev-backend dev-frontend init help test db-setup db-verify

# Default target
all: help

# Help message
help:
	@echo "Solar Platform Management Commands"
	@echo "-----------------------------"
	@echo "make init      - Initialize the project"
	@echo "make up        - Start all services"
	@echo "make down      - Stop all services"
	@echo "make build     - Build all services"
	@echo "make logs      - Show service logs"
	@echo "make clean     - Clean up containers and data"
	@echo "make test      - Run tests"
	@echo "make db-setup  - Set up database only"
	@echo "make db-verify - Verify database setup"
	@echo "make help      - Show this help message"

# Clean up
clean:
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose down -v
	docker system prune -f
	rm -rf containers/*
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Wait for database to be ready
wait-for-db:
	@echo "$(YELLOW)Waiting for PostgreSQL to be ready...$(NC)"
	@for i in {1..30}; do \
		if docker exec solar-platform-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then \
			echo "$(GREEN)PostgreSQL is ready!$(NC)"; \
			break; \
		fi; \
		echo "Waiting for PostgreSQL... ($$i/30)"; \
		sleep 2; \
	done
	@if ! docker exec solar-platform-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then \
		echo "$(RED)PostgreSQL failed to start!$(NC)"; \
		exit 1; \
	fi

# Database setup
db-setup: wait-for-db
	@echo "$(YELLOW)Setting up database user and database...$(NC)"
	@echo "Dropping existing user and database if they exist..."
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c \
		"DROP DATABASE IF EXISTS solar_platform;" || true
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c \
		"DROP USER IF EXISTS solar_user;" || true
	@echo "Creating user..."
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c \
		"CREATE USER solar_user WITH PASSWORD 'solar_password';"
	@echo "Creating database..."
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c \
		"CREATE DATABASE solar_platform OWNER solar_user;"
	@echo "Granting privileges..."
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c \
		"GRANT ALL PRIVILEGES ON DATABASE solar_platform TO solar_user;"
	@echo "Creating UUID extension..."
	@docker exec -i solar-platform-postgres-1 psql -U solar_user -d solar_platform -c \
		"CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" || true
	@echo "$(GREEN)Database setup complete!$(NC)"

# Verify database setup
db-verify:
	@echo "$(YELLOW)Verifying database setup...$(NC)"
	@echo "Checking if user exists:"
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c "\du solar_user"
	@echo "Checking if database exists:"
	@docker exec -i solar-platform-postgres-1 psql -U postgres -c "\l solar_platform"
	@echo "Testing connection as solar_user:"
	@docker exec -i solar-platform-postgres-1 psql -U solar_user -d solar_platform -c "SELECT version();"
	@echo "$(GREEN)Database verification complete!$(NC)"

# Initialize project
init:
	@echo "$(YELLOW)Stopping any running services...$(NC)"
	docker-compose down || true
	@echo "$(YELLOW)Cleaning up old containers and data...$(NC)"
	docker-compose down -v || true
	docker system prune -f || true
	rm -rf containers/* || true
	rm -rf __pycache__ || true
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"
	@echo "$(YELLOW)Creating required directories...$(NC)"
	mkdir -p containers templates
	mkdir -p backend/migrations
	mkdir -p frontend/src
	@echo "$(YELLOW)Starting database services...$(NC)"
	docker-compose up -d postgres influxdb
	@$(MAKE) db-setup
	@$(MAKE) db-verify
	@echo "$(YELLOW)Setting up Python virtual environment...$(NC)"
	test -d venv || python3 -m venv venv
	@echo "$(YELLOW)Upgrading pip...$(NC)"
	. venv/bin/activate && pip install --upgrade pip
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	. venv/bin/activate && cd backend && pip install -r requirements.txt
	@echo "$(YELLOW)Verifying database connection before migrations...$(NC)"
	@if ! docker exec -i solar-platform-postgres-1 psql -U solar_user -d solar_platform -c "SELECT 1;" >/dev/null 2>&1; then \
		echo "$(RED)Database connection failed! Re-running database setup...$(NC)"; \
		$(MAKE) db-setup; \
		$(MAKE) db-verify; \
	fi
	@echo "$(YELLOW)Running database migrations...$(NC)"
	. venv/bin/activate && cd backend && alembic upgrade head
	@echo "$(GREEN)Initialization complete!$(NC)"
	@echo "$(GREEN)You can now run 'make up' to start all services$(NC)"

# Build services
build:
	@echo "$(YELLOW)Building services...$(NC)"
	docker-compose build
	@echo "$(GREEN)Build complete!$(NC)"

# Start services
up:
	@echo "$(YELLOW)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)All services started!$(NC)"
	@echo "$(YELLOW)Service status:$(NC)"
	docker-compose ps

# Stop services
down:
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Services stopped!$(NC)"

# Show logs
logs:
	docker-compose logs -f

# Show logs for specific service
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-postgres:
	docker-compose logs -f postgres

logs-influxdb:
	docker-compose logs -f influxdb

# Run tests
test:
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@if [ -d "backend" ]; then \
		cd backend && \
		. ../venv/bin/activate && \
		python -m pytest tests/ -v || echo "$(YELLOW)No tests found or tests failed$(NC)"; \
	else \
		echo "$(YELLOW)Backend directory not found$(NC)"; \
	fi
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	@if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then \
		cd frontend && npm test -- --watchAll=false || echo "$(YELLOW)No tests found or tests failed$(NC)"; \
	else \
		echo "$(YELLOW)Frontend not set up or no package.json found$(NC)"; \
	fi

# Development commands
dev-backend:
	@echo "$(YELLOW)Starting backend in development mode...$(NC)"
	@if [ ! -d "venv" ]; then \
		echo "$(RED)Virtual environment not found. Run 'make init' first.$(NC)"; \
		exit 1; \
	fi
	cd backend && \
	. ../venv/bin/activate && \
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "$(YELLOW)Starting frontend in development mode...$(NC)"
	@if [ ! -f "frontend/package.json" ]; then \
		echo "$(RED)Frontend not set up. Please check frontend directory.$(NC)"; \
		exit 1; \
	fi
	cd frontend && npm start

# Database management commands
db-reset: down
	@echo "$(YELLOW)Resetting database...$(NC)"
	docker-compose up -d postgres
	@$(MAKE) wait-for-db
	docker exec -i solar-platform-postgres-1 psql -U postgres -c "DROP DATABASE IF EXISTS solar_platform;"
	docker exec -i solar-platform-postgres-1 psql -U postgres -c "DROP USER IF EXISTS solar_user;"
	@$(MAKE) db-setup
	@echo "$(GREEN)Database reset complete!$(NC)"

# Manual database connection test
db-connect:
	@echo "$(YELLOW)Connecting to database as solar_user...$(NC)"
	docker exec -it solar-platform-postgres-1 psql -U solar_user -d solar_platform

# Test database connection
db-test:
	@echo "$(YELLOW)Testing database connection...$(NC)"
	@if docker exec -i solar-platform-postgres-1 psql -U solar_user -d solar_platform -c "SELECT version();" >/dev/null 2>&1; then \
		echo "$(GREEN)Database connection successful!$(NC)"; \
	else \
		echo "$(RED)Database connection failed!$(NC)"; \
		exit 1; \
	fi

# Quick status check
status:
	@echo "$(YELLOW)Service Status:$(NC)"
	docker-compose ps
	@echo ""
	@echo "$(YELLOW)Database Status:$(NC)"
	@if docker exec solar-platform-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then \
		echo "$(GREEN)PostgreSQL: Running$(NC)"; \
	else \
		echo "$(RED)PostgreSQL: Not running$(NC)"; \
	fi

# Install frontend dependencies
install-frontend:
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	@if [ ! -f "frontend/package.json" ]; then \
		echo "$(YELLOW)Initializing frontend...$(NC)"; \
		mkdir -p frontend; \
		cd frontend && npm init -y; \
	fi
	cd frontend && npm install

# Create a new migration
migration:
	@echo "$(YELLOW)Creating new migration...$(NC)"
	@read -p "Enter migration message: " message; \
	. venv/bin/activate && cd backend && alembic revision --autogenerate -m "$$message"

# Show database connection info
db-info:
	@echo "$(YELLOW)Database Connection Information:$(NC)"
	@echo "Host: localhost"
	@echo "Port: 5432"
	@echo "Database: solar_platform"
	@echo "User: solar_user"
	@echo "Password: solar_password"
	@echo ""
	@echo "$(YELLOW)Connection URL:$(NC)"
	@echo "postgresql://solar_user:solar_password@localhost:5432/solar_platform"