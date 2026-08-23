#!/usr/bin/env python3
"""Validate references to the preserved Week 2 IR v0.2 graph artifact.

The historical condition-C planner serialized only ``nodes`` and ``answer``
in ``attempts[*].raw_output``.  It then injected the graph envelope from the
planner input before storing ``attempts[*].graph`` and the row-level ``graph``.
This adapter replays exactly that boundary: it parses the raw serialization
with the preserved parser, accepts only those two raw keys, restores only the
five known envelope fields, and requires exact equality with the stored graph.
This is envelope reconstruction, not parser repair.

The preserved Python files remain read-only.  They are loaded under a private
in-memory package, the v0.2 registries are passed by explicit path, and the
validator is always called with ``generated_plan=True``.  Consequently the
preserved registry module's v0.1 default paths are never consulted.
"""

from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Iterable, Mapping


VALIDATOR_VERSION = "ir_v0_2_reference_validator_v0_1"
DEFAULT_ARTIFACT = (
    "historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl"
)
DEFAULT_ARTIFACT_SHA256 = (
    "62d806c69bf30125a25dab8fb4f0682f279b4cf3d6559de477dd888c0393757a"
)
APPROVED_AUTHORITY_COMMIT = "dcc5ac5c14e9acb5c689b400a4046708b6837ac3"
RECOVERY_MANIFEST_PATH = "historical/ir_v0_2/recovery_manifest_v0_1.json"
RECOVERY_MANIFEST_SHA256 = (
    "2ad207c4d5229d9ed32e763b71b3373b5a737cbc816338a1f759e55edd8fdd4e"
)
_PRESERVED_FILES: tuple[dict[str, Any], ...] = (
    {
        "original_path": "ir/spec_v0_2.md",
        "repository_relative_path": "historical/ir_v0_2/ir/spec_v0_2.md",
        "sha256": "d6b9bdae4b673ec7c756728bb343f4e99d43d5d3caa3332c408d8f682d84cd8e",
    },
    {
        "original_path": "ir/execution_graph.schema.json",
        "repository_relative_path": "historical/ir_v0_2/ir/execution_graph.schema.json",
        "sha256": "55ccc7721cccba570a94cea94452eccbb6409a45606adf2d79764df783bbbb63",
    },
    {
        "original_path": "ir/operator_registry_v0_2.json",
        "repository_relative_path": "historical/ir_v0_2/ir/operator_registry_v0_2.json",
        "sha256": "964eae96dd1942b904b5e6395bf9818dc3bc7d074f0d2523ef10263c609fea39",
    },
    {
        "original_path": "ir/type_registry_v0_2.json",
        "repository_relative_path": "historical/ir_v0_2/ir/type_registry_v0_2.json",
        "sha256": "c4d9e55851bd3d22274aeb89581d125673c90bb9db34fc3f3ace075538c21f80",
    },
    {
        "original_path": "src/hybridqa_graph/ir.py",
        "repository_relative_path": "historical/ir_v0_2/src/hybridqa_graph/ir.py",
        "sha256": "1dc669cfd7dadf6d646299c991db0f8f82dc2e64d5a61552f4686ee1d3da6e51",
    },
    {
        "original_path": "src/hybridqa_graph/planning.py",
        "repository_relative_path": "historical/ir_v0_2/src/hybridqa_graph/planning.py",
        "sha256": "19d9685b8133fa421bc54f73ecad3c80ff769ea574072b1d2f541d6be8e89cc1",
    },
    {
        "original_path": "src/hybridqa_graph/registry.py",
        "repository_relative_path": "historical/ir_v0_2/src/hybridqa_graph/registry.py",
        "sha256": "ec466b5647394053f360182fdb430a23b159386962c9e6b678845cd130230f40",
    },
    {
        "original_path": "src/hybridqa_graph/validator.py",
        "repository_relative_path": "historical/ir_v0_2/src/hybridqa_graph/validator.py",
        "sha256": "a8970505f1f31504753e6c6f0726129bc27acd59799eb8289ed09bb45562f871",
    },
    {
        "original_path": "experiments/results/week2_pilot/condition_C.jsonl",
        "repository_relative_path": (
            "historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl"
        ),
        "sha256": "62d806c69bf30125a25dab8fb4f0682f279b4cf3d6559de477dd888c0393757a",
        "record_count": 50,
    },
    {
        "original_path": "experiments/results/week2_pilot/run_manifest.json",
        "repository_relative_path": (
            "historical/ir_v0_2/experiments/results/week2_pilot/run_manifest.json"
        ),
        "sha256": "8ae5a7a84a35d5c9d50ce479b90bc6e487a3d2eaed2396f5af35cd5a5b93316a",
    },
)
_EXPECTED_RECOVERY_MANIFEST: dict[str, Any] = {
    "schema_version": "historical_ir_v0_2_recovery_manifest_v0_1",
    "status": "researcher_approved_authoritative",
    "authority_kind": "git_commit",
    "authority_identity": APPROVED_AUTHORITY_COMMIT,
    "recovery_source_kind": "researcher_approved_historical_workspace",
    "preservation_policy": (
        "All listed recovered files are byte-for-byte read-only evidence. "
        "Current-side adapters and reports must live outside this historical tree."
    ),
    "leakage_policy": (
        "The condition C artifact contains answers and evaluator outputs and must never "
        "be exposed to question-only semantic or topology annotation/prediction."
    ),
    "files": list(_PRESERVED_FILES),
}
_ENVELOPE_FIELDS = (
    "ir_version",
    "graph_id",
    "question_ref",
    "schema_ref",
    "sources",
)
_RAW_GRAPH_FIELDS = frozenset({"nodes", "answer"})
_FULL_GRAPH_FIELDS = frozenset((*_ENVELOPE_FIELDS, *_RAW_GRAPH_FIELDS))
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _issue(
    code: str,
    message: str,
    *,
    stage: str,
    graph_id: str | None = None,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"code": code, "message": message, "stage": stage}
    if graph_id is not None:
        result["graph_id"] = graph_id
    if path is not None:
        result["path"] = path
    if details:
        result["details"] = dict(details)
    return result


def _summary(
    artifact: str,
    expected_sha256: str,
    graph_id: str | None,
    all_graphs: bool,
) -> dict[str, Any]:
    return {
        "validator_version": VALIDATOR_VERSION,
        "status": "fail",
        "mode": "all" if all_graphs else "one",
        "requested_graph_id": graph_id,
        "artifact": {
            "path": artifact,
            "expected_sha256": expected_sha256,
            "observed_sha256": None,
        },
        "runtime": {
            "isolated_package": None,
            "ir_version": None,
            "registry_version": None,
            "authority_kind": "git_commit",
            "authority_identity": APPROVED_AUTHORITY_COMMIT,
            "recovery_manifest": RECOVERY_MANIFEST_PATH,
            "recovery_manifest_sha256": None,
            "operator_registry": "historical/ir_v0_2/ir/operator_registry_v0_2.json",
            "type_registry": "historical/ir_v0_2/ir/type_registry_v0_2.json",
            "schema": "historical/ir_v0_2/ir/execution_graph.schema.json",
        },
        "checks": [],
        "counts": {
            "records": 0,
            "graphs_selected": 0,
            "graphs_validated": 0,
            "preserved_files_verified": 0,
            "nodes": 0,
            "parse_errors": 0,
            "schema_errors": 0,
            "validator_errors": 0,
            "validator_warnings": 0,
            "dead_node_warnings": 0,
        },
        "error_code_counts": {},
        "warning_code_counts": {},
        "graphs": [],
        "errors": [],
        "warnings": [],
    }


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    errors = summary["errors"]
    warnings = summary["warnings"]
    summary["status"] = "pass" if not errors else "fail"
    summary["error_code_counts"] = dict(sorted(Counter(
        str(error.get("code", "UNKNOWN")) for error in errors
    ).items()))
    summary["warning_code_counts"] = dict(sorted(Counter(
        str(warning.get("code", "UNKNOWN")) for warning in warnings
    ).items()))
    return summary


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_command(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _verify_preserved_bundle(
    root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Bind all live preserved bytes to the approved immutable Git commit."""

    errors: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "authority_identity": APPROVED_AUTHORITY_COMMIT,
        "manifest_sha256": None,
        "files_verified": 0,
    }
    manifest_path = root / RECOVERY_MANIFEST_PATH
    try:
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        errors.append(_issue(
            "RECOVERY_MANIFEST_READ_FAILED",
            f"cannot read the IR v0.2 recovery manifest: {exc}",
            stage="preserved_bundle_authority",
            path=RECOVERY_MANIFEST_PATH,
        ))
        manifest_bytes = None

    if manifest_bytes is not None:
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        evidence["manifest_sha256"] = manifest_sha256
        if manifest_sha256 != RECOVERY_MANIFEST_SHA256:
            errors.append(_issue(
                "RECOVERY_MANIFEST_SHA256_MISMATCH",
                "recovery manifest bytes do not match the fixed approved manifest",
                stage="preserved_bundle_authority",
                path=RECOVERY_MANIFEST_PATH,
                details={
                    "expected": RECOVERY_MANIFEST_SHA256,
                    "observed": manifest_sha256,
                },
            ))
        try:
            manifest = json.loads(manifest_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(_issue(
                "RECOVERY_MANIFEST_INVALID_JSON",
                f"recovery manifest is not valid UTF-8 JSON: {exc}",
                stage="preserved_bundle_authority",
                path=RECOVERY_MANIFEST_PATH,
            ))
        else:
            if manifest != _EXPECTED_RECOVERY_MANIFEST:
                errors.append(_issue(
                    "RECOVERY_MANIFEST_CONTRACT_MISMATCH",
                    "recovery manifest metadata or exact ten-file inventory differs from the approved contract",
                    stage="preserved_bundle_authority",
                    path=RECOVERY_MANIFEST_PATH,
                ))

    expected_paths = sorted(
        specification["repository_relative_path"]
        for specification in _PRESERVED_FILES
    )
    expected_live_paths = sorted([*expected_paths, RECOVERY_MANIFEST_PATH])
    bundle_root = root / "historical" / "ir_v0_2"
    try:
        observed_live_paths = sorted(
            path.relative_to(root).as_posix()
            for path in bundle_root.rglob("*")
            if path.is_file()
        )
    except OSError as exc:
        errors.append(_issue(
            "PRESERVED_BUNDLE_INVENTORY_READ_FAILED",
            f"cannot enumerate the live preserved bundle: {exc}",
            stage="preserved_bundle_authority",
        ))
        observed_live_paths = []
    if observed_live_paths != expected_live_paths:
        errors.append(_issue(
            "PRESERVED_BUNDLE_LIVE_INVENTORY_MISMATCH",
            "live IR v0.2 bundle does not contain exactly the manifest and ten approved files",
            stage="preserved_bundle_authority",
            details={
                "missing": sorted(set(expected_live_paths) - set(observed_live_paths)),
                "unexpected": sorted(set(observed_live_paths) - set(expected_live_paths)),
            },
        ))

    try:
        object_type = _git_command(
            root,
            "cat-file",
            "-t",
            APPROVED_AUTHORITY_COMMIT,
        )
    except OSError as exc:
        errors.append(_issue(
            "GIT_AUTHORITY_CHECK_FAILED",
            f"cannot execute Git for preserved-bundle verification: {exc}",
            stage="preserved_bundle_authority",
        ))
        return evidence, errors
    if object_type.returncode != 0 or object_type.stdout != b"commit\n":
        errors.append(_issue(
            "GIT_AUTHORITY_COMMIT_UNAVAILABLE",
            "the fixed approved authority identity is not an available Git commit",
            stage="preserved_bundle_authority",
            details={
                "authority_identity": APPROVED_AUTHORITY_COMMIT,
                "git_stderr": object_type.stderr.decode("utf-8", errors="replace").strip(),
            },
        ))
        return evidence, errors

    tree = _git_command(
        root,
        "ls-tree",
        "-r",
        "-z",
        "--name-only",
        APPROVED_AUTHORITY_COMMIT,
        "--",
        "historical/ir_v0_2",
    )
    if tree.returncode != 0:
        errors.append(_issue(
            "GIT_AUTHORITY_INVENTORY_READ_FAILED",
            "cannot enumerate the approved commit's IR v0.2 tree",
            stage="preserved_bundle_authority",
            details={
                "git_stderr": tree.stderr.decode("utf-8", errors="replace").strip(),
            },
        ))
    else:
        try:
            authority_paths = sorted(
                value.decode("utf-8")
                for value in tree.stdout.split(b"\0")
                if value
            )
        except UnicodeDecodeError as exc:
            errors.append(_issue(
                "GIT_AUTHORITY_INVENTORY_NOT_UTF8",
                f"approved Git tree contains a non-UTF-8 path: {exc}",
                stage="preserved_bundle_authority",
            ))
        else:
            if authority_paths != expected_paths:
                errors.append(_issue(
                    "GIT_AUTHORITY_INVENTORY_MISMATCH",
                    "approved commit does not contain exactly the ten recovered IR v0.2 files",
                    stage="preserved_bundle_authority",
                    details={
                        "missing": sorted(set(expected_paths) - set(authority_paths)),
                        "unexpected": sorted(set(authority_paths) - set(expected_paths)),
                    },
                ))

    for specification in _PRESERVED_FILES:
        relative = specification["repository_relative_path"]
        expected_sha256 = specification["sha256"]
        live_path = root / relative
        try:
            live_bytes = live_path.read_bytes()
        except OSError as exc:
            errors.append(_issue(
                "PRESERVED_FILE_READ_FAILED",
                f"cannot read preserved file: {exc}",
                stage="preserved_bundle_authority",
                path=relative,
            ))
            continue
        live_sha256 = hashlib.sha256(live_bytes).hexdigest()
        if live_sha256 != expected_sha256:
            errors.append(_issue(
                "PRESERVED_FILE_LIVE_SHA256_MISMATCH",
                "live preserved file SHA-256 differs from the approved inventory",
                stage="preserved_bundle_authority",
                path=relative,
                details={"expected": expected_sha256, "observed": live_sha256},
            ))

        authority_blob = _git_command(
            root,
            "show",
            f"{APPROVED_AUTHORITY_COMMIT}:{relative}",
        )
        if authority_blob.returncode != 0:
            errors.append(_issue(
                "GIT_AUTHORITY_BLOB_READ_FAILED",
                "cannot read preserved file bytes from the approved commit with git show",
                stage="preserved_bundle_authority",
                path=relative,
                details={
                    "git_stderr": authority_blob.stderr.decode(
                        "utf-8", errors="replace"
                    ).strip(),
                },
            ))
            continue
        authority_sha256 = hashlib.sha256(authority_blob.stdout).hexdigest()
        if authority_sha256 != expected_sha256:
            errors.append(_issue(
                "GIT_AUTHORITY_BLOB_SHA256_MISMATCH",
                "approved commit blob SHA-256 differs from the fixed inventory",
                stage="preserved_bundle_authority",
                path=relative,
                details={"expected": expected_sha256, "observed": authority_sha256},
            ))
        if live_bytes != authority_blob.stdout:
            errors.append(_issue(
                "PRESERVED_FILE_GIT_AUTHORITY_MISMATCH",
                "live bytes differ from git show at the approved authority commit",
                stage="preserved_bundle_authority",
                path=relative,
            ))
        if live_sha256 == expected_sha256 and authority_sha256 == expected_sha256:
            evidence["files_verified"] += 1

    return evidence, errors


def _resolve_artifact(
    root: Path,
    artifact: str | Path,
) -> tuple[Path | None, str | None, dict[str, Any] | None]:
    supplied = Path(artifact)
    if supplied.is_absolute():
        return None, None, _issue(
            "ARTIFACT_PATH_NOT_REPOSITORY_RELATIVE",
            "artifact path must be repository-relative",
            stage="artifact_path",
            details={"path": str(artifact)},
        )
    try:
        resolved = (root / supplied).resolve()
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        return None, None, _issue(
            "ARTIFACT_PATH_OUTSIDE_PROJECT_ROOT",
            "artifact path does not resolve inside the project root",
            stage="artifact_path",
            details={"path": str(artifact), "reason": str(exc)},
        )
    if not resolved.is_file():
        return None, relative.as_posix(), _issue(
            "ARTIFACT_NOT_FILE",
            "artifact path does not name a regular file",
            stage="artifact_path",
            path=relative.as_posix(),
        )
    return resolved, relative.as_posix(), None


def _load_submodule(package_name: str, module_name: str, path: Path) -> ModuleType:
    qualified_name = f"{package_name}.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create an import specification for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    try:
        # Execute the approved source bytes directly so validation never writes
        # __pycache__ into the read-only historical evidence tree.
        source = path.read_bytes()
        code = compile(source, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(qualified_name, None)
        raise
    return module


@lru_cache(maxsize=4)
def _load_preserved_runtime(root_string: str) -> SimpleNamespace:
    root = Path(root_string)
    source_dir = root / "historical" / "ir_v0_2" / "src" / "hybridqa_graph"
    identity = hashlib.sha256(str(source_dir).encode("utf-8")).hexdigest()[:16]
    package_name = f"_pj_preserved_ir_v0_2_{identity}"

    package = sys.modules.get(package_name)
    package_created = package is None
    if package is None:
        package = ModuleType(package_name)
        package.__package__ = package_name
        package.__path__ = [str(source_dir)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package

    loaded_names: list[str] = []
    try:
        modules: dict[str, ModuleType] = {}
        for module_name in ("ir", "registry", "planning", "validator"):
            qualified_name = f"{package_name}.{module_name}"
            module = sys.modules.get(qualified_name)
            if module is None:
                module = _load_submodule(
                    package_name,
                    module_name,
                    source_dir / f"{module_name}.py",
                )
                loaded_names.append(qualified_name)
            modules[module_name] = module
        operator_path = (
            root / "historical" / "ir_v0_2" / "ir" / "operator_registry_v0_2.json"
        )
        type_path = root / "historical" / "ir_v0_2" / "ir" / "type_registry_v0_2.json"
        registry = modules["registry"].load_registries(
            operator_path=operator_path,
            type_path=type_path,
        )
        if registry.ir_version != "0.2" or registry.registry_version != "0.2":
            raise ValueError(
                "the explicitly loaded preserved registries are not the frozen v0.2 pair"
            )
    except BaseException:
        for name in reversed(loaded_names):
            sys.modules.pop(name, None)
        if package_created or not any(
            name.startswith(f"{package_name}.") for name in sys.modules
        ):
            sys.modules.pop(package_name, None)
        raise

    return SimpleNamespace(
        package_name=package_name,
        ir=modules["ir"],
        registry_module=modules["registry"],
        planning=modules["planning"],
        validator=modules["validator"],
        registry=registry,
    )


def _load_jsonl(path: Path) -> tuple[list[tuple[int, dict[str, Any]]], list[dict[str, Any]]]:
    records: list[tuple[int, dict[str, Any]]] = []
    errors: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    errors.append(_issue(
                        "BLANK_JSONL_RECORD",
                        "blank JSONL records are not allowed",
                        stage="jsonl",
                        path=f"line:{line_number}",
                    ))
                    continue
                try:
                    value = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    errors.append(_issue(
                        "INVALID_JSONL_RECORD",
                        f"cannot parse JSONL record: {exc}",
                        stage="jsonl",
                        path=f"line:{line_number}",
                    ))
                    continue
                if not isinstance(value, dict):
                    errors.append(_issue(
                        "JSONL_RECORD_NOT_OBJECT",
                        "each JSONL record must be an object",
                        stage="jsonl",
                        path=f"line:{line_number}",
                    ))
                    continue
                records.append((line_number, value))
    except (OSError, UnicodeError) as exc:
        errors.append(_issue(
            "ARTIFACT_READ_FAILED",
            f"cannot read artifact: {exc}",
            stage="jsonl",
        ))
    return records, errors


def _graph_identity(
    line_number: int,
    row: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    graph = row.get("graph")
    if not isinstance(graph, dict):
        return None, _issue(
            "TOP_LEVEL_GRAPH_NOT_OBJECT",
            "row.graph must be an object",
            stage="graph_selection",
            path=f"line:{line_number}.graph",
        )
    graph_id = graph.get("graph_id")
    if not isinstance(graph_id, str) or not graph_id:
        return None, _issue(
            "INVALID_TOP_LEVEL_GRAPH_ID",
            "row.graph.graph_id must be a non-empty string",
            stage="graph_selection",
            path=f"line:{line_number}.graph.graph_id",
        )
    return graph_id, None


def _json_pointer(parts: Iterable[Any]) -> str:
    encoded = []
    for part in parts:
        value = str(part).replace("~", "~0").replace("/", "~1")
        encoded.append(value)
    return "/" + "/".join(encoded) if encoded else ""


def _validate_one_graph(
    *,
    row: Mapping[str, Any],
    line_number: int,
    graph_id: str,
    runtime: SimpleNamespace,
    schema_validator: Any,
) -> dict[str, Any]:
    graph = row["graph"]
    graph_errors: list[dict[str, Any]] = []
    graph_warnings: list[dict[str, Any]] = []
    checks: list[str] = ["unique_top_level_graph_id"]
    parse_error_count = 0

    attempts = row.get("attempts")
    matching_attempts: list[Mapping[str, Any]] = []
    if isinstance(attempts, list):
        matching_attempts = [
            attempt
            for attempt in attempts
            if isinstance(attempt, Mapping) and attempt.get("graph") == graph
        ]
    else:
        graph_errors.append(_issue(
            "ATTEMPTS_NOT_ARRAY",
            "row.attempts must be an array",
            stage="attempt_selection",
            graph_id=graph_id,
            path=f"line:{line_number}.attempts",
        ))
        parse_error_count += 1

    if len(matching_attempts) != 1:
        graph_errors.append(_issue(
            "MATCHING_ATTEMPT_COUNT",
            "exactly one attempt.graph must equal the top-level row.graph",
            stage="attempt_selection",
            graph_id=graph_id,
            path=f"line:{line_number}.attempts",
            details={"matching_attempts": len(matching_attempts)},
        ))
        parse_error_count += 1
    else:
        checks.append("exactly_one_matching_attempt")
        attempt = matching_attempts[0]
        raw_output = attempt.get("raw_output")
        try:
            parsed = runtime.planning.parse_graph_output(raw_output)
        except Exception as exc:
            graph_errors.append(_issue(
                "PRESERVED_PARSER_EXCEPTION",
                f"preserved parser raised {type(exc).__name__}: {exc}",
                stage="parser",
                graph_id=graph_id,
                path=f"line:{line_number}.attempts.raw_output",
            ))
            parse_error_count += 1
            parsed = None
        if parsed is None:
            pass
        elif not parsed.parse_success or not isinstance(parsed.graph, dict):
            graph_errors.append(_issue(
                "RAW_OUTPUT_PARSE_FAILED",
                parsed.parse_error or "preserved parser did not return a graph object",
                stage="parser",
                graph_id=graph_id,
                path=f"line:{line_number}.attempts.raw_output",
            ))
            parse_error_count += 1
        else:
            checks.append("preserved_raw_output_parser")
            parsed_keys = frozenset(parsed.graph)
            if parsed_keys != _RAW_GRAPH_FIELDS:
                graph_errors.append(_issue(
                    "UNEXPECTED_RAW_GRAPH_KEYS",
                    "constrained-planner raw graph must contain exactly nodes and answer",
                    stage="envelope_reconstruction",
                    graph_id=graph_id,
                    details={
                        "actual": sorted(parsed_keys),
                        "expected": sorted(_RAW_GRAPH_FIELDS),
                    },
                ))
                parse_error_count += 1
            elif frozenset(graph) != _FULL_GRAPH_FIELDS:
                graph_errors.append(_issue(
                    "UNEXPECTED_STORED_GRAPH_KEYS",
                    "stored graph does not have the exact preserved v0.2 envelope",
                    stage="envelope_reconstruction",
                    graph_id=graph_id,
                    details={
                        "actual": sorted(graph),
                        "expected": sorted(_FULL_GRAPH_FIELDS),
                    },
                ))
                parse_error_count += 1
            else:
                reconstructed = {
                    field: attempt["graph"][field]
                    for field in _ENVELOPE_FIELDS
                }
                reconstructed["nodes"] = parsed.graph["nodes"]
                reconstructed["answer"] = parsed.graph["answer"]
                if reconstructed != graph:
                    graph_errors.append(_issue(
                        "RECONSTRUCTED_GRAPH_MISMATCH",
                        "parsed raw graph plus the known envelope does not equal row.graph",
                        stage="envelope_reconstruction",
                        graph_id=graph_id,
                    ))
                    parse_error_count += 1
                else:
                    checks.append("historical_constrained_planner_envelope_equality")

    try:
        schema_errors = sorted(
            schema_validator.iter_errors(graph),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                error.message,
            ),
        )
    except Exception as exc:
        schema_errors = []
        schema_error_count = 1
        graph_errors.append(_issue(
            "DRAFT_2020_12_SCHEMA_EXCEPTION",
            f"Draft 2020-12 validator raised {type(exc).__name__}: {exc}",
            stage="json_schema",
            graph_id=graph_id,
        ))
    else:
        schema_error_count = len(schema_errors)
    for error in schema_errors:
        graph_errors.append(_issue(
            "DRAFT_2020_12_SCHEMA_ERROR",
            error.message,
            stage="json_schema",
            graph_id=graph_id,
            path=_json_pointer(error.absolute_path),
            details={"validator": error.validator},
        ))
    if schema_error_count == 0:
        checks.append("draft_2020_12_schema")

    validator_error_count = 0
    validator_warning_count = 0
    try:
        validation_report = runtime.validator.validate_graph(
            graph,
            registry=runtime.registry,
            generated_plan=True,
        )
        for error in validation_report.errors:
            serialized = error.to_dict()
            graph_errors.append(_issue(
                serialized["code"],
                serialized["message"],
                stage="ir_validator",
                graph_id=graph_id,
                path=serialized.get("path"),
                details=serialized.get("details"),
            ))
        for warning in validation_report.warnings:
            serialized = warning.to_dict()
            graph_warnings.append(_issue(
                serialized["code"],
                serialized["message"],
                stage="ir_validator",
                graph_id=graph_id,
                path=serialized.get("path"),
                details=serialized.get("details"),
            ))
        validator_error_count = len(validation_report.errors)
        validator_warning_count = len(validation_report.warnings)
    except Exception as exc:
        validator_error_count = 1
        graph_errors.append(_issue(
            "PRESERVED_VALIDATOR_EXCEPTION",
            f"preserved validator raised {type(exc).__name__}: {exc}",
            stage="ir_validator",
            graph_id=graph_id,
        ))
    else:
        if validator_error_count == 0:
            checks.append("ir_v0_2_registry_validator")

    nodes = graph.get("nodes")
    return {
        "graph_id": graph_id,
        "question_id": (
            graph.get("question_ref", {}).get("question_id")
            if isinstance(graph.get("question_ref"), Mapping)
            else None
        ),
        "table_id": (
            graph.get("question_ref", {}).get("table_id")
            if isinstance(graph.get("question_ref"), Mapping)
            else None
        ),
        "line_number": line_number,
        "status": "pass" if not graph_errors else "fail",
        "checks": checks,
        "node_count": len(nodes) if isinstance(nodes, list) else 0,
        "parse_error_count": parse_error_count,
        "schema_error_count": schema_error_count,
        "validator_error_count": validator_error_count,
        "validator_warning_count": validator_warning_count,
        "errors": graph_errors,
        "warnings": graph_warnings,
    }


def validate_ir_v0_2_reference(
    *,
    artifact: str | Path = DEFAULT_ARTIFACT,
    sha256: str = DEFAULT_ARTIFACT_SHA256,
    graph_id: str | None = None,
    all_graphs: bool = False,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate one or every graph in a hash-bound preserved JSONL artifact.

    The returned object is stable, JSON-serializable, and intentionally uses
    the same ``status``/``checks``/``errors``/``warnings`` shape as the current
    annotation validator's per-record results.
    """

    artifact_text = str(artifact)
    summary = _summary(artifact_text, sha256, graph_id, all_graphs)
    root = _project_root() if project_root is None else Path(project_root).resolve()

    if all_graphs == (graph_id is not None):
        summary["errors"].append(_issue(
            "INVALID_SELECTION_MODE",
            "choose exactly one of graph_id or all_graphs=True",
            stage="arguments",
        ))
        return _finalize(summary)
    if not isinstance(sha256, str) or _SHA256_RE.fullmatch(sha256) is None:
        summary["errors"].append(_issue(
            "INVALID_EXPECTED_SHA256",
            "sha256 must be exactly 64 lowercase hexadecimal characters",
            stage="artifact_hash",
        ))
        return _finalize(summary)

    resolved, relative, path_error = _resolve_artifact(root, artifact)
    if relative is not None:
        summary["artifact"]["path"] = relative
    if path_error is not None or resolved is None:
        summary["errors"].append(path_error)
        return _finalize(summary)
    summary["checks"].append("artifact_repository_relative_path")

    try:
        observed_sha256 = _sha256_file(resolved)
    except OSError as exc:
        summary["errors"].append(_issue(
            "ARTIFACT_HASH_READ_FAILED",
            f"cannot hash artifact: {exc}",
            stage="artifact_hash",
        ))
        return _finalize(summary)
    summary["artifact"]["observed_sha256"] = observed_sha256
    if observed_sha256 != sha256:
        summary["errors"].append(_issue(
            "ARTIFACT_SHA256_MISMATCH",
            "artifact SHA-256 does not equal the required digest",
            stage="artifact_hash",
            details={"expected": sha256, "observed": observed_sha256},
        ))
        return _finalize(summary)
    summary["checks"].append("artifact_sha256")

    rows, row_errors = _load_jsonl(resolved)
    summary["counts"]["records"] = len(rows)
    summary["errors"].extend(row_errors)
    if row_errors:
        return _finalize(summary)
    if not rows:
        summary["errors"].append(_issue(
            "EMPTY_ARTIFACT",
            "artifact contains no JSONL records",
            stage="jsonl",
        ))
        return _finalize(summary)
    summary["checks"].append("jsonl_records")

    identities: list[tuple[int, Mapping[str, Any], str]] = []
    for line_number, row in rows:
        identity, identity_error = _graph_identity(line_number, row)
        if identity_error is not None:
            summary["errors"].append(identity_error)
        else:
            identities.append((line_number, row, identity))
    if summary["errors"]:
        return _finalize(summary)

    id_counts = Counter(identity for _, _, identity in identities)
    duplicates = sorted(identity for identity, count in id_counts.items() if count != 1)
    if duplicates:
        summary["errors"].append(_issue(
            "DUPLICATE_GRAPH_ID",
            "row.graph.graph_id values must be unique in the artifact",
            stage="graph_selection",
            details={
                "graph_ids": duplicates,
                "counts": {identity: id_counts[identity] for identity in duplicates},
            },
        ))
        return _finalize(summary)
    summary["checks"].append("unique_top_level_graph_ids")

    if all_graphs:
        selected = identities
    else:
        selected = [item for item in identities if item[2] == graph_id]
        if not selected:
            summary["errors"].append(_issue(
                "GRAPH_ID_NOT_FOUND",
                "requested graph_id does not occur in row.graph.graph_id",
                stage="graph_selection",
                graph_id=graph_id,
            ))
            return _finalize(summary)
    summary["counts"]["graphs_selected"] = len(selected)
    summary["checks"].append("graph_id_selection")

    authority_evidence, authority_errors = _verify_preserved_bundle(root)
    summary["runtime"]["recovery_manifest_sha256"] = authority_evidence[
        "manifest_sha256"
    ]
    summary["counts"]["preserved_files_verified"] = authority_evidence[
        "files_verified"
    ]
    if authority_errors:
        summary["errors"].extend(authority_errors)
        return _finalize(summary)
    summary["checks"].append("preserved_bundle_git_authority")

    try:
        runtime = _load_preserved_runtime(str(root))
    except Exception as exc:
        summary["errors"].append(_issue(
            "PRESERVED_RUNTIME_LOAD_FAILED",
            f"cannot load the isolated preserved IR runtime: {type(exc).__name__}: {exc}",
            stage="runtime",
        ))
        return _finalize(summary)
    summary["runtime"].update({
        "isolated_package": runtime.package_name,
        "ir_version": runtime.registry.ir_version,
        "registry_version": runtime.registry.registry_version,
    })
    summary["checks"].extend([
        "preserved_runtime_isolated_package",
        "explicit_v0_2_operator_and_type_registries",
    ])

    try:
        import jsonschema

        validator_class = getattr(jsonschema, "Draft202012Validator")
        schema_path = root / "historical" / "ir_v0_2" / "ir" / "execution_graph.schema.json"
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        validator_class.check_schema(schema)
        schema_validator = validator_class(schema)
    except Exception as exc:
        summary["errors"].append(_issue(
            "DRAFT_2020_12_VALIDATOR_LOAD_FAILED",
            f"cannot initialize Draft 2020-12 validation: {type(exc).__name__}: {exc}",
            stage="json_schema",
        ))
        return _finalize(summary)
    summary["checks"].append("draft_2020_12_validator_initialized")

    graph_results = [
        _validate_one_graph(
            row=row,
            line_number=line_number,
            graph_id=identity,
            runtime=runtime,
            schema_validator=schema_validator,
        )
        for line_number, row, identity in selected
    ]
    summary["graphs"] = graph_results
    summary["counts"]["graphs_validated"] = len(graph_results)
    summary["counts"]["nodes"] = sum(result["node_count"] for result in graph_results)
    summary["counts"]["parse_errors"] = sum(
        result["parse_error_count"] for result in graph_results
    )
    summary["counts"]["schema_errors"] = sum(
        result["schema_error_count"] for result in graph_results
    )
    summary["counts"]["validator_errors"] = sum(
        result["validator_error_count"] for result in graph_results
    )
    summary["counts"]["validator_warnings"] = sum(
        result["validator_warning_count"] for result in graph_results
    )
    summary["errors"] = [
        error
        for result in graph_results
        for error in result["errors"]
    ]
    summary["warnings"] = [
        warning
        for result in graph_results
        for warning in result["warnings"]
    ]
    summary["counts"]["dead_node_warnings"] = sum(
        warning.get("code") == "DEAD_NODE" for warning in summary["warnings"]
    )

    if summary["counts"]["parse_errors"] == 0:
        summary["checks"].extend([
            "preserved_raw_output_parser",
            "historical_constrained_planner_envelope_equality",
        ])
    if summary["counts"]["schema_errors"] == 0:
        summary["checks"].append("all_graphs_draft_2020_12_valid")
    if summary["counts"]["validator_errors"] == 0:
        summary["checks"].append("all_graphs_ir_v0_2_registry_valid")
    return _finalize(summary)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact",
        default=DEFAULT_ARTIFACT,
        help="repository-relative preserved condition-C JSONL artifact",
    )
    parser.add_argument(
        "--sha256",
        default=DEFAULT_ARTIFACT_SHA256,
        help="exact expected SHA-256 for --artifact",
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--graph-id", help="validate exactly one row.graph.graph_id")
    selection.add_argument("--all", dest="all_graphs", action="store_true", help="validate every graph")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_ir_v0_2_reference(
        artifact=args.artifact,
        sha256=args.sha256,
        graph_id=args.graph_id,
        all_graphs=args.all_graphs,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
