# ============================================================================
# Makefile - Comandos comunes para desarrollo
# ============================================================================

.PHONY: help install dev test clean migrate deploy

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependencias
	pip install -r requirements.txt

dev: ## Inicia servidor de desarrollo
	uvicorn app.main:app --reload --port 8080

test: ## Ejecuta tests (TODO: agregar pytest)
	@echo "⚠️  Tests no implementados aún"

init-db: ## Inicializa la base de datos
	python scripts/init_db.py

migrate-create: ## Crea nueva migración (uso: make migrate-create MSG="descripción")
	alembic revision --autogenerate -m "$(MSG)"

migrate-up: ## Aplica migraciones pendientes
	alembic upgrade head

migrate-down: ## Revierte última migración
	alembic downgrade -1

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

deploy: ## Despliega a Google Cloud Run
	./deploy.sh

docker-build: ## Build imagen Docker localmente
	docker build -t nexus-legal-api:latest .

docker-run: ## Ejecuta contenedor Docker localmente
	docker run -p 8080:8080 --env-file .env nexus-legal-api:latest

format: ## Formatea código con black
	black app/ scripts/

lint: ## Ejecuta linter
	flake8 app/ --max-line-length=100

.DEFAULT_GOAL := help
