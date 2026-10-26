"""AVL operations, structural invariants, and randomized regression tests."""

import json
import random

import pytest

from backend.exceptions import DuplicateNodeError, NodeNotFoundError
from backend.models.node import Node
from backend.models.tree import InventoryTree


def build_tree(keys: list[int]) -> InventoryTree:
    """Build a fixture from insertion-ordered SKUs."""
    tree = InventoryTree()
    for key in keys:
        tree.insert(key, f"Product {key}", key)
    return tree


def assert_invariants(tree: InventoryTree, expected: set[int]) -> None:
    """Independently verify ordering, actual heights, balance, and cached size."""
    def inspect(node: Node | None, lower: float, upper: float) -> int:
        """Recompute height recursively without trusting cached values."""
        if node is None:
            return -1
        assert lower < node.sku < upper
        left = inspect(node.left, lower, node.sku)
        right = inspect(node.right, node.sku, upper)
        assert abs(left - right) <= 1
        assert node.height == 1 + max(left, right)
        return node.height

    assert tree.height == inspect(tree.root, float("-inf"), float("inf"))
    assert tree.size == len(expected)
    assert [node.sku for node in tree.traverse("inorder")] == sorted(expected)


def test_empty_tree_and_missing_operations() -> None:
    """Define empty height, serialization, search, statistics, and errors."""
    tree = InventoryTree()
    assert tree.root is None and tree.size == 0 and tree.height == -1
    assert tree.to_dict() is None
    assert tree.search("42") == ([], [])
    assert tree.search("   ") == ([], [])
    assert tree.search("keyboard") == ([], [])
    for order in ["preorder", "inorder", "postorder", "level-order"]:
        assert tree.traverse(order) == []
    for operation in [tree.find, tree.remove]:
        with pytest.raises(NodeNotFoundError):
            operation(1)
    assert tree.stats() == {"size": 0, "height": -1, "leaves": 0,
                            "total_quantity": 0, "root": None, "balanced": True}


@pytest.mark.parametrize("keys", [[30, 20, 10], [10, 20, 30],
                                 [30, 10, 20], [10, 30, 20]])
def test_all_four_insert_rotations(keys: list[int]) -> None:
    """Cover single and double rotations for both balance directions."""
    tree = build_tree(keys)
    assert tree.root.sku == 20
    assert_invariants(tree, set(keys))


def test_duplicate_insert_does_not_mutate_tree() -> None:
    """A rejected SKU leaves all products and counters unchanged."""
    tree = build_tree([20, 10, 30])
    before = tree.to_dict()
    with pytest.raises(DuplicateNodeError):
        tree.insert(10, "Replacement", 0)
    assert tree.to_dict() == before
    assert tree.size == 3


@pytest.mark.parametrize("order,expected", [
    ("preorder", [40, 20, 10, 30, 60, 50, 70]),
    ("inorder", [10, 20, 30, 40, 50, 60, 70]),
    ("postorder", [10, 30, 20, 50, 70, 60, 40]),
    ("level-order", [40, 20, 60, 10, 30, 50, 70]),
])
def test_traversal_orders(order: str, expected: list[int]) -> None:
    """Compare traversals against manually determined sequences."""
    tree = build_tree([40, 20, 60, 10, 30, 50, 70])
    assert [node.sku for node in tree.traverse(order)] == expected


def test_invalid_traversal() -> None:
    """Reject unsupported orders for empty and nonempty trees."""
    for tree in [InventoryTree(), build_tree([1])]:
        with pytest.raises(ValueError):
            tree.traverse("diagonal")


@pytest.mark.parametrize("keys,target", [
    ([20], 20), ([20, 10], 20), ([20, 30], 20),
    ([20, 10, 30], 10), ([20, 10, 30, 5], 10),
    ([20, 10, 30, 40], 30), ([40, 20, 60, 10, 30, 50, 70, 45, 55], 40),
    ([40, 20, 60, 10, 30, 50, 70], 20),
])
def test_delete_leaf_one_child_two_children_and_root(
    keys: list[int], target: int
) -> None:
    """Retain every other product and its payload after deletion."""
    tree = build_tree(keys)
    removed = tree.remove(target)
    assert (removed.sku, removed.name, removed.quantity) == (
        target, f"Product {target}", target
    )
    assert_invariants(tree, set(keys) - {target})
    for key in set(keys) - {target}:
        assert tree.find(key).quantity == key
    with pytest.raises(NodeNotFoundError):
        tree.find(target)


def test_search_paths_and_name_matches() -> None:
    """Numeric lookup visits only a branch; text lookup checks names."""
    tree = build_tree([40, 20, 60, 10, 30, 50, 70])
    matches, path = tree.search(" 30 ")
    assert [node.sku for node in matches] == [30]
    assert path == [40, 20, 30]
    assert tree.search("31") == ([], [40, 20, 30])
    assert tree.find(70).sku == 70
    matches, visits = tree.search("PRODUCT 2")
    assert [node.sku for node in matches] == [20]
    assert len(visits) == tree.size
    assert tree.search("absent")[0] == []


def test_json_serialization_and_statistics() -> None:
    """Return nested JSON and metrics derived from actual inventory."""
    tree = build_tree([20, 10, 30])
    data = json.loads(json.dumps(tree.to_dict()))
    assert data["sku"] == 20 and data["balance"] == 0
    assert data["left"]["sku"] == 10 and data["right"]["sku"] == 30
    assert data["left"]["left"] is None
    assert tree.stats() == {"size": 3, "height": 1, "leaves": 2,
                            "total_quantity": 60, "root": 20, "balanced": True}


def test_sorted_input_stays_logarithmic() -> None:
    """Inserting sorted SKUs must not degenerate into a linked list."""
    tree = build_tree(list(range(1, 1001)))
    assert_invariants(tree, set(range(1, 1001)))
    assert tree.height <= 14


@pytest.mark.parametrize("seed", range(5))
def test_randomized_insert_delete_invariants(seed: int) -> None:
    """Check every mutation across deterministic, shuffled full lifecycles."""
    generator = random.Random(seed)
    keys = generator.sample(range(1, 2000), 150)
    tree = InventoryTree()
    expected: set[int] = set()
    for key in keys:
        tree.insert(key, f"Product {key}", key)
        expected.add(key)
        assert_invariants(tree, expected)
    generator.shuffle(keys)
    for key in keys:
        tree.remove(key)
        expected.remove(key)
        assert_invariants(tree, expected)
    assert tree.root is None
