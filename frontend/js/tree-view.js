/** SVG tree renderer using inorder ranks to guarantee non-overlapping nodes. */
import { messages } from "./messages.js";

const namespace = "http://www.w3.org/2000/svg";

function element(tag, attributes = {}, content) {
  const node = document.createElementNS(namespace, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (content !== undefined) node.textContent = content;
  return node;
}

export class TreeView {
  constructor(svg, onSelect) {
    this.svg = svg;
    this.onSelect = onSelect;
    this.groups = new Map();
  }

  render(root) {
    this.svg.replaceChildren();
    this.groups.clear();
    document.getElementById("empty-state").hidden = Boolean(root);
    this.svg.toggleAttribute("hidden", !root);
    if (!root) return;
    const positions = new Map();
    let index = 0;
    let depth = 0;
    const place = (node, level) => {
      if (!node) return;
      place(node.left, level + 1);
      positions.set(node.sku, { x: 64 + index++ * 102, y: 54 + level * 106 });
      depth = Math.max(depth, level);
      place(node.right, level + 1);
    };
    place(root, 0);
    const width = Math.max(450, (index - 1) * 102 + 128);
    const height = Math.max(320, depth * 106 + 136);
    this.svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    this.svg.style.minWidth = `${Math.max(450, index * 72)}px`;
    this.svg.style.minHeight = `${Math.min(height, 540)}px`;
    const edges = element("g", { class: "tree-edges" });
    const nodes = element("g");
    const draw = (node) => {
      if (!node) return;
      const position = positions.get(node.sku);
      for (const child of [node.left, node.right]) {
        if (!child) continue;
        const destination = positions.get(child.sku);
        edges.append(element("path", { d: `M ${position.x} ${position.y + 25} C ${position.x} ${position.y + 65}, ${destination.x} ${destination.y - 65}, ${destination.x} ${destination.y - 25}` }));
      }
      const group = element("g", {
        class: `tree-node${node === root ? " is-root" : ""}`,
        transform: `translate(${position.x} ${position.y})`,
        "data-sku": node.sku, tabindex: "0", role: "button",
        "aria-label": `${messages.nodeAction}: ${node.sku}, ${node.name}, ${node.quantity} ${messages.unitLabel}`,
      });
      group.append(element("title", {}, `${node.name} · ${node.quantity} ${messages.unitLabel}`));
      group.append(element("circle", { r: 26, class: "node-circle" }));
      group.append(element("text", { class: "node-code", "text-anchor": "middle", y: 5 }, node.sku));
      group.append(element("text", { class: "node-name", "text-anchor": "middle", y: 47 }, node.name.length > 17 ? `${node.name.slice(0, 16)}…` : node.name));
      const badge = element("g", { class: "visit-badge", transform: "translate(23 -21)" });
      badge.append(element("circle", { r: 11 }));
      badge.append(element("text", { "text-anchor": "middle", y: 4 }));
      group.append(badge);
      const select = () => {
        this.clear();
        this.highlight(node.sku, "is-selected");
        this.onSelect(node);
      };
      group.addEventListener("click", select);
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select();
        }
      });
      this.groups.set(node.sku, group);
      nodes.append(group);
      draw(node.left);
      draw(node.right);
    };
    draw(root);
    this.svg.append(edges, nodes);
  }

  clear() {
    for (const group of this.groups.values()) {
      group.classList.remove("is-selected", "is-visited", "is-current", "is-path");
      group.querySelector(".visit-badge text").textContent = "";
    }
  }

  highlight(sku, state, step) {
    const group = this.groups.get(sku);
    if (!group) return;
    group.classList.add(state);
    if (step !== undefined) group.querySelector(".visit-badge text").textContent = step;
  }

  visit(sku, step) {
    for (const group of this.groups.values()) group.classList.remove("is-current");
    this.highlight(sku, "is-visited", step);
    this.highlight(sku, "is-current");
  }

  fit() {
    const container = this.svg.parentElement;
    this.svg.style.minWidth = "0px";
    container.scrollTo({ left: 0, top: 0, behavior: "smooth" });
  }
}
