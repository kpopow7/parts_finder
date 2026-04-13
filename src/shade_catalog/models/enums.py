from enum import Enum


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
