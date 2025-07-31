.PHONY: lint test clean pre-build build post-build pre-test post-test setup purge develop

lint:
	ruff .

purge:
	make clean
	@if exist .data (rmdir /s /q .data)

clean:
	python scripts/clean.py || python3 scripts/clean.py

pre-build:
	make clean
	make lint
	uv export --format requirements.txt --output-file requirements.txt --no-annotate --no-hashes --no-group test --no-group poc --no-group dev

build:


post-build:


pre-test:
	uv pip install . --group test

test:
	pytest tests/unit --cov=src --cov-report=term-missing -ra --cov-report=xml
	pytest tests/api --cov=src --cov-report=term-missing -ra --cov-report=xml
#    pytest tests/integration --cov=src --cov-report=term-missing -ra
	

post-test:
	coverage combine
	coverage xml
	sonar-scanner
	curl -s -u admin:P@ssw0rd$123 "http://localhost:9000/api/qualitygates/project_status?projectKey=marcus" | grep -q '"status":"OK"' || (echo "SonarQube quality gate failed!" && exit 1)
develop:
	make pre-test
	make test
	make post-test
	make pre-build
	make build
	make post-build

setup-sonar:
	npm install
	node scripts/sonar.js
setup:
	make teardown
	uv venv
	uv pip install . --group test --group poc --group dev
	uv export --format requirements.txt --output-file requirements.txt --no-annotate --no-hashes --no-group test --no-group poc	
	docker-compose up -d
	make setup-sonar
	python .\scripts\generate_env.py
	
teardown:	
	docker-compose down
	docker-compose rm -v -f
	docker volume prune -f
	make purge