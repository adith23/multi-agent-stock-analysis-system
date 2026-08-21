.PHONY: install lint format test check schema load-test migrate run worker beat compose-up compose-down

install:
	python -m pip install -r backend/requirements/dev.txt

lint:
	cd backend && ruff check . && black --check .

format:
	cd backend && ruff check --fix . && black .

test:
	cd backend && pytest --cov --cov-report=term-missing

check:
	cd backend && python manage.py check

schema:
	cd backend && python manage.py spectacular --file openapi.yaml --validate

load-test:
	cd backend && locust -f tests/load/locustfile.py --headless -u 20 -r 5 -t 60s

migrate:
	cd backend && python manage.py migrate

bootstrap:
	cd backend && python manage.py bootstrap_infrastructure

run:
	cd backend && python manage.py runserver

worker:
	cd backend && celery -A config worker --loglevel=INFO

beat:
	cd backend && celery -A config beat --loglevel=INFO --scheduler=django_celery_beat.schedulers:DatabaseScheduler

compose-up:
	docker compose -f docker/docker-compose.yml up --build

compose-down:
	docker compose -f docker/docker-compose.yml down
