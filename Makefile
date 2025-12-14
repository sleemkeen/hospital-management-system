.PHONY: help install test test-cov run run-debug clean

PYTHON = ./venv/bin/python
PIP = ./venv/bin/pip
PYTEST = ./venv/bin/pytest
FLASK = ./venv/bin/flask

help:
	@echo "Hospital Management System - Available Commands"
	@echo "================================================"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage report"
	@echo "  make run        - Run the application"
	@echo "  make run-debug  - Run the application in debug mode"
	@echo "  make clean      - Remove cached files"

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=. --cov-report=term-missing --cov-report=html

run:
	$(PYTHON) app.py

run-debug:
	FLASK_DEBUG=1 $(PYTHON) app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true

