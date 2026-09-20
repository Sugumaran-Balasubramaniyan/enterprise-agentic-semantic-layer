VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
# Prefer the managed environment when it exists, with a python3-only fallback
# for a fresh checkout.  A caller may still override PYTHON explicitly.
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3)

.PHONY: setup test lint validate-semantic check-yaml check-mappings-quality check-golden check-compiler demo evaluate run-api kg-build kg-validate research-benchmark research-demo research-verify
setup:
	python3.12 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip==25.2
	$(VENV_PYTHON) -m pip install --require-hashes -r constraints/py312.txt
test:
	$(PYTHON) -m pytest
lint:
	$(PYTHON) -m ruff check .
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
kg-build:
	$(PYTHON) -m semantic_layer.kg.sap_dataset_generator
kg-validate:
	$(PYTHON) -m pytest tests/semantic/test_sap_kg.py -v
research-benchmark:
	$(PYTHON) -m semantic_layer.research
research-demo:
	$(PYTHON) -m semantic_layer.demo_sap
research-verify:
	PYTHONPATH=src $(PYTHON) scripts/research_verify.py
	PYTHONPATH=src $(PYTHON) -m pytest tests/unit/test_claim_scan.py -q
	PYTHONPATH=src $(PYTHON) -m pytest -q
	PYTHONPATH=src $(PYTHON) -m ruff check .
