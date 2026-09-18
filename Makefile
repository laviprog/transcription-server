.DEFAULT_GOAL := help

COMPOSE := docker compose

.PHONY: help
help: ## Show available commands
	@echo "Available targets:"
	@echo "  install      Install all dependencies including dev"
	@echo "  env          Create .env from .env.example if missing"
	@echo "  hooks        Install pre-commit hooks"
	@echo "  lint         Check code style"
	@echo "  format       Auto-fix code style and formatting"
	@echo "  typecheck    Run static type checking"
	@echo "  test         Run tests with coverage"
	@echo "  check        Run linting, type checking, and tests"
	@echo "  pre-commit   Run pre-commit hooks on all files"
	@echo "  build        Build docker images"
	@echo "  up           Start services in background"
	@echo "  down         Stop services"

.PHONY: install
install: ## Install all dependencies (including dev)
	uv sync --all-extras

.PHONY: env
env: ## Create .env from .env.example (if missing)
	@test -f .env && echo ".env already exists" || (cp .env.example .env && echo ".env created")

.PHONY: hooks
hooks: ## Install pre-commit hooks
	pre-commit install

.PHONY: lint
lint: ## Check code style (ruff)
	ruff check
	ruff format --check

.PHONY: format
format: ## Auto-fix style and format code
	ruff check --fix
	ruff format

.PHONY: typecheck
typecheck: ## Run static type checking (ty)
	ty check

.PHONY: test
test: ## Run tests with coverage
	pytest -v

.PHONY: check
check: lint typecheck test ## Run all checks (lint + typecheck + test)

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

.PHONY: build
build: ## Build docker images
	docker compose build

.PHONY: up
up: ## Start services in background
	docker compose up -d

.PHONY: down
down: ## Stop services
	docker compose down
