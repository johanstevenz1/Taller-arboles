"""Product nodes used by the handwritten AVL tree."""

from dataclasses import dataclass
from typing import Any

from backend.exceptions import InvalidNodeError


@dataclass(slots=True)
class Node:
    """Store one product and two child links. Construction is O(1)."""

    sku: int
    name: str
    quantity: int = 1
    left: "Node | None" = None
    right: "Node | None" = None
    height: int = 0

    def __post_init__(self) -> None:
        """Validate product fields in O(m), where m is the name length."""
        if type(self.sku) is not int or not 1 <= self.sku <= 99999:
            raise InvalidNodeError("SKU must be an integer between 1 and 99999.")
        if not isinstance(self.name, str):
            raise InvalidNodeError("Product name must be text.")
        self.name = self.name.strip()
        if not 1 <= len(self.name) <= 60:
            raise InvalidNodeError("Product name must contain 1 to 60 characters.")
        if type(self.quantity) is not int or not 0 <= self.quantity <= 99999:
            raise InvalidNodeError("Quantity must be an integer between 0 and 99999.")

    def to_dict(self) -> dict[str, Any]:
        """Return flat, JSON-compatible product data in O(1) time."""
        return {"id": self.sku, "sku": self.sku, "name": self.name,
                "quantity": self.quantity, "height": self.height}
