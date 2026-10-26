"""FastAPI application factory and same-origin static frontend."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.exceptions import (
    CapacityError,
    DuplicateNodeError,
    InvalidNodeError,
    NodeNotFoundError,
    TreeError,
)
from backend.routes.tree import router
from backend.services.inventory import InventoryService

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    """Build an isolated application and empty inventory in O(1) time."""
    application = FastAPI(title="Inventory Tree Explorer", version="1.0.0")
    application.state.inventory = InventoryService()
    application.include_router(router)

    @application.exception_handler(TreeError)
    async def handle_tree_error(request: Request, error: TreeError) -> JSONResponse:
        """Map domain errors to stable, frontend-translatable codes in O(1)."""
        mapping = {
            NodeNotFoundError: (404, "node_not_found"),
            DuplicateNodeError: (409, "duplicate_node"),
            InvalidNodeError: (422, "invalid_node"),
            CapacityError: (409, "capacity_reached"),
        }
        status, code = mapping.get(type(error), (400, "tree_error"))
        return JSONResponse(status_code=status, content={"code": code})

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        """Return a validation code without leaking English UI strings in O(1)."""
        return JSONResponse(status_code=422, content={"code": "invalid_input"})

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Serve the Spanish interface in O(1) setup time."""
        return FileResponse(FRONTEND / "index.html")

    application.mount("/static", StaticFiles(directory=FRONTEND), name="static")
    return application


app = create_app()
