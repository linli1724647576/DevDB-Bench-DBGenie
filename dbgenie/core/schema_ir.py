from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnIR:
    name: str
    type: str
    nullable: bool = True
    identity: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ColumnIR":
        return cls(
            name=str(data["name"]),
            type=str(data.get("type", "")),
            nullable=bool(data.get("nullable", True)),
            identity=bool(
                data.get("identity")
                or data.get("auto_increment")
                or data.get("autoincrement")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
        }
        if self.identity:
            payload["identity"] = True
        return payload


@dataclass(frozen=True)
class ForeignKeyIR:
    columns: list[str]
    ref_table: str
    ref_columns: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ForeignKeyIR":
        references = data.get("references") if isinstance(data.get("references"), dict) else {}
        return cls(
            columns=_string_list(data.get("columns") or data.get("column")),
            ref_table=str(
                data.get("ref_table")
                or data.get("referenced_table")
                or data.get("reference_table")
                or data.get("target_table")
                or references.get("table")
                or references.get("ref_table")
                or ""
            ),
            ref_columns=_string_list(
                data.get("ref_columns")
                or data.get("referenced_columns")
                or data.get("reference_columns")
                or data.get("target_columns")
                or references.get("columns")
                or references.get("ref_columns")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "ref_table": self.ref_table,
            "ref_columns": self.ref_columns,
        }


@dataclass(frozen=True)
class UniqueConstraintIR:
    columns: list[str]
    name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UniqueConstraintIR":
        return cls(
            columns=_string_list(data.get("columns") or data.get("column")),
            name=data.get("name"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"columns": self.columns}
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class CheckConstraintIR:
    expression: str
    columns: list[str] = field(default_factory=list)
    name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckConstraintIR":
        if isinstance(data, str):
            return cls(expression=data)
        return cls(
            expression=str(data.get("expression", "")),
            columns=list(data.get("columns", [])),
            name=data.get("name"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "expression": self.expression,
            "columns": self.columns,
        }
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class IndexIR:
    columns: list[str]
    name: str | None = None
    unique: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexIR":
        return cls(
            columns=_string_list(data.get("columns") or data.get("column")),
            name=data.get("name"),
            unique=bool(data.get("unique", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "columns": self.columns,
            "unique": self.unique,
        }
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class TableIR:
    name: str
    columns: list[ColumnIR] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKeyIR] = field(default_factory=list)
    unique_constraints: list[UniqueConstraintIR] = field(default_factory=list)
    check_constraints: list[CheckConstraintIR] = field(default_factory=list)
    indexes: list[IndexIR] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableIR":
        return cls(
            name=str(data["name"]),
            columns=[
                ColumnIR.from_dict(item) for item in _dict_items(data.get("columns", []))
            ],
            primary_key=_string_list(data.get("primary_key")),
            foreign_keys=[
                ForeignKeyIR.from_dict(item)
                for item in _dict_items(data.get("foreign_keys", []))
            ],
            unique_constraints=[
                UniqueConstraintIR.from_dict(item)
                for item in _dict_items(data.get("unique_constraints", []))
            ],
            check_constraints=[
                CheckConstraintIR.from_dict(item)
                for item in _dict_items(data.get("check_constraints", []))
            ],
            indexes=[IndexIR.from_dict(item) for item in _dict_items(data.get("indexes", []))],
        )

    def column_names(self) -> set[str]:
        return {column.name for column in self.columns}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "columns": [column.to_dict() for column in self.columns],
            "primary_key": self.primary_key,
            "foreign_keys": [foreign_key.to_dict() for foreign_key in self.foreign_keys],
            "unique_constraints": [
                constraint.to_dict() for constraint in self.unique_constraints
            ],
            "check_constraints": [
                constraint.to_dict() for constraint in self.check_constraints
            ],
            "indexes": [index.to_dict() for index in self.indexes],
        }


@dataclass(frozen=True)
class SchemaIR:
    tables: list[TableIR] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SchemaIR":
        if not data:
            return cls()
        return cls(tables=[TableIR.from_dict(item) for item in data.get("tables", [])])

    def table_names(self) -> set[str]:
        return {table.name for table in self.tables}

    def table_count(self) -> int:
        return len(self.tables)

    def find_table(self, name: str) -> TableIR | None:
        normalized = name.lower()
        for table in self.tables:
            if table.name.lower() == normalized:
                return table
        return None

    def to_dict(self) -> dict[str, Any]:
        return {"tables": [table.to_dict() for table in self.tables]}


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        return _string_list(
            value.get("columns")
            or value.get("column")
            or value.get("names")
            or value.get("fields")
            or value.get("field")
        )
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("column") or item.get("field")
                if name:
                    result.append(str(name))
            else:
                result.append(str(item))
        return result
    return [str(value)]


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []
