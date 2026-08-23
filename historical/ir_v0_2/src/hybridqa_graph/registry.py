"""Read-only access to the JSON registries that define IR v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, Mapping


class RegistryError(ValueError):
    """Raised when a checked-in registry is missing or structurally invalid."""


def _project_root() -> Path:
    # src/hybridqa_graph/registry.py -> project root
    return Path(__file__).resolve().parents[2]


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Cannot load registry {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryError(f"Registry {path} must contain a JSON object")
    return value


@dataclass(frozen=True)
class RegistryBundle:
    """Immutable registry view; JSON files remain the sole definitions."""

    registry_version: str
    ir_version: str
    types: Mapping[str, Mapping[str, Any]]
    coercions: tuple[Any, ...]
    operators: Mapping[str, Mapping[str, Any]]

    def __contains__(self, operator: object) -> bool:
        return operator in self.operators

    def operator(self, name: str) -> Mapping[str, Any] | None:
        return self.operators.get(name)

    def is_type(self, name: object) -> bool:
        return isinstance(name, str) and name in self.types


def load_registries(
    operator_path: str | Path | None = None,
    type_path: str | Path | None = None,
) -> RegistryBundle:
    """Load and sanity-check operator and type registries.

    Custom paths are useful for isolated tests.  The default loader below is
    cached; explicit-path calls are intentionally not cached.
    """

    ir_dir = _project_root() / "ir"
    operator_source = Path(operator_path) if operator_path else ir_dir / "operator_registry_v0_1.json"
    type_source = Path(type_path) if type_path else ir_dir / "type_registry_v0_1.json"
    operator_doc = _load_json(operator_source)
    type_doc = _load_json(type_source)

    for path, document, required in (
        (operator_source, operator_doc, {"registry_version", "ir_version", "operators"}),
        (type_source, type_doc, {"registry_version", "ir_version", "types", "coercions"}),
    ):
        missing = required - document.keys()
        if missing:
            raise RegistryError(f"Registry {path} is missing keys: {sorted(missing)}")

    if operator_doc["registry_version"] != type_doc["registry_version"]:
        raise RegistryError("Operator and type registry versions differ")
    if operator_doc["ir_version"] != type_doc["ir_version"]:
        raise RegistryError("Operator and type registries target different IR versions")
    if not isinstance(operator_doc["operators"], dict) or not isinstance(type_doc["types"], dict):
        raise RegistryError("Registry 'operators' and 'types' fields must be objects")
    if not isinstance(type_doc["coercions"], list):
        raise RegistryError("Type-registry 'coercions' must be an array")

    known_types = set(type_doc["types"])
    for name, operator in operator_doc["operators"].items():
        if not isinstance(name, str) or not isinstance(operator, dict):
            raise RegistryError("Each operator entry must be a named object")
        signatures = operator.get("signatures")
        if not isinstance(signatures, list) or not signatures:
            raise RegistryError(f"Operator {name} has no signatures")
        bindings = operator.get("tool_bindings")
        if not isinstance(bindings, list) or not bindings:
            raise RegistryError(f"Operator {name} has no tool bindings")
        for signature in signatures:
            if not isinstance(signature, dict) or not isinstance(signature.get("inputs"), list):
                raise RegistryError(f"Operator {name} contains a malformed signature")
            referenced: set[str] = set(signature.get("output_types", []))
            for input_spec in signature["inputs"]:
                if not isinstance(input_spec, dict):
                    raise RegistryError(f"Operator {name} contains a malformed input spec")
                referenced.update(input_spec.get("types", []))
            unknown = referenced - known_types
            if unknown:
                raise RegistryError(f"Operator {name} references unknown types: {sorted(unknown)}")

    return RegistryBundle(
        registry_version=str(operator_doc["registry_version"]),
        ir_version=str(operator_doc["ir_version"]),
        types=_deep_freeze(type_doc["types"]),
        coercions=tuple(_deep_freeze(type_doc["coercions"])),
        operators=_deep_freeze(operator_doc["operators"]),
    )


@lru_cache(maxsize=1)
def get_registry() -> RegistryBundle:
    """Return the process-wide immutable default registry bundle."""

    return load_registries()


def get_operator(name: str) -> Mapping[str, Any] | None:
    return get_registry().operator(name)


def iter_operators() -> Iterator[tuple[str, Mapping[str, Any]]]:
    yield from get_registry().operators.items()


__all__ = [
    "RegistryBundle",
    "RegistryError",
    "get_operator",
    "get_registry",
    "iter_operators",
    "load_registries",
]
