VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
# Prefer the managed environment when it exists, with a python3-only fallback
# for a fresh checkout.  A caller may still override PYTHON explicitly.
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3)

.PHONY: setup test lint validate-semantic check-yaml check-publication-formats check-mappings-quality check-golden check-compiler demo evaluate run-api kg-build kg-validate research-benchmark research-demo research-verify
setup:
	python3.12 -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip==25.2
	$(VENV_PYTHON) -m pip install --require-hashes -r constraints/py312.txt
test:
	PYTHONPATH=src $(PYTHON) -m pytest
lint:
	PYTHONPATH=src $(PYTHON) -m ruff check .
validate-semantic:
	PYTHONPATH=src $(PYTHON) -m semantic_layer.validation
check-yaml:
	PYTHONPATH=src $(PYTHON) -c "from pathlib import Path; import yaml; files=[path for path in Path('.').rglob('*.yaml') if '.venv' not in path.parts and '.git' not in path.parts]; [yaml.safe_load(path.read_text(encoding='utf-8')) for path in files]; print(f'YAML: {len(files)} files parsed')"
check-publication-formats:
	PYTHONPATH=src $(PYTHON) scripts/check_publication_formats.py
check-mappings-quality:
	PYTHONPATH=src $(PYTHON) -m pytest tests/semantic/test_mappings.py tests/unit/test_quality.py -q
check-golden:
	PYTHONPATH=src $(PYTHON) -m pytest tests/golden -q
check-compiler:
	PYTHONPATH=src $(PYTHON) -m pytest tests/unit/test_compiler.py -q
demo:
	PYTHONPATH=src $(PYTHON) -m semantic_layer.demo
evaluate:
	PYTHONPATH=src $(PYTHON) -m semantic_layer.evaluation
run-api:
	PYTHONPATH=src $(PYTHON) -m uvicorn semantic_layer.api:app --reload
kg-build:
	PYTHONPATH=src $(PYTHON) -m semantic_layer.kg.sap_dataset_generator
kg-validate:
	PYTHONPATH=src $(PYTHON) -m pytest tests/semantic/test_sap_kg.py -v
research-benchmark:
	@benchmark_output=$$(mktemp); trap 'rm -f -- "$$benchmark_output"' EXIT; \
	PYTHONPATH=src $(PYTHON) -m semantic_layer.research --output "$$benchmark_output"
research-demo:
	PYTHONPATH=src $(PYTHON) -m semantic_layer.demo_sap
research-verify:
	PYTHONPATH=src $(PYTHON) scripts/research_verify.py
	$(MAKE) PYTHON=$(PYTHON) check-yaml
	$(MAKE) PYTHON=$(PYTHON) check-publication-formats
	PYTHONPATH=src $(PYTHON) -m pytest tests/unit/test_claim_scan.py tests/unit/test_final_readiness.py tests/unit/test_documentation_contract.py tests/research/test_contracts.py tests/research/test_result_artifact.py -q
	PYTHONPATH=src $(PYTHON) -m pytest -q
	PYTHONPATH=src $(PYTHON) -m ruff check .
