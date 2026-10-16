# Common development tasks. Everything runs inside Docker.
# Run `make` or `make help` to list the available targets.

COMPOSE := docker compose
# One-off container for the API service (removed when the command ends).
RUN_API := $(COMPOSE) run --rm api

.DEFAULT_GOAL := help
.PHONY: help run up down logs shell makemigrations migrate seed test lint format

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

run: up migrate seed ## Start everything from scratch: services, migrations and demo users

up: ## Build and start all services in the background
	$(COMPOSE) up -d --build

down: ## Stop all services (data volumes are kept)
	$(COMPOSE) down

logs: ## Follow the logs of all services
	$(COMPOSE) logs -f

shell: ## Open a Django shell inside the API container
	$(RUN_API) python manage.py shell

makemigrations: ## Create migration files from model changes (and format them)
	$(RUN_API) sh -c "python manage.py makemigrations && ruff check --select I --fix --quiet . && ruff format --quiet ."

migrate: ## Apply database migrations
	$(RUN_API) python manage.py migrate

seed: ## Create the demo users (safe to run many times)
	$(RUN_API) python manage.py seed_users

test: ## Run the test suite
	$(RUN_API) pytest

lint: ## Check code style and common errors (does not modify files)
	$(RUN_API) sh -c "ruff check . && ruff format --check ."

format: ## Auto-fix lint issues and format the code
	$(RUN_API) sh -c "ruff check --fix . && ruff format ."
