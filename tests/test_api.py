"""REST integration tests with isolated application state."""

from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide an isolated inventory for each test."""
    with TestClient(create_app()) as test_client:
        yield test_client


def test_frontend_and_empty_endpoints(client: TestClient) -> None:
    """Serve static assets and valid empty-tree responses."""
    assert client.get("/").status_code == 200
    for path in [
        "/static/js/main.js",
        "/static/js/messages.js",
        "/static/css/styles.css",
        "/docs",
        "/openapi.json",
    ]:
        assert client.get(path).status_code == 200
    assert client.get("/api/tree").json()["root"] is None
    assert client.get("/api/stats").json()["height"] == -1
    assert client.get("/api/search", params={"query": "100"}).json()["matches"] == []
    for order in ["preorder", "inorder", "postorder", "level-order"]:
        assert client.get(f"/api/traversal/{order}").json()["nodes"] == []


def test_full_inventory_lifecycle(client: TestClient) -> None:
    """Exercise add, lookup, traversal, deletion, and final statistics."""
    for sku in [40, 20, 60, 10, 30, 50, 70]:
        response = client.post(
            "/api/nodes",
            json={
                "sku": sku,
                "name": f"Product {sku}",
                "quantity": 2,
            },
        )
        assert response.status_code == 201
        assert response.json()["id"] == sku
    assert client.get("/api/stats").json()["total_quantity"] == 14
    result = client.get("/api/search", params={"query": "30"}).json()
    assert result["path"] == [40, 20, 30]
    assert result["matches"][0]["sku"] == 30
    result = client.get("/api/search", params={"query": "pRODUCT 3"}).json()
    assert result["matches"][0]["sku"] == 30
    for order in ["preorder", "inorder", "postorder", "level-order"]:
        assert len(client.get(f"/api/traversal/{order}").json()["nodes"]) == 7
    assert client.delete("/api/nodes/40").json()["sku"] == 40
    assert client.get("/api/stats").json()["size"] == 6
    assert client.get("/api/stats").json()["balanced"] is True
    for sku in [20, 60, 10, 30, 50, 70]:
        assert client.delete(f"/api/nodes/{sku}").status_code == 200
    assert client.get("/api/tree").json()["root"] is None


def test_duplicate_and_missing_errors(client: TestClient) -> None:
    """Expose stable error codes without mutating inventory."""
    product = {"sku": 5, "name": "Product", "quantity": 0}
    assert client.post("/api/nodes", json=product).status_code == 201
    response = client.post("/api/nodes", json=product)
    assert response.status_code == 409
    assert response.json() == {"code": "duplicate_node"}
    response = client.delete("/api/nodes/999")
    assert response.status_code == 404
    assert response.json() == {"code": "node_not_found"}
    assert client.get("/api/stats").json()["size"] == 1


@pytest.mark.parametrize(
    "product",
    [
        {},
        {"sku": 0, "name": "Product"},
        {"sku": True, "name": "Product"},
        {"sku": 2.5, "name": "Product"},
        {"sku": 1, "name": "   "},
        {"sku": 1, "name": "x" * 61},
        {"sku": 1, "name": "Product", "quantity": -1},
        {"sku": 1, "name": "Product", "quantity": True},
        {"sku": 1, "name": "Product", "extra": 1},
    ],
)
def test_invalid_request_data(client: TestClient, product: dict) -> None:
    """Reject invalid JSON fields with a translatable validation code."""
    response = client.post("/api/nodes", json=product)
    assert response.status_code == 422
    assert response.json() == {"code": "invalid_input"}
    assert client.get("/api/stats").json()["size"] == 0


def test_invalid_routes_and_queries(client: TestClient) -> None:
    """Reject missing search queries, unknown traversals, and invalid IDs."""
    for path in [
        "/api/search",
        "/api/search?query=",
        "/api/traversal/diagonal",
        "/api/nodes/not-a-number",
    ]:
        response = client.delete(path) if "/nodes/" in path else client.get(path)
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_input"


def test_example_replacement_is_atomic(client: TestClient) -> None:
    """An invalid replacement keeps the entire existing inventory intact."""
    products = [{"sku": sku, "name": f"Product {sku}"} for sku in [20, 10, 30]]
    assert client.post("/api/example", json=products).status_code == 200
    before = client.get("/api/tree").json()
    response = client.post("/api/example", json=products + [products[0]])
    assert response.status_code == 409
    assert client.get("/api/tree").json() == before
    assert client.post("/api/example", json=[]).status_code == 422
    assert client.post("/api/example", json=products[:1]).json()["stats"]["size"] == 1


def test_interactive_capacity(client: TestClient) -> None:
    """Bound the SVG demo without constraining the underlying AVL class."""
    products = [{"sku": sku, "name": f"Product {sku}"} for sku in range(1, 128)]
    assert client.post("/api/example", json=products).status_code == 200
    response = client.post("/api/nodes", json={"sku": 500, "name": "Extra"})
    assert response.status_code == 409
    assert response.json() == {"code": "capacity_reached"}
    assert (
        client.post(
            "/api/example", json=products + [{"sku": 900, "name": "Extra"}]
        ).status_code
        == 422
    )


def test_concurrent_inserts_preserve_state(client: TestClient) -> None:
    """Concurrent API requests must not corrupt counters or structure."""

    def insert(sku: int) -> int:
        """Insert one product from a worker thread."""
        return client.post(
            "/api/nodes", json={"sku": sku, "name": "Product"}
        ).status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(insert, range(1, 41)))
    assert statuses == [201] * 40
    stats = client.get("/api/stats").json()
    assert stats["size"] == 40 and stats["balanced"] is True


def test_application_instances_are_isolated() -> None:
    """Different app factories must not share a module-global inventory."""
    with TestClient(create_app()) as first, TestClient(create_app()) as second:
        first.post("/api/nodes", json={"sku": 1, "name": "Product"})
        assert second.get("/api/stats").json()["size"] == 0
