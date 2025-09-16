run:
	uvicorn main:app --reload --port 8003

lib:
	pip freeze > requirements.txt

# Tests
test:
	source .venv/bin/activate && python -m pytest tests/ -v

test-cov:
	source .venv/bin/activate && python -m pytest --cov=app/services --cov-report=html:coverage --cov-report=term-missing --cov-fail-under=70 -v tests/

test-unit:
	source .venv/bin/activate && python -m pytest -m unit -v tests/
	
test-openai:
	source .venv/bin/activate && python -m pytest tests/test_openai_service.py -v

test-tournament:
	source .venv/bin/activate && python -m pytest tests/test_tournament_service.py -v

test-database:
	source .venv/bin/activate && python -m pytest tests/test_database_service.py -v

test-planning:
	source .venv/bin/activate && python -m pytest tests/test_ai_planning_service.py -v

test-security:
	source .venv/bin/activate && ENVIRONMENT=development python -m pytest tests/test_security.py -v

test-rate-limiter:
	source .venv/bin/activate && ENVIRONMENT=development python -m pytest tests/test_rate_limiter.py -v

test-integration:
	source .venv/bin/activate && python -m pytest -m integration -v tests/

test-all:
	source .venv/bin/activate && ENVIRONMENT=development python -m pytest tests/test_tournament_service.py tests/test_openai_service.py tests/test_database_service.py tests/test_ai_planning_service.py tests/test_security.py tests/test_rate_limiter.py --cov=app/services --cov-report=term-missing -v

# Installation
install-test:
	pip install -r requirements-test.txt

install-dev:
	pip install -e ".[dev]"

# Linting et formatage
format:
	black app/ tests/
	isort app/ tests/

format-check:
	black --check --diff app/ tests/
	isort --check-only --diff app/ tests/

lint:
	flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy app/ --ignore-missing-imports

# Sécurité
security:
	bandit -r app/ -f txt
	safety check

# Qualité de code complète
quality: format-check lint security test-all

# Docker
docker-build:
	docker build -t ai-tournament-service:latest .

docker-run:
	docker run -p 8003:8003 ai-tournament-service:latest

docker-build-prod:
	docker build --target production -t ai-tournament-service:prod .

docker-build-env:
	docker build --build-arg SUPABASE_URL=$$SUPABASE_URL \
		--build-arg SUPABASE_SERVICE_KEY=$$SUPABASE_SERVICE_KEY \
		--build-arg SUPABASE_KEY=$$SUPABASE_KEY \
		--build-arg OPENAI_API_KEY=$$OPENAI_API_KEY \
		--build-arg OPENAI_ASSISTANT_ID=$$OPENAI_ASSISTANT_ID \
		--build-arg ENVIRONMENT=$$ENVIRONMENT \
		--build-arg CORS_ORIGIN=$$CORS_ORIGIN \
		--build-arg TRUSTED_HOSTS=$$TRUSTED_HOSTS \
		-t ai-tournament-service:latest .

docker-run-env:
	docker run -p 8003:8003 \
		-e SUPABASE_URL=$$SUPABASE_URL \
		-e SUPABASE_SERVICE_KEY=$$SUPABASE_SERVICE_KEY \
		-e SUPABASE_KEY=$$SUPABASE_KEY \
		-e OPENAI_API_KEY=$$OPENAI_API_KEY \
		-e OPENAI_ASSISTANT_ID=$$OPENAI_ASSISTANT_ID \
		-e ENVIRONMENT=$$ENVIRONMENT \
		-e CORS_ORIGIN=$$CORS_ORIGIN \
		-e TRUSTED_HOSTS=$$TRUSTED_HOSTS \
		ai-tournament-service:latest

# Docker Compose
docker-compose-up:
	docker-compose up --build

docker-compose-down:
	docker-compose down

docker-compose-dev:
	docker-compose --profile dev up --build

# CI/CD
ci-test: format-check lint security test-all

# Release
release:
	npx semantic-release --config .releaserc.json

release-dry-run:
	npx semantic-release --dry-run --config .releaserc.json

# Nettoyage
clean:
	rm -rf coverage/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .bandit/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  run              - Lancer le serveur de développement"
	@echo "  test-all         - Lancer tous les tests avec couverture"
	@echo "  quality          - Vérifier la qualité du code (format, lint, security, tests)"
	@echo "  format           - Formater le code avec black et isort"
	@echo "  lint             - Vérifier le style et les types"
	@echo "  security         - Vérifier la sécurité"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     - Construire l'image Docker"
	@echo "  docker-run       - Lancer le conteneur Docker"
	@echo "  docker-build-env - Construire avec variables d'environnement"
	@echo "  docker-run-env   - Lancer avec variables d'environnement"
	@echo "  docker-compose-up - Lancer avec docker-compose"
	@echo "  docker-compose-dev - Lancer en mode développement"
	@echo "  docker-compose-down - Arrêter docker-compose"
	@echo ""
	@echo "Utilitaires:"
	@echo "  clean            - Nettoyer les fichiers temporaires"
	@echo "  help             - Afficher cette aide"

