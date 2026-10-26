"""Domain errors exposed by the inventory tree."""


class TreeError(Exception):
    """Base domain error. Creation is O(1)."""


class NodeNotFoundError(TreeError):
    """A requested SKU does not exist. Creation is O(1)."""


class DuplicateNodeError(TreeError):
    """A SKU already exists. Creation is O(1)."""


class InvalidNodeError(TreeError):
    """Product data violates the domain rules. Creation is O(1)."""


class CapacityError(TreeError):
    """The interactive inventory has reached its capacity. Creation is O(1)."""
