from enum import Enum
from typing import TypeVar

_E = TypeVar("_E", bound=Enum)


def str_enum_values_callable(enum_cls: type[_E]) -> list[str]:
    """Pass to ``SQLEnum(..., values_callable=...)`` so VARCHAR stores str Enum **values** (e.g. ``draft``), not member names (``DRAFT``)."""

    return [member.value for member in enum_cls]


def enum_as_str(value: Enum | str) -> str:
    """Serialize ORM enum columns. String-mapped columns may load as plain ``str`` from the DB."""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class ProductStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PartStatus(str, Enum):
    ACTIVE = "active"
    DISCONTINUED = "discontinued"


class UserRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
