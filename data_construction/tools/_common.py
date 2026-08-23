"""Shared, dependency-light helpers for data-construction command line tools."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, Iterator


HISTORICAL_READ_ONLY_PATHS = (
    "data_analysis/week1_sample_100.jsonl",
    "evaluation/week2_eval_ids.json",
    "evaluation/week3_engineering_dev_ids.json",
    "evaluation/week3_locked_eval_ids.json",
    "evaluation/week3_split_manifest.json",
    "historical/ir_v0_2/ir/spec_v0_2.md",
    "historical/ir_v0_2/ir/execution_graph.schema.json",
    "historical/ir_v0_2/ir/operator_registry_v0_2.json",
    "historical/ir_v0_2/ir/type_registry_v0_2.json",
    "historical/ir_v0_2/src/hybridqa_graph/ir.py",
    "historical/ir_v0_2/src/hybridqa_graph/planning.py",
    "historical/ir_v0_2/src/hybridqa_graph/registry.py",
    "historical/ir_v0_2/src/hybridqa_graph/validator.py",
    "historical/ir_v0_2/experiments/results/week2_pilot/condition_C.jsonl",
    "historical/ir_v0_2/experiments/results/week2_pilot/run_manifest.json",
)


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        value[key] = item
    return value


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-standard non-finite JSON number: {value}")


def strict_json_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_reject_duplicate_object_keys,
        parse_constant=_reject_nonfinite_constant,
    )


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_nonfinite_constant,
        )


def iter_json_records(path: Path) -> Iterator[dict[str, Any]]:
    """Yield records from JSONL, a JSON array, or a common wrapped JSON object."""

    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = strict_json_loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number}: expected a JSON object")
                yield value
        return

    value = read_json(path)
    if isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        records = None
        for key in ("records", "questions", "data", "annotations", "items"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                records = candidate
                break
        if records is None:
            records = [value]
    else:
        raise ValueError(f"{path}: expected a JSON array or object")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"{path}: item {index} is not a JSON object")
        yield record


def write_json(path: Path, value: Any) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.write("\n")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
        for record in records
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def implementation_artifact_set_sha256(
    project_root: Path,
    implementation_paths: Iterable[Path],
) -> str:
    resolved_root = project_root.resolve()
    references: list[dict[str, str]] = []
    for path in implementation_paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(resolved_root).as_posix()
        except ValueError as exc:
            raise ValueError(f"implementation artifact is outside the repository: {path}") from exc
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"implementation artifact is missing or a symlink: {relative}")
        references.append({"repository_relative_path": relative, "sha256": sha256_file(path)})
    references.sort(key=lambda value: value["repository_relative_path"].encode("utf-8"))
    return canonical_json_sha256(references)


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_string_set_sha256(values: Iterable[str]) -> str:
    materialized = list(values)
    if any(
        not isinstance(value, str) or "\n" in value or "\r" in value
        for value in materialized
    ):
        raise ValueError("canonical string-set members must be strings without CR/LF")
    unique = set(materialized)
    payload = b"".join(
        value.encode("utf-8") + b"\n"
        for value in sorted(unique, key=lambda item: item.encode("utf-8"))
    )
    return hashlib.sha256(payload).hexdigest()


def git_commit_identity(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "NOT_A_GIT_REPOSITORY"


def git_tracked_commit_identity(
    project_root: Path,
    implementation_paths: Iterable[Path],
) -> str:
    """Return HEAD only when every implementation input is tracked and unchanged there."""

    resolved_root = project_root.resolve()
    root_result = subprocess.run(
        ["git", "-C", str(resolved_root), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if root_result.returncode != 0 or Path(root_result.stdout.strip()).resolve() != resolved_root:
        raise ValueError("project root is not the canonical Git work tree")
    head = git_commit_identity(resolved_root)
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise ValueError("cannot resolve a full lowercase Git HEAD commit")
    for path in implementation_paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"implementation artifact is outside the repository: {path}") from exc
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"implementation artifact is missing or a symlink: {relative.as_posix()}")
        relative_text = relative.as_posix()
        tracked = subprocess.run(
            ["git", "-C", str(resolved_root), "cat-file", "-e", f"HEAD:{relative_text}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if tracked.returncode != 0:
            raise ValueError(
                f"implementation artifact is not present in HEAD {head}: {relative_text}"
            )
        unchanged = subprocess.run(
            ["git", "-C", str(resolved_root), "diff", "--quiet", "HEAD", "--", relative_text],
            text=True,
            capture_output=True,
            check=False,
        )
        if unchanged.returncode == 1:
            raise ValueError(
                f"implementation artifact differs from HEAD {head}: {relative_text}"
            )
        if unchanged.returncode != 0:
            raise ValueError(f"cannot compare implementation artifact with HEAD: {relative_text}")
    return head


def stable_rank(seed: str, identifier: str) -> str:
    payload = f"{seed}\0{identifier}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def first_string(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(value)
    return None


def output_path_collision_errors(
    input_paths: dict[str, Path | None],
    output_paths: dict[str, Path | None],
) -> list[str]:
    """Report output/input and output/output collisions before any file is written."""
    resolved_inputs = {
        path.resolve(): label
        for label, path in input_paths.items()
        if path is not None
    }
    errors: list[str] = []
    seen_outputs: dict[Path, str] = {}
    for label, path in output_paths.items():
        if path is None:
            continue
        resolved = path.resolve()
        input_label = resolved_inputs.get(resolved)
        if input_label is not None:
            errors.append(f"output {label!r} collides with input {input_label!r}: {resolved}")
        previous_output = seen_outputs.get(resolved)
        if previous_output is not None:
            errors.append(f"outputs {previous_output!r} and {label!r} collide: {resolved}")
        else:
            seen_outputs[resolved] = label
    return errors


def historical_output_collision_errors(
    output_paths: dict[str, Path | None],
    project_root: Path,
) -> list[str]:
    protected = {
        (project_root.resolve() / relative).resolve(): relative
        for relative in HISTORICAL_READ_ONLY_PATHS
    }
    errors: list[str] = []
    for label, path in output_paths.items():
        if path is None:
            continue
        relative = protected.get(path.resolve())
        if relative is not None:
            errors.append(f"output {label!r} targets read-only historical evidence: {relative}")
    return errors
