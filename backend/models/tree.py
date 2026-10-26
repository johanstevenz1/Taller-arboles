"""AVL inventory with handwritten rotations, deletion, and traversals."""

from collections import deque
from typing import Any, Literal

from backend.exceptions import DuplicateNodeError, NodeNotFoundError
from backend.models.node import Node

TraversalOrder = Literal["preorder", "inorder", "postorder", "level-order"]


class InventoryTree:
    """Maintain products in an AVL search tree; initialization is O(1)."""

    def __init__(self) -> None:
        """Create an empty tree in O(1) time."""
        self.root: Node | None = None
        self._size = 0

    @property
    def size(self) -> int:
        """Return the cached number of nodes in O(1) time."""
        return self._size

    @property
    def height(self) -> int:
        """Return edge height in O(1): empty = -1, leaf = 0."""
        return self._height(self.root)

    def insert(self, sku: int, name: str, quantity: int = 1) -> Node:
        """Insert a unique SKU in O(log n) time plus O(m) name validation."""
        node = Node(sku, name, quantity)
        self.root = self._insert(self.root, node)
        self._size += 1
        return node

    def find(self, sku: int) -> Node:
        """Find an exact SKU in O(log n) time and O(1) auxiliary space."""
        current = self.root
        while current is not None:
            if current.sku == sku:
                return current
            current = current.left if sku < current.sku else current.right
        raise NodeNotFoundError(f"SKU {sku} was not found.")

    def search(self, query: str) -> tuple[list[Node], list[int]]:
        """Return matches and visits: numeric O(log n), name O(n*m)."""
        query = query.strip()
        if not query:
            return [], []
        if query.isascii() and query.isdecimal():
            sku = int(query)
            current = self.root
            path: list[int] = []
            while current is not None:
                path.append(current.sku)
                if current.sku == sku:
                    return [current], path
                current = current.left if sku < current.sku else current.right
            return [], path
        nodes = self.traverse("inorder")
        return (
            [node for node in nodes if query.casefold() in node.name.casefold()],
            [node.sku for node in nodes],
        )

    def remove(self, sku: int) -> Node:
        """Delete a SKU, retaining its children, in O(log n) time."""
        found = self.find(sku)
        removed = Node(found.sku, found.name, found.quantity)
        self.root = self._remove(self.root, sku)
        self._size -= 1
        return removed

    def traverse(self, order: TraversalOrder = "inorder") -> list[Node]:
        """Visit all nodes in O(n) time and O(n) output/auxiliary space."""
        if order not in ("preorder", "inorder", "postorder", "level-order"):
            raise ValueError("Unsupported traversal order.")
        result: list[Node] = []
        if self.root is None:
            return result
        if order == "level-order":
            queue = deque([self.root])
            while queue:
                node = queue.popleft()
                result.append(node)
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
        else:
            self._visit(self.root, order, result)
        return result

    def to_dict(self) -> dict[str, Any] | None:
        """Serialize the whole tree for JSON in O(n) time and space."""
        return self._serialize(self.root)

    def stats(self) -> dict[str, Any]:
        """Compute inventory statistics in O(n) time and O(n) space."""
        nodes = self.traverse("inorder")
        return {
            "size": self.size,
            "height": self.height,
            "leaves": sum(node.left is None and node.right is None for node in nodes),
            "total_quantity": sum(node.quantity for node in nodes),
            "root": self.root.sku if self.root else None,
            "balanced": all(abs(self._balance(node)) <= 1 for node in nodes),
        }

    @staticmethod
    def _height(node: Node | None) -> int:
        return node.height if node else -1

    def _update(self, node: Node) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance(self, node: Node) -> int:
        return self._height(node.left) - self._height(node.right)

    def _rotate_left(self, node: Node) -> Node:
        pivot = node.right
        assert pivot is not None
        node.right = pivot.left
        pivot.left = node
        self._update(node)
        self._update(pivot)
        return pivot

    def _rotate_right(self, node: Node) -> Node:
        pivot = node.left
        assert pivot is not None
        node.left = pivot.right
        pivot.right = node
        self._update(node)
        self._update(pivot)
        return pivot

    def _rebalance(self, node: Node) -> Node:
        self._update(node)
        balance = self._balance(node)
        if balance > 1:
            assert node.left is not None
            if self._balance(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1:
            assert node.right is not None
            if self._balance(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    def _insert(self, root: Node | None, node: Node) -> Node:
        if root is None:
            return node
        if node.sku == root.sku:
            raise DuplicateNodeError(f"SKU {node.sku} already exists.")
        if node.sku < root.sku:
            root.left = self._insert(root.left, node)
        else:
            root.right = self._insert(root.right, node)
        return self._rebalance(root)

    def _remove(self, root: Node | None, sku: int) -> Node | None:
        assert root is not None
        if sku < root.sku:
            root.left = self._remove(root.left, sku)
        elif sku > root.sku:
            root.right = self._remove(root.right, sku)
        else:
            if root.left is None:
                return root.right
            if root.right is None:
                return root.left
            successor = root.right
            while successor.left:
                successor = successor.left
            root.sku, root.name, root.quantity = (
                successor.sku,
                successor.name,
                successor.quantity,
            )
            root.right = self._remove(root.right, successor.sku)
        return self._rebalance(root)

    def _visit(self, node: Node | None, order: str, result: list[Node]) -> None:
        if node is None:
            return
        if order == "preorder":
            result.append(node)
        self._visit(node.left, order, result)
        if order == "inorder":
            result.append(node)
        self._visit(node.right, order, result)
        if order == "postorder":
            result.append(node)

    def _serialize(self, node: Node | None) -> dict[str, Any] | None:
        if node is None:
            return None
        return {
            **node.to_dict(),
            "balance": self._balance(node),
            "left": self._serialize(node.left),
            "right": self._serialize(node.right),
        }
