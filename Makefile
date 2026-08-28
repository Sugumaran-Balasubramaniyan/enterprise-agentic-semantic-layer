PYTHON ?= python

.PHONY: setup test lint validate-semantic check-yaml check-mappings-quality check-golden check-compiler demo evaluate run-api
setup:
	$(PYTHON) -m pip install -e '.[dev]'
test:
	$(PYTHON) -m pytest
lint:
	ruff check .
validate-semantic:
	$(PYTHON) -m semantic_layer.validation
check-yaml:
	$(PYTHON) -c "from pathlib import Path; import yaml; files=[path for path in Path('.').rglob('*.yaml') if '.venv' not in path.parts and '.git' not in path.parts]; [yaml.safe_load(path.read_text(encoding='utf-8')) for path in files]; print(f'YAML: {len(files)} files parsed')"
check-mappings-quality:
	$(PYTHON) -m pytest tests/semantic/test_mappings.py tests/unit/test_quality.py -q
check-golden:
	$(PYTHON) -m pytest tests/golden -q
check-compiler:
	$(PYTHON) -m pytest tests/unit/test_compiler.py -q
demo:
	$(PYTHON) -m semantic_layer.demo
evaluate:
	$(PYTHON) -m semantic_layer.evaluation
run-api:
	$(PYTHON) -m uvicorn semantic_layer.api:app --reload
