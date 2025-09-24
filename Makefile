# Makefile for Agora Supply Chain Simulator

.PHONY: help install install-dev test test-cov lint format clean run docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install production dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  test        - Run tests"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  clean       - Clean up temporary files"
	@echo "  run         - Start the simulation server"
	@echo "  docs        - Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Testing
test:
	pytest

test-cov:
	pytest --cov=agents --cov=models --cov=simulation --cov=web --cov-report=html --cov-report=term

test-verbose:
	pytest -v

test-fast:
	pytest -x

# Code quality
lint:
	flake8 agents/ models/ simulation/ web/ tests/
	mypy agents/ models/ simulation/ web/

format:
	black agents/ models/ simulation/ web/ tests/
	isort agents/ models/ simulation/ web/ tests/

format-check:
	black --check agents/ models/ simulation/ web/ tests/
	isort --check-only agents/ models/ simulation/ web/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +

# Development
run:
	python web/app.py

run-debug:
	FLASK_ENV=development python web/app.py

# Documentation
docs:
	@echo "Documentation is available in:"
	@echo "  - README.md (main documentation)"
	@echo "  - .kiro/specs/ (design specifications)"
	@echo "  - CONTRIBUTING.md (contribution guidelines)"

# Git helpers
git-setup:
	git init
	git add .
	git commit -m "Initial commit: Agora Supply Chain Simulator"

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make run' to start the simulation server"

# CI/CD helpers
ci-test: install test lint

# Package building
build:
	python -m build

build-wheel:
	python setup.py bdist_wheel

# Docker (if needed in future)
docker-build:
	docker build -t agora-simulator .

docker-run:
	docker run -p 5000:5000 agora-simulator