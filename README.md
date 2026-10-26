# Inventory Tree Explorer

A small warehouse needs to find products by numeric SKU, maintain a sorted catalog, and insert or remove products without repeatedly sorting a list. This project uses an AVL binary search tree implemented from scratch. Each product is a node; smaller SKUs belong to the left subtree and larger SKUs to the right. Rotations preserve logarithmic search, insertion, and deletion even for sorted input, and inorder traversal produces the ordered inventory directly. The tree is the actual inventory store.

Python 3.10+ and FastAPI provide the backend; HTML, CSS, vanilla JavaScript, and SVG provide the frontend. Code and documentation are in English; visible UI text is centralized in Spanish.

## Planned structure

- backend/models: Node and AVL tree
- backend/services: inventory service and sample catalog
- backend/routes: REST API
- frontend: HTML, CSS, JavaScript, and SVG rendering
- tests: tree invariants, operations, and API integration
- docs: actual frontend screenshots

Repository: https://github.com/johanstevenz1/Taller-arboles

Verification and usage documentation will be completed after implementation.
