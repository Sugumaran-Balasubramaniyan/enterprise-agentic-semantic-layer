"""Command-line semantic asset and reproducibility validation."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

from rdflib import Graph
from rdflib.compare import isomorphic

from .semantic_validation import ValidationResult, load_vocabulary, validate_graph

__all__ = [
    "ValidationResult",
    "VerificationReport",
    "assert_graph_isomorphic",
    "load_vocabulary",
    "main",
    "run_asset_verification",
    "run_research_verify",
    "validate_graph",
]


@dataclass(frozen=True)
class VerificationReport:
    """Machine-readable result of the local research verification boundary."""

    mode: Literal["assets", "final"]
    returncode: int
    scope: Literal["assets", "final"]
    interpreter: str
    validation: dict[str, Any] | None = None
    parity: dict[str, Any] | None = None
    benchmark: dict[str, Any] | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def return_code(self) -> int:
        """Compatibility spelling for callers that use snake case."""

        return self.returncode

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "returncode": self.returncode,
            "scope": self.scope,
            "interpreter": self.interpreter,
            "validation": self.validation,
            "parity": self.parity,
            "benchmark": self.benchmark,
            "errors": list(self.errors),
        }


def assert_graph_isomorphic(generated: Graph, checked_in: Graph) -> None:
    """Fail when two RDF graphs differ semantically, independent of serialization."""

    if not isomorphic(generated, checked_in):
        raise AssertionError(
            "generated and checked-in RDF graphs are not isomorphic "
            f"(generated={len(generated)} triples, checked_in={len(checked_in)} triples)"
        )


def _safe_environment(root: Path) -> dict[str, str]:
    """Build the minimal environment used by worker and final subprocesses."""

    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONPATH": str(root / "src"),
        "PYTHONNOUSERSITE": "1",
        "LC_ALL": "C",
        "LANG": "C",
    }


def _validate_interpreter(python: str, root: Path) -> str:
    """Resolve and execute the caller-supplied Python 3.12 interpreter safely."""

    candidate = Path(python).expanduser()
    if not candidate.is_absolute():
        rooted = root / candidate
        candidate = rooted if rooted.is_file() else Path(shutil.which(python) or "")
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise ValueError(f"interpreter is not executable: {python}")
    probe = (
        "import importlib, json, sys; "
        "[importlib.import_module(name) for name in "
        "('rdflib', 'pyshacl', 'yaml', 'pydantic', 'jsonschema')]; "
        "print(json.dumps({'version': list(sys.version_info[:2]), 'executable': sys.executable}))"
    )
    completed = subprocess.run(
        [str(candidate), "-c", probe],
        cwd=root,
        env=_safe_environment(root),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if completed.returncode:
        raise ValueError(
            f"interpreter probe failed ({completed.returncode}): "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        evidence = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValueError("interpreter is not compatible with Python 3.12") from error
    if evidence.get("version") != [3, 12]:
        raise ValueError(f"interpreter must be compatible with Python 3.12: {python}")
    # Preserve the virtual-environment path instead of resolving its Python
    # symlink to the system interpreter; site-packages are selected by the
    # supplied venv path.
    return str(candidate.absolute())


_VALIDATION_SCOPES = {
    "SUPPORT_VALID": "support",
    "SUPPORT_INVALID": "support",
    "ERP_VALID": "erp",
    "ERP_INVALID": "erp",
    "COMBINED_VALID": "combined",
    "PREREQUISITE_CYCLE_DEPTH": "algorithm",
}

# Byte identities are part of the reproducibility boundary.  The validation
# metadata remains the source of matrix results; these digests only detect a
# fixture changing in a way that leaves its parsed RDF graph unchanged (for
# example, a comment or whitespace-only edit).
_EXPECTED_ASSET_SHA256 = {
    "semantic/data/sap_support_graph.ttl": "e36887b065ea722861f7a5d9b382bdebea349f37f7360245843b8375db40b017",
    "semantic/data/support-graph-invalid.ttl": "0cf9c669679b9e80189dc20c96bb4e0fd1f2f35f59618380135d73db1e7b803c",
    "semantic/ontology/sample-graph-valid.ttl": "a71f3009c6b5961985ffac339f0725b994a385db899545a66a60168b409c09fe",
    "semantic/ontology/sample-graph-invalid.ttl": "599f008a5468f10de3d2a2c07364d249779b259908df6b682b5fb2007c3221c1",
    "semantic/ontology/sap_support.ttl": "40a24c18b2037fdc8e90843272801b21eb8eb062a65e1b98dcb776bc8bde3b30",
    "semantic/ontology/sap_ppms.ttl": "90aa9beea27ec0a04851255b003432a679b673bc7c39c422cf966bcdee7c49d8",
    "semantic/ontology/sap_erp.ttl": "9e3031e50268f6288b671f835a5059e042cd62ad0904a925754f55dfb9e1c971",
    "semantic/shapes/sap_support_shapes.ttl": "483850daf948b45f3984a0374fff59d8445d6f40e0c9ce8828a87b79c047ed76",
    "semantic/shapes/sap_erp_shapes.ttl": "e3d7dbb687800fd3a4d60b09a8551f4318553f148de43c61b009a9705090b647",
    "semantic/data/support-prerequisite-cycle.ttl": "2de2f0905ec6a2e0380cbfeac8a904db25b6124aa2669488a267200413078708",
    "semantic/data/support-prerequisite-depth17.ttl": "b38b8bc49bc421704535d60e89616e4f77ee5688e5ea63523c63fccb3e99d42d",
}

_WORKER_KEYS = {
    "returncode",
    "errors",
    "parity",
    "validation",
    "worker_interpreter",
    "scope",
}
_PARITY_KEYS = {
    "generated_path",
    "checked_in_path",
    "generated_triples",
    "checked_in_triples",
    "generated_reloaded",
    "worker_interpreter",
    "isomorphic",
}
_SHACL_ROW_KEYS = {
    "check_id",
    "data_paths",
    "shape_paths",
    "inference",
    "expected_conforms",
    "observed_conforms",
    "conforms",
    "violation_count",
    "data_sha256",
    "shape_sha256",
    "provenance_dataset_id",
    "result",
    "scope",
}
_ALGORITHM_ROW_KEYS = _SHACL_ROW_KEYS | {"algorithm_cases"}
_COMBINED_GRAPH_KEYS = {
    "data_paths",
    "shape_paths",
    "construction_order",
    "combined_graph_sha256",
    "combined_shapes_sha256",
    "inference",
    "conforms",
    "violation_count",
}


def _validated_metadata(root: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    """Attach scope evidence and fail closed on stale or unexpected evidence."""

    enriched = copy.deepcopy(metadata)
    checks = enriched.get("checks")
    if not isinstance(checks, list) or [row.get("check_id") for row in checks] != list(
        _VALIDATION_SCOPES
    ):
        raise ValueError("validation checks do not match the required matrix order")
    for row in checks:
        check_id = row["check_id"]
        scope = _VALIDATION_SCOPES[check_id]
        row["scope"] = scope
        result = row.get("result")
        if result not in {"PASS", "EXPECTED_NONCONFORMANT"}:
            raise ValueError(f"unexpected validation result for {check_id}: {result!r}")
        if check_id == "PREREQUISITE_CYCLE_DEPTH" and result != "PASS":
            raise ValueError("unexpected validation result for PREREQUISITE_CYCLE_DEPTH")
        data_paths = row.get("data_paths", [])
        shape_paths = row.get("shape_paths", [])
        for path_key, hash_key in (("data_paths", "data_sha256"), ("shape_paths", "shape_sha256")):
            paths = row.get(path_key, [])
            hashes = row.get(hash_key, [])
            if len(paths) != len(hashes):
                raise ValueError(f"hash count mismatch for {check_id}: {hash_key}")
            actual = []
            for relative in paths:
                path = root / relative
                if not path.is_file():
                    raise ValueError(f"validation asset is missing: {relative}")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if (
                    relative in _EXPECTED_ASSET_SHA256
                    and digest != _EXPECTED_ASSET_SHA256[relative]
                ):
                    raise ValueError(f"hash mismatch for canonical asset: {relative}")
                actual.append(digest)
            if actual != hashes:
                raise ValueError(f"hash mismatch for {check_id}: {hash_key}")
        if check_id != "PREREQUISITE_CYCLE_DEPTH":
            expected = row.get("expected_conforms")
            observed = row.get("observed_conforms")
            if result == "EXPECTED_NONCONFORMANT" and not (expected is False and observed is False):
                raise ValueError(f"unexpected validation result for {check_id}: {result!r}")
            if result == "PASS" and not (expected is True and observed is True):
                raise ValueError(f"unexpected validation result for {check_id}: {result!r}")
        del data_paths, shape_paths
    return enriched


def _run_asset_checks(root: Path) -> dict[str, Any]:
    """Execute generation, parity, and validation inside the asset worker."""

    from semantic_layer.kg.sap_dataset_generator import build_sap_support_graph
    from semantic_layer.research.benchmark_runner import build_validation_metadata

    checked_in_path = root / "semantic/data/sap_support_graph.ttl"
    with TemporaryDirectory(prefix="cifre-asset-") as temporary:
        generated_path = Path(temporary) / "sap_support_graph.ttl"
        generated_graph = build_sap_support_graph()
        generated_graph.serialize(destination=generated_path, format="turtle")
        reloaded_generated_graph = Graph().parse(generated_path, format="turtle")
        checked_in_graph = Graph().parse(checked_in_path, format="turtle")
        assert_graph_isomorphic(reloaded_generated_graph, checked_in_graph)
        parity = {
            "generated_path": str(generated_path),
            "checked_in_path": checked_in_path.relative_to(root).as_posix(),
            "generated_triples": len(reloaded_generated_graph),
            "checked_in_triples": len(checked_in_graph),
            "generated_reloaded": True,
            "worker_interpreter": sys.executable,
            "isomorphic": True,
        }
        validation = _validated_metadata(root, build_validation_metadata(root))
    return {"parity": parity, "validation": validation}


def run_asset_worker(root: Path) -> dict[str, Any]:
    """Private JSON worker entry point invoked under the supplied interpreter."""

    try:
        result = _run_asset_checks(Path(root).resolve())
    # Broad handling is intentional: the subprocess worker must serialize every drift.
    except Exception as error:  # noqa: BLE001
        return {
            "returncode": 1,
            "errors": [f"{type(error).__name__}: {error}"],
            "parity": None,
            "validation": None,
            "worker_interpreter": sys.executable,
            "scope": "assets",
        }
    return {
        "returncode": 0,
        "errors": [],
        "parity": result["parity"],
        "validation": result["validation"],
        "worker_interpreter": sys.executable,
        "scope": "assets",
    }


def _parse_worker_payload(stdout: str, expected_interpreter: str) -> dict[str, Any]:
    """Validate the worker's exact success contract before consuming evidence."""

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ValueError("asset worker payload is not valid JSON") from error
    if not isinstance(payload, dict) or set(payload) != _WORKER_KEYS:
        raise ValueError("asset worker payload keys do not match the exact contract")
    if payload["scope"] != "assets":
        raise ValueError("asset worker payload has an unexpected scope")
    if type(payload["returncode"]) is not int or payload["returncode"] != 0:
        errors = payload["errors"]
        detail = "; ".join(errors) if isinstance(errors, list) else "invalid worker errors"
        raise ValueError(f"asset worker did not report success: {detail}")
    if payload["worker_interpreter"] != expected_interpreter:
        raise ValueError("asset worker interpreter does not match the supplied interpreter")
    if payload["errors"] != []:
        raise ValueError("successful asset worker returned errors")

    parity = payload["parity"]
    if not isinstance(parity, dict) or set(parity) != _PARITY_KEYS:
        raise ValueError("asset worker parity evidence is incomplete")
    if parity["worker_interpreter"] != expected_interpreter:
        raise ValueError("asset parity interpreter does not match the supplied interpreter")
    if parity["generated_reloaded"] is not True or parity["isomorphic"] is not True:
        raise ValueError("asset worker parity evidence is not successful")

    validation = payload["validation"]
    if not isinstance(validation, dict) or set(validation) != {"checks", "combined_graph"}:
        raise ValueError("asset worker validation evidence is incomplete")
    checks = validation["checks"]
    expected_ids = list(_VALIDATION_SCOPES)
    if not isinstance(checks, list) or not all(isinstance(row, dict) for row in checks):
        raise ValueError("asset worker validation rows are incomplete or out of order")
    if [row.get("check_id") for row in checks] != expected_ids:
        raise ValueError("asset worker validation rows are incomplete or out of order")
    for row in checks:
        expected_keys = (
            _ALGORITHM_ROW_KEYS
            if row.get("check_id") == "PREREQUISITE_CYCLE_DEPTH"
            else _SHACL_ROW_KEYS
        )
        if set(row) != expected_keys:
            raise ValueError(f"asset worker validation row is incomplete: {row.get('check_id')}")
    combined = validation["combined_graph"]
    if not isinstance(combined, dict) or set(combined) != _COMBINED_GRAPH_KEYS:
        raise ValueError("asset worker combined graph evidence is incomplete")
    return payload


def _asset_verification(
    root: Path, python: str, mode: Literal["assets", "final"]
) -> VerificationReport:
    parity: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    benchmark: dict[str, Any] | None = None
    errors: list[str] = []
    interpreter = python
    try:
        interpreter = _validate_interpreter(python, root)
        worker_command = [
            interpreter,
            str(root / "scripts/research_verify.py"),
            "--asset-worker",
            "--root",
            str(root),
        ]
        worker = subprocess.run(
            worker_command,
            cwd=root,
            env=_safe_environment(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if worker.returncode:
            raise RuntimeError(
                f"asset worker failed ({worker.returncode}): "
                f"{worker.stderr.strip() or worker.stdout.strip()}"
            )
        payload = _parse_worker_payload(worker.stdout, interpreter)
        parity = payload.get("parity")
        validation = payload.get("validation")

        if mode == "final":
            with TemporaryDirectory(prefix="cifre-final-") as temporary:
                result_path = Path(temporary) / "cifre-benchmark-result.json"
                command = [
                    interpreter,
                    "-m",
                    "semantic_layer.research",
                    "--output",
                    str(result_path),
                ]
                completed = subprocess.run(
                    command,
                    cwd=root,
                    env=_safe_environment(root),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode:
                    raise RuntimeError(
                        f"benchmark command failed ({completed.returncode}): "
                        f"{completed.stderr.strip() or completed.stdout.strip()}"
                    )
                benchmark = {"command": command, "artifact": json.loads(result_path.read_text())}
    # Broad handling is intentional: verification must report every drift, not raise.
    except Exception as error:  # noqa: BLE001
        errors.append(f"{type(error).__name__}: {error}")

    return VerificationReport(
        mode=mode,
        returncode=0 if not errors else 1,
        scope=mode,
        interpreter=interpreter,
        validation=validation,
        parity=parity,
        benchmark=benchmark,
        errors=tuple(errors),
    )


def run_research_verify(
    root: Path,
    python: str,
    *,
    mode: Literal["assets", "final"],
) -> VerificationReport:
    """Run the reusable asset boundary, optionally followed by final checks."""

    if mode not in {"assets", "final"}:
        raise ValueError("mode must be 'assets' or 'final'")
    return _asset_verification(Path(root).resolve(), python, mode)


def run_asset_verification(root: Path, python: str) -> VerificationReport:
    """Run only generation/parity, SHACL matrix, and prerequisite evidence."""

    return run_research_verify(root, python, mode="assets")


def main(root: Path | None = None) -> int:
    root = root or Path(__file__).resolve().parents[2]
    shapes = root / "semantic" / "shapes" / "sap_erp_shapes.ttl"
    valid = root / "semantic" / "ontology" / "sample-graph-valid.ttl"
    invalid = root / "semantic" / "ontology" / "sample-graph-invalid.ttl"

    vocabulary = load_vocabulary(root / "semantic" / "vocabulary" / "sap_erp.yaml")
    print(f"Vocabulary: {len(vocabulary)} concepts loaded")
    results = []
    for path in (valid, invalid):
        result = validate_graph(path, shapes)
        results.append(result)
        expected = "conforms" if path == valid else "fails as expected"
        outcome = "CONFORMS" if result.conforms else "DOES NOT CONFORM"
        print(f"{path.name}: {outcome} ({expected})")
        if not result.conforms:
            print(result.report_text)
    valid_result, invalid_result = results
    return 0 if valid_result.conforms and not invalid_result.conforms else 1


if __name__ == "__main__":
    raise SystemExit(main())
