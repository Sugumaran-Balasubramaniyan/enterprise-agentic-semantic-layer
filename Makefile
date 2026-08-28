PYTHON ?= python

.PHONY: setup test lint validate-semantic demo evaluate run-api
setup:
	$(PYTHON) -m pip install -e '.[dev]'
test:
	$(PYTHON) -m pytest
lint:
	ruff check .
validate-semantic:
	$(PYTHON) -m semantic_layer.validation
demo:
	$(PYTHON) -m semantic_layer.demo
evaluate:
	$(PYTHON) -m semantic_layer.evaluation
run-api:
	$(PYTHON) -m uvicorn semantic_layer.api:app --reload
