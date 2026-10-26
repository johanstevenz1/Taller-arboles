# Inventory Tree Explorer

A small warehouse needs to find products by numeric SKU, keep its catalog sorted, and add or remove products without repeatedly sorting a list. This project uses an **AVL binary search tree implemented from scratch**. Each product is a node; smaller SKUs belong to its left subtree and larger SKUs to its right. Rotations guarantee logarithmic lookup, insertion, and deletion even when input is sorted, and inorder traversal produces the sorted inventory directly. The tree is the actual inventory store, not a diagram over a dictionary or database.

The application, branded **Arbórea**, combines Python 3.10+, FastAPI, and a responsive HTML/CSS/vanilla JavaScript frontend. Its SVG visualization renders the real tree returned by the API. All identifiers, comments, docstrings, filenames, and endpoints are in English. All visible application text, including sample product names and errors, is in Spanish and centralized in `frontend/js/messages.js`.

## Features

- Handwritten product `Node` and `InventoryTree` classes; no tree libraries.
- AVL insertion and deletion with left, right, left-right, and right-left rotations.
- Delete a leaf, a node with one child, a node with two children, or the root while preserving every other product and its stock.
- Exact SKU lookup with its search path; case-insensitive partial product-name search.
- Preorder, inorder, postorder, and breadth-first (level-order) traversals.
- Interactive SVG nodes, highlighted search paths, animated traversal order, visit badges, and a fit-view control.
- Product count, edge height, leaf count, total units, and balance statistics.
- Spanish validation, success, empty-state, duplicate, missing-product, and connection messages.
- Accessible product controls, labeled forms, reduced-motion support, and responsive layouts.
- Optional nine-product example loaded through an explicit action; replacing existing data requires an in-page confirmation.
- Thread-safe API mutations and atomic example replacement.

## Requirements and installation

Use Python **3.10 or newer**, pip, and a modern browser. Development was verified on Windows with Python 3.13.3. Direct dependency versions are pinned in `requirements.txt`; no Node.js build step or database is needed. Optional Google Fonts have system-font fallbacks.

```bash
git clone https://github.com/johanstevenz1/Taller-arboles.git
cd Taller-arboles
python -m venv venv
```

Activate the environment on macOS/Linux:

```bash
source venv/bin/activate
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

Then install and start the server from the project root:

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Open **http://127.0.0.1:8000**. API documentation is available at **http://127.0.0.1:8000/docs**.

If PowerShell blocks environment activation, use its Python executable directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

## Walkthrough

1. Click **Cargar ejemplo** to load nine products (245 units, height 3, five leaves).
2. Under **Agregar**, enter SKU `450`, a product name, and stock `7`. The tree rotates if necessary and all metrics update after the request succeeds.
3. Under **Buscar**, search for `450`. The actual lookup path and matching product are highlighted. Search by a partial name to inspect text matching.
4. Click a node, or focus it and press Enter/Space, to inspect its product and prefill the deletion field.
5. Under **Eliminar**, delete `450`; every other product is retained. Deleting a root with two children replaces it using its inorder successor and then rebalances.
6. Select **Inorden**, **Preorden**, **Postorden**, or **Por niveles**, then click **Iniciar recorrido**. Badges and the result sequence show the visit order. Click **Detener recorrido** to cancel.
7. Use **Ajustar vista del árbol** to fit a wide diagram inside its panel. On small screens the map also supports horizontal scrolling.

## State and scope

This is an educational, local, in-memory inventory application. A new server process starts with an empty tree. Browser reloads keep the inventory; restarting the server clears it. Tabs connected to the same process share the inventory, but another tab must reload to see changes made elsewhere. Run **one Uvicorn worker**; each worker would otherwise own a separate tree. The `--reload` option is for local development and also resets memory when backend code changes.

The service caps its interactive inventory at **127 products** to keep the SVG manageable. The underlying AVL implementation is not capped (the tests insert 1,000 ordered products). SKUs are integers from 1 to 99999, quantities are integers from 0 to 99999, and trimmed names contain 1 to 60 characters. Zero stock is allowed; duplicate SKUs are rejected. User content is rendered with `textContent`, not injected as HTML.

## Tree model and complexity

`Node` stores `sku`, `name`, `quantity`, `left`, `right`, and cached `height`. `InventoryTree` owns `root` and a cached node count. Its search-order invariant is `left.sku < node.sku < right.sku`; every node's child heights differ by at most one. Heights count **edges**, so an empty tree has height **-1** and a leaf has height **0**.

Here, `n` is the number of products, `h = O(log n)` for an AVL tree, and `m` is the maximum product-name length. Complexity refers to tree work and excludes HTTP transfer and SVG rendering.

| Operation | Worst-case time | Auxiliary space, excluding returned data |
| --- | --- | --- |
| Construct empty tree | O(1) | O(1) |
| Construct/validate a node | O(m) | O(m) for trimming |
| Insert SKU | O(log n + m) | O(log n) recursion |
| Find exact SKU | O(log n) | O(1) |
| Search numeric query and return visits | O(log n) | O(log n) search path |
| Search partial name | O(n m) | O(n) traversal list |
| Delete SKU, including successor and rotations | O(log n + m) | O(log n) recursion |
| Any traversal | O(n) | DFS O(log n), BFS O(n), plus O(n) result |
| Height | O(1) | O(1) |
| Size | O(1) | O(1) |
| Flat node serialization | O(1) | O(1) references |
| Nested tree serialization to JSON-compatible data | O(n) | O(log n) stack, plus O(n) result |
| Compute statistics | O(n) | O(n) traversal list |
| Load example atomically | O(n log n + n m) | O(n) replacement tree |

Product names are bounded to 60 characters, so insert/delete retain **O(log n)** complexity with respect to `n`. Exact SKU lookup follows tree links. Name search intentionally scans all nodes and does not claim logarithmic complexity. A hash table would provide exact-key access but no natural ordering, ordered traversal, or hierarchical visualization; a sorted list would require O(n) shifts on insertion and deletion.

## REST API

All endpoints use JSON and the same origin as the frontend. A node's `id` is its numeric SKU.

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | `/api/tree` | Consistent `{root, stats}` snapshot; `root` is null when empty |
| POST | `/api/nodes` | Add `{sku, name, quantity}`; return a flat product, HTTP 201 |
| DELETE | `/api/nodes/{id}` | Remove only that product and return its original payload |
| GET | `/api/search?query=450` | Return `{matches, path}`; no match returns HTTP 200 and an empty list |
| GET | `/api/traversal/preorder` | Root, left, right |
| GET | `/api/traversal/inorder` | Left, root, right; ascending SKUs |
| GET | `/api/traversal/postorder` | Left, right, root |
| GET | `/api/traversal/level-order` | Breadth-first using a queue |
| GET | `/api/stats` | Size, edge height, leaves, units, root SKU, balance |
| POST | `/api/example` | Atomically replace data with an explicitly submitted list of 1–127 products |

For example, submit this body to `POST /api/nodes`:

```json
{"sku": 450, "name": "Sample product", "quantity": 7}
```

Domain failures return stable codes that `messages.js` translates: `duplicate_node` (409), `node_not_found` (404), `invalid_node` (422), and `capacity_reached` (409). Invalid request fields or unsupported traversal types return `invalid_input` (422). Missing search results are not transport errors. API developer documentation is in English; the application translates all user-facing errors into Spanish.

## Testing

From the project root, with the environment active:

```bash
python -m pytest
```

The default pytest configuration measures statements and branches in `backend/models` and requires at least **81%** coverage. The verified result is **58 passing tests and 100% model coverage** (171 statements and 66 branches). The suite covers:

- Node validation, zero stock, inclusive numeric limits, and JSON data.
- Empty-tree behavior and missing or duplicate products without mutation.
- All four insertion rotation shapes and deterministic traversal sequences.
- Leaf, one-child, two-child, and root deletion, preserving product payloads.
- Independent ordering, actual-height, cached-size, and balance checks after every mutation across five randomized 150-product lifecycles.
- 1,000 sorted insertions without degeneration into a linked list.
- API lifecycle, error codes, validation, capacity, atomic replacement, isolated app instances, static assets, and concurrent inserts.

A third-party deprecation warning from Starlette/AnyIO may appear; it does not fail the suite. See `docs/verification.md` for browser evidence and the remaining visual-verification limit.

## Frontend screenshots and verification status

The frontend was opened in the browser and visually inspected at mobile and desktop widths during development. Browser interactions verified example loading, insertion, successful search, duplicate rejection, deletion, missing search results, and root deletion while preserving other products.

**Final screenshot files are pending.** Computer Use stopped because it could not determine the desktop browser URL with sufficient confidence. No mock screenshot is presented as evidence. The four traversal sequences are covered by automated tree/API tests; their full animation and the final in-page confirmation still need a browser pass. To finish this assignment item, run the app, load the example, save real screenshots under `docs/`, and reference them here with Markdown image links.

## Project structure

```text
.
├── AGENTS.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── exceptions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── node.py
│   │   └── tree.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── inventory.py
│   └── routes/
│       ├── __init__.py
│       └── tree.py
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js
│       ├── messages.js
│       ├── tree-view.js
│       └── main.js
├── tests/
│   ├── __init__.py
│   ├── test_node.py
│   ├── test_tree.py
│   └── test_api.py
└── docs/
    └── verification.md
```

## Assignment checklist

- [x] Justification written before implementation.
- [x] Python backend, functional Spanish frontend, English code and docstrings.
- [x] Tree implementation from scratch with all required operations.
- [x] Four traversals, custom exceptions, JSON serialization, and complexity documentation.
- [x] All required REST endpoints plus atomic example loading.
- [x] Interactive SVG map, forms, traversal animation controls, and statistics.
- [x] Pytest passes with coverage above 80%.
- [x] Pinned dependencies and installation instructions.
- [x] No credentials, environment, or private records in the repository.
- [ ] Save final real frontend screenshots and complete the final animation/dialog browser pass.

## Author and repository

Author / repository owner: [johanstevenz1](https://github.com/johanstevenz1). Developed with AI assistance for a data-structures workshop.

Repository: **https://github.com/johanstevenz1/Taller-arboles**

The user-specified repository name is retained even though the assignment suggests an English kebab-case name. Submit the repository URL above in the professor's delivery space.
