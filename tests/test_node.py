"""Node validation and serialization tests."""

import pytest

from backend.exceptions import InvalidNodeError
from backend.models.node import Node


def test_node_defaults_and_flat_serialization() -> None:
    """Create independent child links and trim user input."""
    node = Node(20, "  Keyboard  ")
    assert node.left is None and node.right is None
    assert node.to_dict() == {
        "id": 20, "sku": 20, "name": "Keyboard", "quantity": 1, "height": 0,
    }


@pytest.mark.parametrize("sku,name,quantity", [
    (0, "Item", 1), (100000, "Item", 1), (True, "Item", 1),
    (1.5, "Item", 1), (1, "", 1), (1, "   ", 1),
    (1, "x" * 61, 1), (1, None, 1), (1, "Item", -1),
    (1, "Item", 100000), (1, "Item", True), (1, "Item", 1.1),
])
def test_invalid_products(sku: object, name: object, quantity: object) -> None:
    """Reject invalid domain data including booleans masquerading as integers."""
    with pytest.raises(InvalidNodeError):
        Node(sku, name, quantity)


def test_zero_stock_and_boundary_values() -> None:
    """Accept the documented inclusive numeric bounds."""
    assert Node(99999, "x" * 60, 0).quantity == 0
