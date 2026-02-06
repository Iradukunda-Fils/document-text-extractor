# Makefile for DocuExtract Pro

.PHONY: help install test run clean docker-build docker-run

help: ## Show this help message
	@echo "DocuExtract Pro - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (creates venv if needed)
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@. venv/bin/activate && pip install -r requirements.txt

install-dev: install ## Install development dependencies
	@. venv/bin/activate && pip install pytest pytest-cov

test: ## Run unit tests
	@. venv/bin/activate && pytest -v tests/

test-cov: ## Run tests with coverage report
	@. venv/bin/activate && pytest --cov=text_extractor --cov-report=html tests/

extract: ## Extract text from file (usage: make extract FILE=path/to/file.pdf)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required. Usage: make extract FILE=path/to/file.pdf"; \
		exit 1; \
	fi
	@./extract "$(FILE)" $(ARGS)

run-app: ## Run Streamlit app
	@. venv/bin/activate && streamlit run app.py

docker-build: ## Build Docker image
	docker build -t docuextract-pro .

docker-run: ## Run Docker container
	docker run -p 8501:8501 docuextract-pro

docker-extract: ## Extract using Docker (usage: make docker-extract FILE=path/to/file.pdf)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required"; \
		exit 1; \
	fi
	@docker run -v "$(PWD):/workspace" docuextract-pro python -m text_extractor "/workspace/$(FILE)" $(ARGS)

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage

clean-all: clean ## Clean everything including venv
	rm -rf venv .venv

.DEFAULT_GOAL := help
