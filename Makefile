PY ?= python3
export PYTHONPATH := server:server/vendor

.PHONY: install test lint run docker core manifests endpoints docs agents generated manuals
install:
	$(PY) -m pip install -r requirements-dev.txt
test:
	$(PY) -m pytest tests -q
lint:
	ruff check .
run:
	$(PY) server/run_server.py
core:
	$(PY) scripts/sync_core.py
manifests:
	$(PY) scripts/build_manifests.py
endpoints:
	@echo "usage: $(PY) scripts/build_endpoints.py PATH/TO/octopus-rest-api-spec.json"
docs:
	$(PY) scripts/build_docs.py
agents:
	$(PY) scripts/build_agents.py
generated: manifests docs agents
	$(PY) scripts/build_postman.py
manuals:
	python3 scripts/build_manuals.py
docker:
	docker build -t fiscai-octopus-api-connector .
