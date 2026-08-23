"""Deterministic structural, schema, and type validation for IR v0.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .ir import ExecutionGraph
from .registry import RegistryBundle, get_registry


class ErrorCode:
    """Stable machine-readable codes emitted by :func:`validate_graph`."""

    GRAPH_NOT_OBJECT = "GRAPH_NOT_OBJECT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    UNSUPPORTED_IR_VERSION = "UNSUPPORTED_IR_VERSION"
    EMPTY_NODES = "EMPTY_NODES"
    DUPLICATE_NODE_ID = "DUPLICATE_NODE_ID"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    INVALID_REFERENCE_KIND = "INVALID_REFERENCE_KIND"
    DANGLING_SOURCE_REFERENCE = "DANGLING_SOURCE_REFERENCE"
    DANGLING_NODE_REFERENCE = "DANGLING_NODE_REFERENCE"
    OUTPUT_PORT_MISMATCH = "OUTPUT_PORT_MISMATCH"
    INVALID_ANSWER_REFERENCE = "INVALID_ANSWER_REFERENCE"
    ANSWER_TYPE_NOT_ELIGIBLE = "ANSWER_TYPE_NOT_ELIGIBLE"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    ANSWER_NOT_SOURCE_REACHABLE = "ANSWER_NOT_SOURCE_REACHABLE"
    DEAD_NODE = "DEAD_NODE"
    UNKNOWN_OPERATOR = "UNKNOWN_OPERATOR"
    INPUT_ARITY_MISMATCH = "INPUT_ARITY_MISMATCH"
    INPUT_SIGNATURE_MISMATCH = "INPUT_SIGNATURE_MISMATCH"
    INPUT_TYPE_MISMATCH = "INPUT_TYPE_MISMATCH"
    ARGUMENT_ARITY_MISMATCH = "ARGUMENT_ARITY_MISMATCH"
    MISSING_ARGUMENT = "MISSING_ARGUMENT"
    UNKNOWN_ARGUMENT = "UNKNOWN_ARGUMENT"
    ARGUMENT_TYPE_MISMATCH = "ARGUMENT_TYPE_MISMATCH"
    OUTPUT_TYPE_MISMATCH = "OUTPUT_TYPE_MISMATCH"
    TOOL_BINDING_MISMATCH = "TOOL_BINDING_MISMATCH"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_QUESTION_REF = "INVALID_QUESTION_REF"
    INVALID_SOURCE_LOCATOR = "INVALID_SOURCE_LOCATOR"
    TABLE_ID_MISMATCH = "TABLE_ID_MISMATCH"
    INVALID_COLUMN_REFERENCE = "INVALID_COLUMN_REFERENCE"
    SCHEMA_COLUMN_INDEX_OUT_OF_RANGE = "SCHEMA_COLUMN_INDEX_OUT_OF_RANGE"
    SCHEMA_COLUMN_LABEL_MISMATCH = "SCHEMA_COLUMN_LABEL_MISMATCH"


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str
    node_id: str | None = None
    path: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.node_id is not None:
            result["node_id"] = self.node_id
        if self.path is not None:
            result["path"] = self.path
        if self.details:
            result["details"] = dict(self.details)
        return result


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[ValidationError, ...] = ()
    warnings: tuple[ValidationError, ...] = ()
    topological_order: tuple[str, ...] = ()
    inferred_types: Mapping[str, str] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def error_codes(self) -> tuple[str, ...]:
        return tuple(error.code for error in self.errors)

    @property
    def warning_codes(self) -> tuple[str, ...]:
        return tuple(warning.code for warning in self.warnings)

    def has_error(self, code: str) -> bool:
        return any(error.code == code for error in self.errors)

    def has_warning(self, code: str) -> bool:
        return any(warning.code == code for warning in self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "topological_order": list(self.topological_order),
            "inferred_types": dict(self.inferred_types),
        }

    def __bool__(self) -> bool:
        return self.valid


class _Collector:
    def __init__(self) -> None:
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self._seen: set[tuple[str, str, str | None, str | None, str]] = set()

    def add(
        self,
        code: str,
        message: str,
        *,
        node_id: str | None = None,
        path: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        key = ("error", code, node_id, path, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self.errors.append(
            ValidationError(
                code=code,
                message=message,
                node_id=node_id,
                path=path,
                details={} if details is None else dict(details),
            )
        )

    def warn(
        self,
        code: str,
        message: str,
        *,
        node_id: str | None = None,
        path: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        key = ("warning", code, node_id, path, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self.warnings.append(
            ValidationError(
                code=code,
                message=message,
                node_id=node_id,
                path=path,
                details={} if details is None else dict(details),
            )
        )

    @staticmethod
    def _ordered(items: Iterable[ValidationError]) -> tuple[ValidationError, ...]:
        return tuple(sorted(
            items,
            key=lambda error: (
                error.path or "",
                error.node_id or "",
                error.code,
                error.message,
            ),
        ))

    def report(
        self,
        *,
        topological_order: Iterable[str] = (),
        inferred_types: Mapping[str, str] | None = None,
    ) -> ValidationReport:
        # Sorting makes reports stable even when callers construct source/input
        # maps in a different insertion order.
        return ValidationReport(
            errors=self._ordered(self.errors),
            warnings=self._ordered(self.warnings),
            topological_order=tuple(topological_order),
            inferred_types={} if inferred_types is None else dict(sorted(inferred_types.items())),
        )


_TOP_LEVEL_FIELDS = (
    "ir_version",
    "graph_id",
    "question_ref",
    "schema_ref",
    "sources",
    "nodes",
    "answer",
)
_NODE_FIELDS = (
    "id",
    "operator",
    "inputs",
    "arguments",
    "output",
    "tool_binding",
    "provenance",
)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _missing_fields(
    value: Mapping[str, Any],
    fields: Iterable[str],
    collector: _Collector,
    *,
    path: str,
    node_id: str | None = None,
) -> None:
    for name in fields:
        if name not in value:
            collector.add(
                ErrorCode.MISSING_FIELD,
                f"Required field {name!r} is missing",
                node_id=node_id,
                path=f"{path}.{name}" if path else name,
                details={"field": name},
            )


def _graph_mapping(graph: Any) -> Mapping[str, Any] | None:
    if isinstance(graph, ExecutionGraph):
        return graph.to_dict()
    if isinstance(graph, Mapping):
        return graph
    return None


def _schema_columns(
    schema: Any,
    collector: _Collector,
    *,
    explicit: bool,
) -> dict[int, str] | None:
    """Normalize supported schemas to index -> label.

    Canonical JSON uses ``{"columns": [{"index": 0, "label": "..."}]}``.
    A sequence of labels and ``HybridTable.column_names`` are accepted as API
    conveniences, but graph serialization remains canonical.
    """

    if schema is None:
        return None
    if hasattr(schema, "column_names") and not isinstance(schema, Mapping):
        schema = list(schema.column_names)

    raw_columns: Any
    if isinstance(schema, Mapping):
        if "columns" not in schema:
            if explicit:
                collector.add(
                    ErrorCode.INVALID_SCHEMA,
                    "An explicit schema must contain a 'columns' array",
                    path="schema.columns",
                )
            return None
        raw_columns = schema.get("columns")
    elif isinstance(schema, Sequence) and not isinstance(schema, (str, bytes, bytearray)):
        raw_columns = schema
    else:
        collector.add(
            ErrorCode.INVALID_SCHEMA,
            "Schema must be an object with columns, a label sequence, or expose column_names",
            path="schema",
        )
        return None

    if not isinstance(raw_columns, Sequence) or isinstance(raw_columns, (str, bytes, bytearray)):
        collector.add(
            ErrorCode.INVALID_SCHEMA,
            "Schema 'columns' must be an array",
            path="schema.columns",
        )
        return None

    result: dict[int, str] = {}
    for position, column in enumerate(raw_columns):
        path = f"schema.columns[{position}]"
        if isinstance(column, str):
            index, label = position, column
        elif isinstance(column, Mapping):
            if "index" not in column or "label" not in column:
                collector.add(
                    ErrorCode.INVALID_SCHEMA,
                    "Every schema column requires integer 'index' and string 'label'",
                    path=path,
                )
                continue
            index, label = column.get("index"), column.get("label")
        else:
            collector.add(
                ErrorCode.INVALID_SCHEMA,
                "Every schema column must be a label or an index/label object",
                path=path,
            )
            continue
        # Empty HybridQA header cells are real schema labels.  They remain
        # distinguishable from a missing or non-string label by the index.
        if not _is_integer(index) or index < 0 or not isinstance(label, str):
            collector.add(
                ErrorCode.INVALID_SCHEMA,
                "Schema column index must be non-negative and label must be a string",
                path=path,
            )
            continue
        if index in result:
            collector.add(
                ErrorCode.INVALID_SCHEMA,
                f"Duplicate schema column index {index}",
                path=path,
                details={"index": index},
            )
            continue
        result[index] = label
    return result


def _validate_column_ref(
    value: Any,
    schema_columns: Mapping[int, str] | None,
    collector: _Collector,
    *,
    node_id: str,
    path: str,
) -> None:
    if not isinstance(value, Mapping):
        collector.add(
            ErrorCode.INVALID_COLUMN_REFERENCE,
            "A column reference must be an object with 'index' and 'label'",
            node_id=node_id,
            path=path,
        )
        return
    if "index" not in value or "label" not in value:
        collector.add(
            ErrorCode.INVALID_COLUMN_REFERENCE,
            "A column reference requires both 'index' and 'label'",
            node_id=node_id,
            path=path,
        )
        return
    index, label = value.get("index"), value.get("label")
    if not _is_integer(index) or index < 0 or not isinstance(label, str):
        collector.add(
            ErrorCode.INVALID_COLUMN_REFERENCE,
            "Column index must be a non-negative integer and label a string",
            node_id=node_id,
            path=path,
        )
        return
    extra = set(value) - {"index", "label"}
    if extra:
        collector.add(
            ErrorCode.INVALID_COLUMN_REFERENCE,
            f"Unknown column-reference fields: {sorted(extra)}",
            node_id=node_id,
            path=path,
            details={"fields": sorted(extra)},
        )
    if schema_columns is None:
        return
    if index not in schema_columns:
        collector.add(
            ErrorCode.SCHEMA_COLUMN_INDEX_OUT_OF_RANGE,
            f"Column index {index} is not present in the supplied schema",
            node_id=node_id,
            path=path,
            details={"index": index},
        )
        return
    expected = schema_columns[index]
    if label != expected:
        collector.add(
            ErrorCode.SCHEMA_COLUMN_LABEL_MISMATCH,
            f"Column {index} is labelled {expected!r}, not {label!r}",
            node_id=node_id,
            path=path,
            details={"index": index, "expected": expected, "actual": label},
        )


def _validate_argument_value(
    value: Any,
    schema: Mapping[str, Any],
    schema_columns: Mapping[int, str] | None,
    registry: RegistryBundle,
    collector: _Collector,
    *,
    node_id: str,
    path: str,
) -> None:
    kind = schema.get("kind")
    if kind == "any":
        return
    if kind == "column_ref":
        _validate_column_ref(value, schema_columns, collector, node_id=node_id, path=path)
        return
    if kind == "one_of":
        alternatives = schema.get("schemas", ())
        # Column-ref versus string is the only current one_of.  Choose using
        # shape so errors remain specific and schema-grounding is not skipped.
        if isinstance(value, Mapping):
            for alternative in alternatives:
                if alternative.get("kind") == "column_ref":
                    _validate_argument_value(
                        value,
                        alternative,
                        schema_columns,
                        registry,
                        collector,
                        node_id=node_id,
                        path=path,
                    )
                    return
        for alternative in alternatives:
            if alternative.get("kind") == "nonempty_string" and _is_nonempty_string(value):
                return
        collector.add(
            ErrorCode.ARGUMENT_TYPE_MISMATCH,
            "Argument does not match any permitted shape",
            node_id=node_id,
            path=path,
        )
        return

    valid = True
    expectation = kind or "declared schema"
    if kind == "nonempty_string":
        valid = _is_nonempty_string(value)
    elif kind == "boolean":
        valid = isinstance(value, bool)
    elif kind == "integer":
        valid = _is_integer(value) and value >= schema.get("minimum", value)
    elif kind == "enum":
        valid = value in schema.get("values", ())
        expectation = f"one of {list(schema.get('values', ()))}"
    elif kind == "type_name":
        valid = registry.is_type(value)
        expectation = "a registered type name"
    elif kind == "array":
        valid = isinstance(value, list)
        if valid:
            item_schema = schema.get("items", {"kind": "any"})
            for index, item in enumerate(value):
                _validate_argument_value(
                    item,
                    item_schema,
                    schema_columns,
                    registry,
                    collector,
                    node_id=node_id,
                    path=f"{path}[{index}]",
                )
    elif kind == "object":
        valid = isinstance(value, Mapping)
        if valid:
            required = set(schema.get("required", ()))
            optional = set(schema.get("optional", ()))
            properties = schema.get("properties", {})
            missing = required - set(value)
            if missing:
                collector.add(
                    ErrorCode.ARGUMENT_TYPE_MISMATCH,
                    f"Object argument is missing fields: {sorted(missing)}",
                    node_id=node_id,
                    path=path,
                    details={"missing": sorted(missing)},
                )
            if not schema.get("allow_additional", True):
                extra = set(value) - required - optional
                if extra:
                    collector.add(
                        ErrorCode.ARGUMENT_TYPE_MISMATCH,
                        f"Object argument has unknown fields: {sorted(extra)}",
                        node_id=node_id,
                        path=path,
                        details={"unknown": sorted(extra)},
                    )
            for name in sorted(set(value) & set(properties)):
                _validate_argument_value(
                    value[name],
                    properties[name],
                    schema_columns,
                    registry,
                    collector,
                    node_id=node_id,
                    path=f"{path}.{name}",
                )
            for condition in schema.get("conditional_requirements", ()):
                if not isinstance(condition, Mapping):
                    continue
                expected = condition.get("if", {})
                if not isinstance(expected, Mapping):
                    continue
                matches = all(
                    (
                        value.get(name) in expected_value
                        if isinstance(expected_value, (list, tuple))
                        else value.get(name) == expected_value
                    )
                    for name, expected_value in expected.items()
                )
                if not matches:
                    continue
                conditional_missing = sorted(set(condition.get("require", ())) - set(value))
                conditional_forbidden = sorted(set(condition.get("forbid", ())) & set(value))
                if conditional_missing or conditional_forbidden:
                    collector.add(
                        ErrorCode.ARGUMENT_TYPE_MISMATCH,
                        "Object argument violates a conditional requirement",
                        node_id=node_id,
                        path=path,
                        details={
                            "condition": dict(expected),
                            "missing": conditional_missing,
                            "forbidden": conditional_forbidden,
                        },
                    )
    else:
        valid = False
        expectation = f"known argument schema (registry contained {kind!r})"

    if not valid:
        collector.add(
            ErrorCode.ARGUMENT_TYPE_MISMATCH,
            f"Argument must be {expectation}",
            node_id=node_id,
            path=path,
            details={"expected": expectation, "actual_type": type(value).__name__},
        )


def _reference(
    value: Any,
    collector: _Collector,
    *,
    node_id: str | None,
    path: str,
) -> tuple[str, str, str | None] | None:
    if not isinstance(value, Mapping):
        collector.add(
            ErrorCode.INVALID_REFERENCE,
            "A reference must be an object",
            node_id=node_id,
            path=path,
        )
        return None
    kind = value.get("kind")
    if kind == "source":
        source_id = value.get("source_id")
        if not _is_nonempty_string(source_id):
            collector.add(
                ErrorCode.INVALID_REFERENCE,
                "A source reference requires a non-empty 'source_id'",
                node_id=node_id,
                path=path,
            )
            return None
        return "source", source_id, None
    if kind == "node":
        target, port = value.get("node_id"), value.get("port")
        if not _is_nonempty_string(target) or not _is_nonempty_string(port):
            collector.add(
                ErrorCode.INVALID_REFERENCE,
                "A node reference requires non-empty 'node_id' and 'port'",
                node_id=node_id,
                path=path,
            )
            return None
        return "node", target, port
    collector.add(
        ErrorCode.INVALID_REFERENCE_KIND,
        f"Reference kind must be 'source' or 'node', not {kind!r}",
        node_id=node_id,
        path=path,
    )
    return None


def _cyclic_components(adjacency: Mapping[str, set[str]]) -> list[list[str]]:
    """Return deterministic cyclic strongly connected components."""

    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for dependency in sorted(adjacency.get(node, ())):
            if dependency not in adjacency:
                continue
            if dependency not in indices:
                visit(dependency)
                lowlinks[node] = min(lowlinks[node], lowlinks[dependency])
            elif dependency in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[dependency])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node:
                    break
            component.sort()
            if len(component) > 1 or node in adjacency.get(node, set()):
                components.append(component)

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)
    return sorted(components)


def _topological_order(adjacency: Mapping[str, set[str]]) -> tuple[str, ...]:
    """Return dependency-first order; cyclic nodes are omitted deterministically."""

    dependency_count = {
        node: sum(dependency in adjacency for dependency in dependencies)
        for node, dependencies in adjacency.items()
    }
    dependents: dict[str, set[str]] = {node: set() for node in adjacency}
    for node, dependencies in adjacency.items():
        for dependency in dependencies:
            if dependency in dependents:
                dependents[dependency].add(node)

    ready = sorted(node for node, count in dependency_count.items() if count == 0)
    result: list[str] = []
    while ready:
        current = ready.pop(0)
        result.append(current)
        for dependent in sorted(dependents[current]):
            dependency_count[dependent] -= 1
            if dependency_count[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    return tuple(result)


def _signature_inputs(signature: Mapping[str, Any]) -> dict[str, set[str]]:
    return {
        item["name"]: set(item.get("types", ()))
        for item in signature.get("inputs", ())
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }


def _validate_operator_node(
    node: Mapping[str, Any],
    node_id: str,
    path: str,
    input_types: Mapping[str, str | None],
    schema_columns: Mapping[int, str] | None,
    registry: RegistryBundle,
    collector: _Collector,
) -> None:
    operator_name = node.get("operator")
    if not _is_nonempty_string(operator_name):
        if "operator" in node:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "Node operator must be a non-empty string",
                node_id=node_id,
                path=f"{path}.operator",
            )
        return
    operator = registry.operator(operator_name)
    if operator is None:
        collector.add(
            ErrorCode.UNKNOWN_OPERATOR,
            f"Operator {operator_name!r} is not registered",
            node_id=node_id,
            path=f"{path}.operator",
            details={"operator": operator_name},
        )
        return

    signatures = list(operator.get("signatures", ()))
    actual_names = set(input_types)
    exact_name_signatures = [
        signature
        for signature in signatures
        if set(_signature_inputs(signature)) == actual_names
    ]
    if not exact_name_signatures:
        expected_counts = sorted({len(_signature_inputs(signature)) for signature in signatures})
        if len(actual_names) not in expected_counts:
            collector.add(
                ErrorCode.INPUT_ARITY_MISMATCH,
                f"{operator_name} received {len(actual_names)} inputs; expected {expected_counts}",
                node_id=node_id,
                path=f"{path}.inputs",
                details={"actual": len(actual_names), "expected": expected_counts},
            )
        else:
            expected = [sorted(_signature_inputs(signature)) for signature in signatures]
            collector.add(
                ErrorCode.INPUT_SIGNATURE_MISMATCH,
                f"{operator_name} input roles {sorted(actual_names)} do not match {expected}",
                node_id=node_id,
                path=f"{path}.inputs",
                details={"actual": sorted(actual_names), "expected": expected},
            )

    type_candidates = exact_name_signatures
    compatible: list[Mapping[str, Any]] = []
    if type_candidates:
        for signature in type_candidates:
            expected = _signature_inputs(signature)
            matches = all(
                input_types[name] is None or input_types[name] in accepted
                for name, accepted in expected.items()
            )
            same_names = signature.get("same_type_inputs", ())
            if same_names and all(name in input_types for name in same_names):
                known = {input_types[name] for name in same_names if input_types[name] is not None}
                matches = matches and len(known) <= 1
            if matches:
                compatible.append(signature)
        if not compatible:
            # Select the closest signature for compact, role-specific errors.
            def mismatch_count(signature: Mapping[str, Any]) -> int:
                expected = _signature_inputs(signature)
                return sum(
                    input_types[name] is not None and input_types[name] not in accepted
                    for name, accepted in expected.items()
                )

            closest = min(type_candidates, key=mismatch_count)
            expected = _signature_inputs(closest)
            for name in sorted(expected):
                actual = input_types[name]
                if actual is not None and actual not in expected[name]:
                    collector.add(
                        ErrorCode.INPUT_TYPE_MISMATCH,
                        f"Input {name!r} has type {actual}; expected one of {sorted(expected[name])}",
                        node_id=node_id,
                        path=f"{path}.inputs.{name}",
                        details={"input": name, "actual": actual, "expected": sorted(expected[name])},
                    )
            same_names = closest.get("same_type_inputs", ())
            known = {input_types[name] for name in same_names if input_types.get(name) is not None}
            if len(known) > 1:
                collector.add(
                    ErrorCode.INPUT_TYPE_MISMATCH,
                    f"Inputs {list(same_names)} must have exactly the same declared type",
                    node_id=node_id,
                    path=f"{path}.inputs",
                    details={"inputs": list(same_names), "actual_types": sorted(known)},
                )

    arguments = node.get("arguments")
    if not isinstance(arguments, Mapping):
        if "arguments" in node:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "Node arguments must be an object",
                node_id=node_id,
                path=f"{path}.arguments",
            )
        arguments = {}

    argument_candidates = compatible or exact_name_signatures or signatures
    if argument_candidates:
        def argument_cost(signature: Mapping[str, Any]) -> tuple[int, int]:
            required = set(signature.get("required_arguments", ()))
            allowed = required | set(signature.get("optional_arguments", ()))
            return len(required - set(arguments)), len(set(arguments) - allowed)

        best = min(argument_candidates, key=argument_cost)
        required = set(best.get("required_arguments", ()))
        allowed = required | set(best.get("optional_arguments", ()))
        missing = sorted(required - set(arguments))
        unknown = sorted(set(arguments) - allowed)
        if missing or unknown:
            collector.add(
                ErrorCode.ARGUMENT_ARITY_MISMATCH,
                f"{operator_name} arguments are missing {missing} and have unknown fields {unknown}",
                node_id=node_id,
                path=f"{path}.arguments",
                details={"missing": missing, "unknown": unknown},
            )
        for name in missing:
            collector.add(
                ErrorCode.MISSING_ARGUMENT,
                f"Required argument {name!r} is missing",
                node_id=node_id,
                path=f"{path}.arguments.{name}",
                details={"argument": name},
            )
        for name in unknown:
            collector.add(
                ErrorCode.UNKNOWN_ARGUMENT,
                f"Argument {name!r} is not permitted for {operator_name}",
                node_id=node_id,
                path=f"{path}.arguments.{name}",
                details={"argument": name},
            )
        for name, domain in best.get("argument_domains", {}).items():
            if name in arguments and arguments[name] not in domain:
                collector.add(
                    ErrorCode.ARGUMENT_TYPE_MISMATCH,
                    f"Argument {name!r} is not valid for signature {best.get('id')!r}",
                    node_id=node_id,
                    path=f"{path}.arguments.{name}",
                    details={"actual": arguments[name], "expected": list(domain)},
                )

    argument_schemas = operator.get("argument_schemas", {})
    for name in sorted(set(arguments) & set(argument_schemas)):
        _validate_argument_value(
            arguments[name],
            argument_schemas[name],
            schema_columns,
            registry,
            collector,
            node_id=node_id,
            path=f"{path}.arguments.{name}",
        )

    output = node.get("output")
    output_type = output.get("type") if isinstance(output, Mapping) else None
    output_candidates = compatible or exact_name_signatures or signatures
    if isinstance(output_type, str) and output_candidates:
        allowed_outputs = set().union(
            *(set(signature.get("output_types", ())) for signature in output_candidates)
        )
        if output_type not in allowed_outputs:
            collector.add(
                ErrorCode.OUTPUT_TYPE_MISMATCH,
                f"{operator_name} cannot declare output type {output_type}; expected {sorted(allowed_outputs)}",
                node_id=node_id,
                path=f"{path}.output.type",
                details={"actual": output_type, "expected": sorted(allowed_outputs)},
            )
        for signature in output_candidates:
            same_as = signature.get("output_same_as_input")
            if same_as and input_types.get(same_as) is not None and output_type != input_types[same_as]:
                collector.add(
                    ErrorCode.OUTPUT_TYPE_MISMATCH,
                    f"{operator_name} output must retain input {same_as!r} type {input_types[same_as]}",
                    node_id=node_id,
                    path=f"{path}.output.type",
                    details={"actual": output_type, "expected": input_types[same_as]},
                )
                break
        type_argument = operator.get("output_type_argument")
        collection_outputs = set(operator.get("collection_output_types", ()))
        if type_argument in arguments:
            expected_output = arguments[type_argument]
            if registry.is_type(expected_output) and output_type not in collection_outputs and output_type != expected_output:
                collector.add(
                    ErrorCode.OUTPUT_TYPE_MISMATCH,
                    f"Output type {output_type} disagrees with argument {type_argument}={expected_output}",
                    node_id=node_id,
                    path=f"{path}.output.type",
                    details={"actual": output_type, "expected": expected_output},
                )

        # IR v0.2 registries may add argument-dependent output rules.  These
        # rules stay in the machine-readable registry so constrained planners
        # and post-hoc validation share one contract.
        matched_signature_ids = {
            signature.get("id") for signature in (compatible or exact_name_signatures)
        }
        for rule in operator.get("output_rules", ()):
            if not isinstance(rule, Mapping):
                continue
            conditions = rule.get("when_arguments", {})
            if not isinstance(conditions, Mapping) or not all(
                (
                    arguments.get(name) in expected
                    if isinstance(expected, (list, tuple))
                    else arguments.get(name) == expected
                )
                for name, expected in conditions.items()
            ):
                continue
            signature_condition = rule.get("when_signature")
            if signature_condition is not None:
                expected_signatures = (
                    set(signature_condition)
                    if isinstance(signature_condition, list)
                    else {signature_condition}
                )
                if not (matched_signature_ids & expected_signatures):
                    continue
            permitted = set(rule.get("output_types", ()))
            if isinstance(rule.get("output_type"), str):
                permitted.add(rule["output_type"])
            from_argument = rule.get("output_type_from_argument")
            if isinstance(from_argument, str) and isinstance(arguments.get(from_argument), str):
                permitted.add(arguments[from_argument])
            if permitted and output_type not in permitted:
                collector.add(
                    ErrorCode.OUTPUT_TYPE_MISMATCH,
                    f"{operator_name} arguments {dict(conditions)} require output in {sorted(permitted)}",
                    node_id=node_id,
                    path=f"{path}.output.type",
                    details={"actual": output_type, "expected": sorted(permitted)},
                )

    binding = node.get("tool_binding")
    allowed_bindings = set(operator.get("tool_bindings", ()))
    if binding is not None and binding not in allowed_bindings:
        collector.add(
            ErrorCode.TOOL_BINDING_MISMATCH,
            f"Tool binding {binding!r} is not valid for {operator_name}; expected {sorted(allowed_bindings)}",
            node_id=node_id,
            path=f"{path}.tool_binding",
            details={"actual": binding, "expected": sorted(allowed_bindings)},
        )


def validate_graph(
    graph: Any,
    schema: Any = None,
    *,
    registry: RegistryBundle | None = None,
    generated_plan: bool = False,
) -> ValidationReport:
    """Validate an execution graph without mutating it or applying coercions.

    All independent errors are accumulated in a deterministic report.  The
    optional ``schema`` takes precedence over ``graph['schema_ref']`` for
    column index/label checks.
    """

    collector = _Collector()
    raw = _graph_mapping(graph)
    if raw is None:
        collector.add(
            ErrorCode.GRAPH_NOT_OBJECT,
            "Graph must be a mapping or ExecutionGraph",
            path="$",
        )
        return collector.report()

    registry = registry or get_registry()
    _missing_fields(raw, _TOP_LEVEL_FIELDS, collector, path="")
    version = raw.get("ir_version")
    if version is not None and version != registry.ir_version:
        collector.add(
            ErrorCode.UNSUPPORTED_IR_VERSION,
            f"IR version {version!r} is unsupported; expected {registry.ir_version!r}",
            path="ir_version",
            details={"actual": version, "expected": registry.ir_version},
        )
    if generated_plan:
        extra_top_level = sorted(set(raw) - set(_TOP_LEVEL_FIELDS))
        if extra_top_level:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                f"Generated plan has unknown top-level fields {extra_top_level}",
                path="$",
                details={"unknown": extra_top_level},
            )
        question_ref_value = raw.get("question_ref")
        if isinstance(question_ref_value, Mapping) and "answer" in question_ref_value:
            collector.add(
                ErrorCode.INVALID_QUESTION_REF,
                "Generated plans must not contain a benchmark answer",
                path="question_ref.answer",
            )
        for index, node_value in enumerate(raw.get("nodes", ()) if isinstance(raw.get("nodes"), list) else ()):
            if not isinstance(node_value, Mapping):
                continue
            node_id_value = node_value.get("id") if _is_nonempty_string(node_value.get("id")) else None
            for forbidden in ("provenance", "status", "execution"):
                if forbidden in node_value:
                    collector.add(
                        ErrorCode.INVALID_FIELD_TYPE,
                        f"Generated plan nodes must not contain {forbidden!r}",
                        node_id=node_id_value,
                        path=f"nodes[{index}].{forbidden}",
                    )
            allowed_node_fields = set(_NODE_FIELDS) - {"provenance"}
            extra_node_fields = sorted(set(node_value) - allowed_node_fields)
            if extra_node_fields:
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    f"Generated plan node has unknown fields {extra_node_fields}",
                    node_id=node_id_value,
                    path=f"nodes[{index}]",
                    details={"unknown": extra_node_fields},
                )
    for name in ("graph_id",):
        if name in raw and not _is_nonempty_string(raw[name]):
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                f"{name} must be a non-empty string",
                path=name,
            )
    for name in ("question_ref", "schema_ref"):
        if name in raw and not isinstance(raw[name], Mapping):
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                f"{name} must be an object",
                path=name,
            )

    question_ref = raw.get("question_ref")
    question_table_id: str | None = None
    if isinstance(question_ref, Mapping):
        required_question_fields = {"split", "question_id", "table_id", "question"}
        missing_question = sorted(required_question_fields - set(question_ref))
        if missing_question:
            collector.add(
                ErrorCode.INVALID_QUESTION_REF,
                f"question_ref is missing fields {missing_question}",
                path="question_ref",
                details={"missing": missing_question},
            )
        for field_name in sorted(required_question_fields & set(question_ref)):
            if not _is_nonempty_string(question_ref[field_name]):
                collector.add(
                    ErrorCode.INVALID_QUESTION_REF,
                    f"question_ref.{field_name} must be a non-empty string",
                    path=f"question_ref.{field_name}",
                )
        if _is_nonempty_string(question_ref.get("table_id")):
            question_table_id = str(question_ref["table_id"])

    schema_ref = raw.get("schema_ref")
    schema_table_id: str | None = None
    if isinstance(schema_ref, Mapping):
        if not _is_nonempty_string(schema_ref.get("table_id")):
            collector.add(
                ErrorCode.INVALID_SCHEMA,
                "schema_ref requires a non-empty table_id",
                path="schema_ref.table_id",
            )
        else:
            schema_table_id = str(schema_ref["table_id"])
            if question_table_id is not None and schema_table_id != question_table_id:
                collector.add(
                    ErrorCode.TABLE_ID_MISMATCH,
                    "schema_ref.table_id does not match question_ref.table_id",
                    path="schema_ref.table_id",
                    details={"question": question_table_id, "schema": schema_table_id},
                )

    schema_source = schema if schema is not None else raw.get("schema_ref")
    schema_columns = _schema_columns(
        schema_source,
        collector,
        explicit=schema is not None,
    )

    sources_raw = raw.get("sources", {})
    sources: dict[str, Mapping[str, Any]] = {}
    source_types: dict[str, str | None] = {}
    if not isinstance(sources_raw, Mapping):
        if "sources" in raw:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "sources must be an object keyed by source ID",
                path="sources",
            )
    else:
        for source_id in sorted(sources_raw, key=str):
            value = sources_raw[source_id]
            path = f"sources.{source_id}"
            if not _is_nonempty_string(source_id) or not isinstance(value, Mapping):
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    "Each source ID must be non-empty and each source must be an object",
                    path=path,
                )
                continue
            sources[source_id] = value
            _missing_fields(value, ("type", "locator"), collector, path=path)
            source_type = value.get("type")
            source_types[source_id] = source_type if isinstance(source_type, str) else None
            if source_type is not None and not registry.is_type(source_type):
                collector.add(
                    ErrorCode.UNKNOWN_TYPE,
                    f"Source type {source_type!r} is not registered",
                    path=f"{path}.type",
                    details={"type": source_type},
                )
            if "locator" in value and not isinstance(value.get("locator"), Mapping):
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    "Source locator must be an object",
                    path=f"{path}.locator",
                )
            locator = value.get("locator")
            if isinstance(locator, Mapping):
                locator_kind = locator.get("kind")
                locator_table_id = locator.get("table_id")
                if locator_kind != "hybridqa_table" or not _is_nonempty_string(locator_table_id):
                    collector.add(
                        ErrorCode.INVALID_SOURCE_LOCATOR,
                        "A Week 2 table source locator requires kind='hybridqa_table' and a non-empty table_id",
                        path=f"{path}.locator",
                    )
                elif question_table_id is not None and locator_table_id != question_table_id:
                    collector.add(
                        ErrorCode.TABLE_ID_MISMATCH,
                        "Source locator table_id does not match question_ref.table_id",
                        path=f"{path}.locator.table_id",
                        details={"question": question_table_id, "source": locator_table_id},
                    )

    nodes_raw = raw.get("nodes", [])
    nodes: list[tuple[int, Mapping[str, Any], str | None]] = []
    node_by_id: dict[str, Mapping[str, Any]] = {}
    node_path_by_id: dict[str, str] = {}
    output_types: dict[str, str | None] = {}
    output_ports: dict[str, str | None] = {}
    if not isinstance(nodes_raw, list):
        if "nodes" in raw:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "nodes must be an array",
                path="nodes",
            )
        nodes_raw = []
    if "nodes" in raw and isinstance(nodes_raw, list) and not nodes_raw:
        collector.add(ErrorCode.EMPTY_NODES, "Graph must contain at least one node", path="nodes")

    for index, value in enumerate(nodes_raw):
        path = f"nodes[{index}]"
        if not isinstance(value, Mapping):
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "Every node must be an object",
                path=path,
            )
            continue
        raw_id = value.get("id")
        node_id = raw_id if _is_nonempty_string(raw_id) else None
        nodes.append((index, value, node_id))
        required_node_fields = (
            tuple(field for field in _NODE_FIELDS if field != "provenance")
            if generated_plan
            else _NODE_FIELDS
        )
        _missing_fields(value, required_node_fields, collector, path=path, node_id=node_id)
        if "id" in value and node_id is None:
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "Node ID must be a non-empty string",
                path=f"{path}.id",
            )
        if node_id is not None:
            if node_id in node_by_id:
                collector.add(
                    ErrorCode.DUPLICATE_NODE_ID,
                    f"Node ID {node_id!r} occurs more than once",
                    node_id=node_id,
                    path=f"{path}.id",
                    details={"node_id": node_id},
                )
            else:
                node_by_id[node_id] = value
                node_path_by_id[node_id] = path
        for object_field in ("inputs", "arguments", "output", "provenance"):
            if object_field in value and not isinstance(value.get(object_field), Mapping):
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    f"Node {object_field} must be an object",
                    node_id=node_id,
                    path=f"{path}.{object_field}",
                )
        output = value.get("output")
        if isinstance(output, Mapping):
            _missing_fields(output, ("port", "type"), collector, path=f"{path}.output", node_id=node_id)
            port, output_type = output.get("port"), output.get("type")
            if "port" in output and not _is_nonempty_string(port):
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    "Output port must be a non-empty string",
                    node_id=node_id,
                    path=f"{path}.output.port",
                )
            if "type" in output and not registry.is_type(output_type):
                collector.add(
                    ErrorCode.UNKNOWN_TYPE,
                    f"Output type {output_type!r} is not registered",
                    node_id=node_id,
                    path=f"{path}.output.type",
                    details={"type": output_type},
                )
            if node_id is not None and node_id not in output_types:
                output_types[node_id] = output_type if isinstance(output_type, str) else None
                output_ports[node_id] = port if isinstance(port, str) else None
        if "tool_binding" in value and not _is_nonempty_string(value.get("tool_binding")):
            collector.add(
                ErrorCode.INVALID_FIELD_TYPE,
                "tool_binding must be a non-empty string",
                node_id=node_id,
                path=f"{path}.tool_binding",
            )

    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_by_id}
    source_inputs_by_node: dict[str, set[str]] = {node_id: set() for node_id in node_by_id}
    input_types_by_node: dict[str, dict[str, str | None]] = {}
    for index, node, node_id in nodes:
        path = f"nodes[{index}]"
        inputs_raw = node.get("inputs")
        if not isinstance(inputs_raw, Mapping):
            continue
        input_types: dict[str, str | None] = {}
        for role in sorted(inputs_raw, key=str):
            ref_path = f"{path}.inputs.{role}"
            if not _is_nonempty_string(role):
                collector.add(
                    ErrorCode.INVALID_FIELD_TYPE,
                    "Input role names must be non-empty strings",
                    node_id=node_id,
                    path=ref_path,
                )
                continue
            parsed = _reference(inputs_raw[role], collector, node_id=node_id, path=ref_path)
            input_types[role] = None
            if parsed is None:
                continue
            kind, target, port = parsed
            if kind == "source":
                if target not in sources:
                    collector.add(
                        ErrorCode.DANGLING_SOURCE_REFERENCE,
                        f"Input refers to unknown source {target!r}",
                        node_id=node_id,
                        path=ref_path,
                        details={"source_id": target},
                    )
                else:
                    input_types[role] = source_types.get(target)
                    if node_id in source_inputs_by_node:
                        source_inputs_by_node[node_id].add(target)
            else:
                if target not in node_by_id:
                    collector.add(
                        ErrorCode.DANGLING_NODE_REFERENCE,
                        f"Input refers to unknown node {target!r}",
                        node_id=node_id,
                        path=ref_path,
                        details={"node_id": target},
                    )
                else:
                    expected_port = output_ports.get(target)
                    if expected_port is not None and port != expected_port:
                        collector.add(
                            ErrorCode.OUTPUT_PORT_MISMATCH,
                            f"Node {target!r} exposes port {expected_port!r}, not {port!r}",
                            node_id=node_id,
                            path=ref_path,
                            details={"target": target, "actual": port, "expected": expected_port},
                        )
                    else:
                        input_types[role] = output_types.get(target)
                    if node_id in adjacency:
                        adjacency[node_id].add(target)
        if node_id is not None:
            input_types_by_node[node_id] = input_types

    for index, node, node_id in nodes:
        if node_id is None:
            continue
        _validate_operator_node(
            node,
            node_id,
            f"nodes[{index}]",
            input_types_by_node.get(node_id, {}),
            schema_columns,
            registry,
            collector,
        )

    for component in _cyclic_components(adjacency):
        collector.add(
            ErrorCode.CYCLE_DETECTED,
            f"Data-dependency cycle detected among nodes {component}",
            node_id=component[0],
            path="nodes",
            details={"nodes": component},
        )

    answer_target: str | None = None
    answer = raw.get("answer")
    if "answer" in raw:
        parsed_answer = _reference(answer, collector, node_id=None, path="answer")
        if parsed_answer is None or parsed_answer[0] != "node":
            collector.add(
                ErrorCode.INVALID_ANSWER_REFERENCE,
                "answer must reference a node output",
                path="answer",
            )
        else:
            _, target, port = parsed_answer
            if target not in node_by_id:
                collector.add(
                    ErrorCode.DANGLING_NODE_REFERENCE,
                    f"Answer refers to unknown node {target!r}",
                    path="answer",
                    details={"node_id": target},
                )
            else:
                answer_target = target
                expected_port = output_ports.get(target)
                if expected_port is not None and port != expected_port:
                    collector.add(
                        ErrorCode.OUTPUT_PORT_MISMATCH,
                        f"Answer node {target!r} exposes port {expected_port!r}, not {port!r}",
                        path="answer",
                        details={"target": target, "actual": port, "expected": expected_port},
                    )
                answer_type = output_types.get(target)
                type_specification = registry.types.get(answer_type, {})
                # v0.1 did not encode termination eligibility.  Enforce this
                # only when the selected registry explicitly defines it.
                if (
                    generated_plan
                    and "answer_eligible" in type_specification
                    and not type_specification["answer_eligible"]
                ):
                    collector.add(
                        ErrorCode.ANSWER_TYPE_NOT_ELIGIBLE,
                        f"Node {target!r} output type {answer_type!r} is not answer-eligible",
                        node_id=target,
                        path="answer",
                        details={"type": answer_type},
                    )

    if answer_target is not None:
        live: set[str] = set()
        stack = [answer_target]
        source_reachable = False
        while stack:
            current = stack.pop()
            if current in live:
                continue
            live.add(current)
            if source_inputs_by_node.get(current):
                source_reachable = True
            stack.extend(sorted(adjacency.get(current, ()), reverse=True))
        if not source_reachable:
            collector.add(
                ErrorCode.ANSWER_NOT_SOURCE_REACHABLE,
                "The answer node has no data-dependency path from a declared source",
                node_id=answer_target,
                path="answer",
            )
        for dead_id in sorted(set(node_by_id) - live):
            collector.warn(
                ErrorCode.DEAD_NODE,
                f"Node {dead_id!r} does not contribute to the answer",
                node_id=dead_id,
                path=node_path_by_id.get(dead_id, "nodes"),
                details={"node_id": dead_id},
            )

    inferred_types = {
        node_id: output_type
        for node_id, output_type in output_types.items()
        if registry.is_type(output_type)
    }
    return collector.report(
        topological_order=_topological_order(adjacency),
        inferred_types=inferred_types,
    )


__all__ = [
    "ErrorCode",
    "ValidationError",
    "ValidationReport",
    "validate_graph",
]
