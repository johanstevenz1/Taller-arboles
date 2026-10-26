"""Thread-safe business operations around the AVL inventory."""

from threading import RLock
from typing import Any

from backend.exceptions import CapacityError
from backend.models.tree import InventoryTree, TraversalOrder

MAX_PRODUCTS = 127


class InventoryService:
    """Coordinate an in-memory inventory. Initialization is O(1)."""

    def __init__(self) -> None:
        """Create an empty inventory and lock in O(1) time."""
        self.tree = InventoryTree()
        self._lock = RLock()

    def snapshot(self) -> dict[str, Any]:
        """Return a consistent tree and statistics snapshot in O(n)."""
        with self._lock:
            return {"root": self.tree.to_dict(), "stats": self.tree.stats()}

    def add(self, sku: int, name: str, quantity: int) -> dict[str, Any]:
        """Insert a product in O(log n) plus name validation time."""
        with self._lock:
            if self.tree.size >= MAX_PRODUCTS:
                raise CapacityError("The interactive limit is 127 products.")
            return self.tree.insert(sku, name, quantity).to_dict()

    def remove(self, sku: int) -> dict[str, Any]:
        """Remove a product in O(log n) time."""
        with self._lock:
            return self.tree.remove(sku).to_dict()

    def search(self, query: str) -> dict[str, Any]:
        """Search SKU in O(log n) or names in O(n*m) time."""
        with self._lock:
            nodes, path = self.tree.search(query)
            return {"matches": [node.to_dict() for node in nodes], "path": path}

    def traverse(self, order: TraversalOrder) -> dict[str, Any]:
        """Return traversal results in O(n) time."""
        with self._lock:
            return {"order": order,
                    "nodes": [node.to_dict() for node in self.tree.traverse(order)]}

    def load_example(self, products: list[dict[str, Any]]) -> dict[str, Any]:
        """Atomically replace the inventory in O(n log n) time."""
        replacement = InventoryTree()
        for product in products:
            replacement.insert(**product)
        with self._lock:
            self.tree = replacement
            return self.snapshot()
