.PHONY: help start stop restart logs status clean install-client test examples

help:
	@echo "Lakehouse Platform - Available Commands:"
	@echo ""
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - Show logs from all services"
	@echo "  make status         - Show status of all services"
	@echo "  make clean          - Stop services and remove volumes"
	@echo "  make install-client - Install Python client"
	@echo "  make test           - Run tests"
	@echo "  make examples       - Run example scripts"
	@echo ""

start:
	@echo "Starting Lakehouse services..."
	docker-compose up -d
	@echo "Services started. Access points:"
	@echo "  MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
	@echo "  Spark Master:  http://localhost:8080"
	@echo "  Trino UI:      http://localhost:8082"
	@echo "  Unity Catalog: http://localhost:8081"

stop:
	@echo "Stopping Lakehouse services..."
	docker-compose down

restart:
	@echo "Restarting Lakehouse services..."
	docker-compose restart

logs:
	docker-compose logs -f

status:
	docker-compose ps

clean:
	@echo "Stopping services and removing volumes..."
	docker-compose down -v
	@echo "Cleanup complete"

install-client:
	@echo "Installing Lakehouse Python client..."
	cd client && pip install -e .
	@echo "Client installed successfully"

test:
	@echo "Running tests..."
	cd client && pytest tests/ -v

examples:
	@echo "Running example scripts..."
	@echo "\n=== Quickstart Example ==="
	cd examples && python quickstart.py
	@echo "\n=== Basic Usage Example ==="
	cd examples && python basic_usage.py
