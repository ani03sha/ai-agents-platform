.PHONY: help infra-up infra-down infra-reset logs api worker token test lint fmt setup

help:
	@echo ""
	@echo "Infrastructure:"
	@echo "  make infra-up        Start infra + create topics + apply schema"
	@echo "  make infra-down      Stop infrastructure"
	@echo "  make infra-reset     Stop and delete all volumes (full wipe)"
	@echo "  make logs svc=NAME   Tail a container (e.g. svc=agents-postgres)"
	@echo ""
	@echo "Services:"
	@echo "  make api             Start the Agent Gateway (port 8010)"
	@echo "  make worker          Start the Agent Runtime worker (+ health 8011)"
	@echo ""
	@echo "Dev:"
	@echo "  make token           Mint a dev JWT access token"
	@echo "  make lint / fmt / test"
	@echo ""

infra-up:
	docker compose -f infrastructure/docker/docker-compose.infra.yml up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@chmod +x infrastructure/scripts/init_topics.sh infrastructure/scripts/init_db.sh
	@./infrastructure/scripts/init_topics.sh
	@./infrastructure/scripts/init_db.sh
	@docker compose -f infrastructure/docker/docker-compose.infra.yml ps

infra-down:
	docker compose -f infrastructure/docker/docker-compose.infra.yml down

infra-reset:
	docker compose -f infrastructure/docker/docker-compose.infra.yml down -v

logs:
	docker compose -f infrastructure/docker/docker-compose.infra.yml logs -f $(svc)

api:
	cd services/api && uv run uvicorn src.main:app --port 8010 --reload

worker:
	cd services/worker && uv run python -m src.main

token:
	@curl -s -X POST http://localhost:8010/v1/auth/token \
		-H "Content-Type: application/json" \
		-d '{"api_key": "dev-key-1"}' | python3 -c \
		"import sys,json; print(json.load(sys.stdin)['access_token'])"

test:
	uv run pytest services/ shared/ -v

lint:
	uv run ruff check services/ shared/

fmt:
	uv run ruff format services/ shared/

setup:
	uv sync
	cp -n .env.example .env || true