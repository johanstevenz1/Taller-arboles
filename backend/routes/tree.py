"""REST endpoints for inventory operations."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.services.inventory import InventoryService, MAX_PRODUCTS

router = APIRouter(prefix="/api", tags=["inventory"])


class ProductInput(BaseModel):
    """Validate a product request before mutation; O(m) for name length m."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    sku: int = Field(ge=1, le=99999, strict=True)
    name: str = Field(min_length=1, max_length=60)
    quantity: int = Field(default=1, ge=0, le=99999, strict=True)


def get_inventory(request: Request) -> InventoryService:
    """Resolve the application-local inventory service in O(1)."""
    return request.app.state.inventory


Inventory = Annotated[InventoryService, Depends(get_inventory)]


@router.get("/tree")
def get_tree(inventory: Inventory) -> dict[str, Any]:
    """Return the complete tree and metrics in O(n) time."""
    return inventory.snapshot()


@router.post("/nodes", status_code=201)
def add_node(product: ProductInput, inventory: Inventory) -> dict[str, Any]:
    """Add a product in O(log n) plus validation time."""
    return inventory.add(**product.model_dump())


@router.delete("/nodes/{node_id}")
def delete_node(node_id: int, inventory: Inventory) -> dict[str, Any]:
    """Delete a product by SKU in O(log n) time."""
    return inventory.remove(node_id)


@router.get("/search")
def search_nodes(
    inventory: Inventory, query: str = Query(min_length=1, max_length=60)
) -> dict[str, Any]:
    """Search SKU in O(log n), or case-insensitive name in O(n*m)."""
    return inventory.search(query)


@router.get("/traversal/{order}")
def get_traversal(
    order: Literal["preorder", "inorder", "postorder", "level-order"],
    inventory: Inventory,
) -> dict[str, Any]:
    """Return any of the four supported traversals in O(n) time."""
    return inventory.traverse(order)


@router.get("/stats")
def get_stats(inventory: Inventory) -> dict[str, Any]:
    """Return computed inventory statistics in O(n) time."""
    return inventory.snapshot()["stats"]


@router.post("/example")
def load_example(
    products: Annotated[list[ProductInput], Field(min_length=1, max_length=MAX_PRODUCTS)],
    inventory: Inventory,
) -> dict[str, Any]:
    """Replace the inventory atomically with an example in O(n log n)."""
    return inventory.load_example([product.model_dump() for product in products])
