"""Regression tests for final semantic-layer readiness boundaries."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from semantic_layer.evaluation import GOLDEN_CASES, load_golden_cases, run_evaluation, runner
from semantic_layer.registry import SemanticRegistry
from semantic_layer.research.benchmark_runner import build_hash_manifest
from semantic_layer.validation import (
    scan_repository_legacy_uris,
    scan_repository_placeholders,
    scan_repository_secrets,
)
from tests.unit.test_claim_scan import (
    LEGACY_URI_CONTROL_DOCUMENTS,
    LEGACY_URI_FAMILIES,
    NON_PUBLICATION_SURFACE,
    scan_claim_surfaces,
)

ROOT = Path(__file__).resolve().parents[2]

SPEC_26_6_GLOBS = (
    ".github/workflows/ci.yml",
    "Makefile",
    "pyproject.toml",
    "constraints/py312.txt",
    "scripts/**/*.py",
    "semantic/**/*.ttl",
    "semantic/**/*.yaml",
    "semantic/**/*.json",
    "src/semantic_layer/**/*.py",
    "data/**/*.py",
    "tests/**/*.py",
    "tests/**/*.yaml",
    "tests/**/*.json",
    "examples/**/*",
    "README.md",
    "docs/**/*.md",
    "docs/**/*.json",
    "docs/**/*.sql",
    "mappings/**/*.yaml",
    "data_products/**/*.yaml",
    "results/**/*.json",
    "results/**/*.sql",
)


def _expected_manifest_paths(root: Path) -> list[str]:
    tracked = set(
        subprocess.check_output(["git", "ls-files", "-z"], cwd=root)
        .decode("utf-8")
        .split("\0")
    )
    return sorted(
        {
            relative
            for pattern in SPEC_26_6_GLOBS
            for path in root.glob(pattern)
            if path.is_file()
            for relative in (path.relative_to(root).as_posix(),)
            if relative in tracked
            and relative != "results/latest_benchmark.json"
            and ".git/" not in f"{relative}/"
            and ".venv/" not in f"{relative}/"
        }
    )


def _copy_tracked_repository(root: Path, destination: Path) -> Path:
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode("utf-8")
    for relative in filter(None, tracked.split("\0")):
        source = root / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    subprocess.run(["git", "init", "-q"], cwd=destination, check=True)
    subprocess.run(["git", "add", "."], cwd=destination, check=True)
    return destination


def _mutate_one_byte(root: Path, relative: str) -> None:
    path = root / relative
    data = bytearray(path.read_bytes())
    data[0] ^= 1
    path.write_bytes(data)


def test_final_hash_manifest_covers_complete_spec_26_6_scope(tmp_path: Path) -> None:
    artifact_path = ROOT / "results/latest_benchmark.json"
    assert artifact_path.is_file(), "canonical artifact must be published before final readiness"
    artifact = json.loads(artifact_path.read_bytes())
    manifest = artifact["hash_manifest"]
    entries = manifest["entries"]
    expected_paths = _expected_manifest_paths(ROOT)

    assert [entry["path"] for entry in entries] == expected_paths
    assert all(set(entry) == {"path", "sha256", "byte_length"} for entry in entries)
    assert manifest == build_hash_manifest(ROOT).to_dict()

    for index, relative in enumerate(
        (
            ".github/workflows/ci.yml",
            "constraints/py312.txt",
            "scripts/research_verify.py",
            "tests/unit/test_final_readiness.py",
            "src/semantic_layer/research/benchmark_runner.py",
            "docs/verification-report.md",
            "mappings/databricks/france.yaml",
        )
    ):
        copied = _copy_tracked_repository(ROOT, tmp_path / f"copy-{index}")
        _mutate_one_byte(copied, relative)
        assert build_hash_manifest(copied).to_dict() != manifest


def test_final_claim_and_secret_scan_is_clean() -> None:
    claim_paths = [ROOT / relative for relative in NON_PUBLICATION_SURFACE]
    assert scan_claim_surfaces(claim_paths) == []
    assert scan_repository_legacy_uris(ROOT) == []
    assert scan_repository_secrets(ROOT) == []
    assert scan_repository_placeholders(ROOT) == []

    assert set(LEGACY_URI_CONTROL_DOCUMENTS) == {
        "docs/superpowers/specs/2026-09-19-cifre-research-prototype-hardening-design.md",
        "docs/superpowers/plans/2026-09-19-cifre-research-prototype-hardening.md",
        "docs/research/cifre-hardening-baseline.md",
    }
    for relative in LEGACY_URI_CONTROL_DOCUMENTS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert any(uri in text for uri in LEGACY_URI_FAMILIES)


def test_repository_scanners_fail_closed_on_secret_and_placeholder_fixtures(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("credential=" + "A_real_value_that_must_not_ship_12345\n", encoding="utf-8")
    marker = tmp_path / "marker.md"
    marker.write_text("status: " + ("T" + "BD") + "\n", encoding="utf-8")

    assert scan_repository_secrets(tmp_path, paths=(secret,))
    assert scan_repository_placeholders(tmp_path, paths=(marker,))


def test_make_target_runs_source_verification_tests_and_locked_ruff() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    target = makefile.split("research-verify:", 1)[1].split("\n\n", 1)[0]
    assert "PYTHONPATH=src" in target
    assert "scripts/research_verify.py" in target
    assert "-m pytest" in target
    assert "-m ruff check ." in target
    assert "pip install -e" not in target


def test_ci_installs_hashed_third_party_lock_and_runs_research_verify() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "pip==25.2" in workflow
    assert "--require-hashes -r constraints/py312.txt" in workflow
    assert "make PYTHON=.venv/bin/python research-verify" in workflow
    assert "pip install -e" not in workflow


def test_explicit_answer_evaluation_uses_evidence_checked_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = SemanticRegistry.from_repository(ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "primary-claims")
    called = False

    def fake_execute(*_args: object, **_kwargs: object) -> tuple[list[dict[str, object]], list[str]]:
        nonlocal called
        called = True
        return list(case.deterministic.answer or ()), []

    monkeypatch.setattr(runner, "_execute_case", fake_execute)
    result = runner._evaluate_case(case, registry, ROOT)

    assert called is True
    assert result.deterministic_answer is True


def test_rows_only_fake_execution_result_fails_deterministic_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = SemanticRegistry.from_repository(ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "primary-claims")

    class FakeAgent:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def answer(self, *_args: object, **_kwargs: object) -> object:
            return SimpleNamespace(rows=list(case.deterministic.answer or ()))

    monkeypatch.setattr(runner, "ClaimsInvestigationAgent", FakeAgent)
    result = runner._evaluate_case(case, registry, ROOT)

    assert result.deterministic_answer is False
    assert any("evidence" in error for error in result.errors)


def test_evaluation_executes_against_the_supplied_registry_rules() -> None:
    registry = SemanticRegistry.from_repository(ROOT)
    case = next(case for case in load_golden_cases(GOLDEN_CASES) if case.id == "primary-claims")
    registry.rules["ciferp:QualifyingPosting"].include_statuses = []

    result = runner._evaluate_case(case, registry, ROOT)

    assert result.deterministic_answer is False
    assert any("execution evidence" in error for error in result.errors)


def test_discovery_only_denominator_includes_failed_applicable_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = SemanticRegistry.from_repository(ROOT)

    def fail_discovery_case(case: object, *_args: object) -> runner.CaseEvaluation:
        typed_case = case
        constraints = typed_case.deterministic.answer_constraints  # type: ignore[attr-defined]
        discovery_only = isinstance(constraints, dict) and constraints.get("mode") == "discovery_only"
        return runner.CaseEvaluation(
            case_id=typed_case.id,  # type: ignore[attr-defined]
            resolution=False,
            relationships=False,
            products=False,
            metrics=False,
            authorization=False,
            deterministic_answer=False,
            discovery_only=discovery_only,
        )

    monkeypatch.setattr(runner, "_evaluate_case", fail_discovery_case)
    report = run_evaluation(registry)

    assert report.discovery_only.total == 10
    assert report.discovery_only.passed == 0
