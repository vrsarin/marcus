.PHONY: lint test clean pre-build build post-build pre-test post-test setup purge

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
	uv export --format requirements.txt --output-file requirements.txt --no-annotate --no-hashes --no-group test --no-group poc

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
	curl -s -u admin:admin "http://localhost:9000/api/qualitygates/project_status?projectKey=marcus" | grep -q '"status":"OK"' || (echo "SonarQube quality gate failed!" && exit 1)

setup-sonar:
	npm install
	node scripts/sonar.js
setup:
	make teardown
	uv venv
	uv pip install . --group test --group poc
	uv export --format requirements.txt --output-file requirements.txt --no-annotate --no-hashes --no-group test --no-group poc	
	docker-compose up -d
	make setup-sonar
	python .\scripts\generate_env.py
	
teardown:	
	docker-compose down
	docker-compose rm -v -f
	docker volume prune -f
	make purge