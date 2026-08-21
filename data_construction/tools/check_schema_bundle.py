#!/usr/bin/env python3
"""Check that the versioned JSON schema/vocabulary bundle is portable and coherent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

from _common import read_json


EXPECTED_SCHEMAS = (
    "common_definitions_v0_1.json",
    "semantic_skeleton_v0_1.json",
    "information_obligation_v0_1.json",
    "abstract_topology_v0_1.json",
    "operator_topology_v0_1.json",
    "grounding_v0_1.json",
    "hierarchical_annotation_v0_1.json",
    "operator_vocabulary_schema_v0_1.json",
)
EXPECTED_VOCABULARIES = (
    "operator_vocabulary_coarse_v0_1.json",
    "operator_vocabulary_medium_v0_1.json",
    "operator_vocabulary_fine_v0_1.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--require-jsonschema", action="store_true")
    return parser.parse_args()


def refs(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                yield child
            else:
                yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


def nested_ids(value: Any, prefix: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}"
            if key == "$id" and isinstance(child, str):
                yield path, child
            yield from nested_ids(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from nested_ids(child, f"{prefix}[{index}]")


def resolve_pointer(document: Any, fragment: str) -> Any:
    if not fragment:
        return document
    if not fragment.startswith("/"):
        raise ValueError(f"unsupported non-JSON-Pointer fragment #{fragment}")
    current = document
    for token in fragment[1:].split("/"):
        token = unquote(token).replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(token)
    return current


def validate_ref(source_path: Path, reference: str, bundle_root: Path) -> None:
    if "://" in reference or reference.startswith("urn:"):
        raise ValueError(f"{source_path}: remote or URN $ref is not allowed in the self-contained bundle: {reference!r}")
    path_part, separator, fragment = reference.partition("#")
    target_path = source_path if not path_part else (source_path.parent / path_part).resolve()
    try:
        target_path.relative_to(bundle_root)
    except ValueError as exc:
        raise ValueError(f"{source_path}: $ref escapes the versioned data-construction bundle: {reference!r}") from exc
    if not target_path.is_file():
        raise FileNotFoundError(f"{source_path}: unresolved $ref {reference!r}")
    document = read_json(target_path)
    if separator:
        resolve_pointer(document, fragment)


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    schema_dir = root / "data_construction" / "schemas"
    vocabulary_dir = root / "data_construction" / "operator_design"
    bundle_root = root / "data_construction"
    errors: list[str] = []
    warnings: list[str] = []
    schema_paths = [schema_dir / name for name in EXPECTED_SCHEMAS]
    vocabulary_paths = [vocabulary_dir / name for name in EXPECTED_VOCABULARIES]

    loaded_schemas: list[tuple[Path, dict[str, Any]]] = []
    loaded_vocabularies: list[tuple[Path, dict[str, Any]]] = []
    for path in schema_paths + vocabulary_paths:
        if not path.is_file():
            errors.append(f"missing: {path.relative_to(root)}")
            continue
        try:
            value = read_json(path)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"invalid JSON: {path.relative_to(root)}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"expected JSON object: {path.relative_to(root)}")
            continue
        if path in schema_paths:
            loaded_schemas.append((path, value))
            if not isinstance(value.get("$schema"), str):
                errors.append(f"missing $schema: {path.relative_to(root)}")
            root_id = value.get("$id")
            if root_id != path.name:
                errors.append(f"non-portable or mismatched root $id: {path.relative_to(root)}: {root_id!r}")
            for id_path, identifier in nested_ids(value):
                if id_path != "$.$id":
                    errors.append(
                        f"nested $id changes reference base and is unsupported by the portable checker: "
                        f"{path.relative_to(root)}:{id_path}={identifier!r}"
                    )
            for reference in refs(value):
                try:
                    validate_ref(path, reference, bundle_root)
                except (FileNotFoundError, KeyError, IndexError, ValueError) as exc:
                    errors.append(str(exc))
        else:
            loaded_vocabularies.append((path, value))
            schema_ref = value.get("schema_ref")
            if not isinstance(schema_ref, str):
                errors.append(f"missing schema_ref: {path.relative_to(root)}")
            else:
                try:
                    validate_ref(path, schema_ref, bundle_root)
                except (FileNotFoundError, KeyError, IndexError, ValueError) as exc:
                    errors.append(str(exc))
            expected_granularity = path.name.removeprefix("operator_vocabulary_").removesuffix("_v0_1.json")
            if value.get("granularity") != expected_granularity:
                errors.append(f"granularity/file mismatch: {path.relative_to(root)}")
            expected_version = f"operator_vocabulary_{expected_granularity}_v0_1"
            if value.get("vocabulary_version") != expected_version:
                errors.append(f"vocabulary_version/file mismatch: {path.relative_to(root)}")
            operators = value.get("operators")
            if not isinstance(operators, list) or not operators:
                errors.append(f"operators must be a non-empty array: {path.relative_to(root)}")
            else:
                names = [item.get("name") for item in operators if isinstance(item, dict)]
                if len(names) != len(operators) or not all(isinstance(name, str) and name for name in names):
                    errors.append(f"every operator needs a name: {path.relative_to(root)}")
                if len(names) != len(set(names)):
                    errors.append(f"duplicate operator names: {path.relative_to(root)}")

    topology_schema = next(
        (value for path, value in loaded_schemas if path.name == "operator_topology_v0_1.json"),
        None,
    )
    vocabularies_by_granularity = {
        value.get("granularity"): value for _, value in loaded_vocabularies
    }
    if isinstance(topology_schema, dict):
        definitions = topology_schema.get("$defs", {})
        for granularity in ("coarse", "medium", "fine"):
            try:
                schema_names = set(
                    definitions[f"{granularity}_operator_node"]["allOf"][1]["properties"]["operator"]["enum"]
                )
            except (KeyError, IndexError, TypeError):
                errors.append(f"cannot read {granularity} operator enum from operator_topology_v0_1.json")
                continue
            vocabulary = vocabularies_by_granularity.get(granularity)
            vocabulary_names = {
                item.get("name")
                for item in vocabulary.get("operators", [])
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            } if isinstance(vocabulary, dict) else set()
            if schema_names != vocabulary_names:
                errors.append(
                    f"{granularity} operator topology enum and vocabulary names differ: "
                    f"schema_only={sorted(schema_names - vocabulary_names)!r}, "
                    f"vocabulary_only={sorted(vocabulary_names - schema_names)!r}"
                )

    schemas_by_name = {path.name: value for path, value in loaded_schemas}
    binding_enum_paths = {
        "operator_vocabulary_schema_v0_1.json": (
            "$defs",
            "argument_slot",
            "properties",
            "binding_kind",
            "enum",
        ),
        "operator_topology_v0_1.json": (
            "$defs",
            "argument_slot",
            "properties",
            "expected_binding_kind",
            "enum",
        ),
        "grounding_v0_1.json": (
            "$defs",
            "argument_grounding",
            "properties",
            "expected_binding_kind",
            "enum",
        ),
    }
    binding_sets: dict[str, set[str]] = {}
    for schema_name, pointer in binding_enum_paths.items():
        current: Any = schemas_by_name.get(schema_name)
        try:
            for component in pointer:
                current = current[component]
        except (KeyError, TypeError):
            errors.append(f"cannot read binding-kind enum from {schema_name}")
            continue
        if (
            not isinstance(current, list)
            or not current
            or not all(isinstance(item, str) and item for item in current)
            or len(current) != len(set(current))
        ):
            errors.append(f"binding-kind enum is not a unique non-empty string set in {schema_name}")
            continue
        binding_sets[schema_name] = set(current)
    if len(binding_sets) == len(binding_enum_paths):
        canonical_name = "operator_vocabulary_schema_v0_1.json"
        canonical_bindings = binding_sets[canonical_name]
        for schema_name, bindings in binding_sets.items():
            if bindings != canonical_bindings:
                errors.append(
                    f"binding-kind enum drift between {canonical_name} and {schema_name}: "
                    f"canonical_only={sorted(canonical_bindings - bindings)!r}, "
                    f"schema_only={sorted(bindings - canonical_bindings)!r}"
                )

    jsonschema_available = False
    try:
        import jsonschema

        jsonschema_available = True
        for path, schema in loaded_schemas:
            uri = str(schema.get("$schema", ""))
            if "2020-12" in uri and not hasattr(jsonschema, "Draft202012Validator"):
                warnings.append(f"installed jsonschema is too old to meta-validate {path.name}")
                continue
            try:
                validator_class = jsonschema.validators.validator_for(schema)
                validator_class.check_schema(schema)
            except Exception as exc:  # jsonschema exposes draft-specific exception classes
                errors.append(f"schema meta-validation failed: {path.name}: {exc}")
        vocabulary_schema_path = schema_dir / "operator_vocabulary_schema_v0_1.json"
        vocabulary_schema = next(
            (
                schema
                for path, schema in loaded_schemas
                if path.name == "operator_vocabulary_schema_v0_1.json"
            ),
            None,
        )
        if isinstance(vocabulary_schema, dict):
            resolver = jsonschema.RefResolver(
                base_uri=vocabulary_schema_path.resolve().as_uri(),
                referrer=vocabulary_schema,
            )
            if hasattr(jsonschema, "Draft202012Validator"):
                validator = jsonschema.Draft202012Validator(vocabulary_schema, resolver=resolver)
            else:
                # The bundle intentionally avoids draft-specific vocabulary features in this
                # instance schema. Draft 7 is a conservative local structural fallback only;
                # it does not replace the required Draft 2020-12 validation in a pinned env.
                validator = jsonschema.Draft7Validator(vocabulary_schema, resolver=resolver)
                warnings.append(
                    "operator vocabularies were instance-checked with a Draft 7 compatibility fallback"
                )
            for path, vocabulary in loaded_vocabularies:
                for error in validator.iter_errors(vocabulary):
                    location = ".".join(str(part) for part in error.absolute_path) or "$"
                    errors.append(f"vocabulary schema validation failed: {path.name}:{location}: {error.message}")
    except ImportError:
        warnings.append("jsonschema is unavailable; JSON and local $ref checks only")

    if args.require_jsonschema and (not jsonschema_available or any("too old" in warning for warning in warnings)):
        errors.append("--require-jsonschema requested but a compatible validator is unavailable")

    result = {
        "schemas_checked": len(loaded_schemas),
        "vocabularies_expected": len(vocabulary_paths),
        "jsonschema_available": jsonschema_available,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
