/** Spanish interface controller. The backend remains the source of truth. */
import { api } from "./api.js";
import { messages } from "./messages.js";
import { TreeView } from "./tree-view.js";

const byId = (id) => document.getElementById(id);
const number = new Intl.NumberFormat("es-CO");
let currentSize = 0;
let selectedOrder = "inorder";
let animationVersion = 0;
let playing = false;
let busy = false;

function translate() {
  document.title = messages.pageTitle;
  for (const node of document.querySelectorAll("[data-text]")) node.textContent = messages[node.dataset.text];
  for (const node of document.querySelectorAll("[data-placeholder]")) node.placeholder = messages[node.dataset.placeholder];
  for (const node of document.querySelectorAll("[data-label]")) node.setAttribute("aria-label", messages[node.dataset.label]);
  for (const node of document.querySelectorAll("[data-title]")) node.title = messages[node.dataset.title];
  for (const form of document.querySelectorAll("form")) form.noValidate = true;
}

function notify(message, error = false) {
  const notice = byId("notice");
  notice.textContent = message;
  notice.className = `notice${error ? " error" : ""}`;
  notice.setAttribute("role", error ? "alert" : "status");
  notice.hidden = false;
}

function stopAnimation() {
  animationVersion += 1;
  playing = false;
  byId("play-button").lastElementChild.textContent = messages.play;
}

const view = new TreeView(byId("tree-svg"), (node) => {
  stopAnimation();
  byId("tree-detail").textContent = `${node.sku} · ${node.name} · ${node.quantity} ${messages.unitLabel}`;
  byId("delete-sku").value = node.sku;
});

function renderSequence(nodes, activeIndex = -1) {
  const container = byId("traversal-results");
  container.replaceChildren();
  if (!nodes.length) {
    container.textContent = messages.traversalEmpty;
    return;
  }
  for (const [index, node] of nodes.entries()) {
    const chip = document.createElement("span");
    chip.className = `sequence-chip${index <= activeIndex ? " visited" : ""}`;
    chip.textContent = node.sku;
    chip.title = `${messages.visitLabel} ${index + 1}: ${node.name}`;
    container.append(chip);
    if (index < nodes.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "sequence-arrow";
      arrow.textContent = "→";
      arrow.setAttribute("aria-hidden", "true");
      container.append(arrow);
    }
  }
}

async function refresh() {
  const snapshot = await api.tree();
  const stats = snapshot.stats;
  currentSize = stats.size;
  byId("stat-size").textContent = number.format(stats.size);
  byId("nav-count").textContent = stats.size;
  byId("stat-height").textContent = number.format(stats.height);
  byId("stat-leaves").textContent = number.format(stats.leaves);
  byId("stat-quantity").textContent = number.format(stats.total_quantity);
  byId("balance-label").textContent = stats.balanced ? messages.balanced : messages.unbalanced;
  byId("tree-detail").textContent = messages.selectHint;
  byId("search-results").replaceChildren();
  byId("traversal-progress").textContent = "";
  view.render(snapshot.root);
  const traversal = await api.traverse(selectedOrder);
  renderSequence(traversal.nodes);
}

async function perform(action) {
  if (busy) return;
  busy = true;
  stopAnimation();
  const buttons = [...document.querySelectorAll("button")];
  buttons.forEach((button) => { button.disabled = true; });
  try {
    await action();
  } catch (error) {
    notify(messages.errors[error.message] || messages.errors.unknown_error, true);
  } finally {
    busy = false;
    buttons.forEach((button) => { button.disabled = false; });
  }
}

function validate(form) {
  if (form.checkValidity()) return true;
  notify(messages.invalidForm, true);
  const invalid = form.querySelector(":invalid");
  invalid?.focus();
  return false;
}

translate();
byId("traversal-description").textContent = messages.traversalDescriptions[selectedOrder];

for (const tab of document.querySelectorAll("[data-mode]")) {
  tab.addEventListener("click", () => {
    for (const other of document.querySelectorAll("[data-mode]")) {
      const active = other === tab;
      other.classList.toggle("active", active);
      other.setAttribute("aria-selected", String(active));
      byId(`${other.dataset.mode}-panel`).hidden = !active;
    }
  });
}

byId("add-panel").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!validate(event.currentTarget)) return;
  const product = {
    sku: Number(byId("product-sku").value),
    name: byId("product-name").value.trim(),
    quantity: Number(byId("product-quantity").value),
  };
  if (!product.name) { notify(messages.invalidForm, true); return; }
  perform(async () => {
    await api.add(product);
    byId("add-panel").reset();
    await refresh();
    view.highlight(product.sku, "is-selected");
    notify(messages.added);
  });
});

byId("delete-panel").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!validate(event.currentTarget)) return;
  const sku = Number(byId("delete-sku").value);
  perform(async () => {
    await api.remove(sku);
    byId("delete-panel").reset();
    await refresh();
    notify(messages.deleted);
  });
});

byId("search-panel").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!validate(event.currentTarget)) return;
  const query = byId("search-query").value.trim();
  if (!query) { notify(messages.invalidForm, true); return; }
  perform(async () => {
    const result = await api.search(query);
    view.clear();
    for (const sku of result.path) view.highlight(sku, "is-path");
    byId("search-results").replaceChildren();
    for (const node of result.matches) {
      view.highlight(node.sku, "is-selected");
      const item = document.createElement("p");
      const label = document.createElement("strong");
      label.textContent = `${node.sku} · ${node.name}`;
      const detail = document.createElement("small");
      detail.textContent = `${node.quantity} ${messages.unitLabel}`;
      item.append(label, detail);
      byId("search-results").append(item);
    }
    byId("tree-detail").textContent = `${messages.visitedLabel}: ${result.path.length} · ${messages.resultLabel}: ${result.matches.length}`;
    notify(result.matches.length ? messages.found : messages.notFound, !result.matches.length);
  });
});

function loadExample() {
  perform(async () => {
    await api.example(messages.demoProducts);
    await refresh();
    notify(messages.exampleLoaded);
  });
}

byId("example-button").addEventListener("click", () => {
  if (currentSize) byId("example-dialog").showModal();
  else loadExample();
});
byId("cancel-example").addEventListener("click", () => byId("example-dialog").close());
byId("confirm-example").addEventListener("click", () => {
  byId("example-dialog").close();
  loadExample();
});

for (const button of document.querySelectorAll("[data-order]")) {
  button.addEventListener("click", () => {
    selectedOrder = button.dataset.order;
    stopAnimation();
    view.clear();
    for (const other of document.querySelectorAll("[data-order]")) {
      other.classList.toggle("active", other === button);
      other.setAttribute("aria-pressed", String(other === button));
    }
    byId("traversal-description").textContent = messages.traversalDescriptions[selectedOrder];
    byId("traversal-progress").textContent = "";
    perform(async () => renderSequence((await api.traverse(selectedOrder)).nodes));
  });
}

byId("play-button").addEventListener("click", async () => {
  if (playing) { stopAnimation(); notify(messages.traversalStopped); return; }
  if (!currentSize) { notify(messages.noProducts, true); return; }
  const token = ++animationVersion;
  playing = true;
  byId("play-button").lastElementChild.textContent = messages.stop;
  try {
    const { nodes } = await api.traverse(selectedOrder);
    if (token !== animationVersion) return;
    view.clear();
    for (const [index, node] of nodes.entries()) {
      if (token !== animationVersion) return;
      view.visit(node.sku, index + 1);
      renderSequence(nodes, index);
      byId("traversal-progress").textContent = `${index + 1} ${messages.ofLabel} ${nodes.length}`;
      const duration = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 550;
      await new Promise((resolve) => setTimeout(resolve, duration));
    }
    if (token === animationVersion) { stopAnimation(); notify(messages.traversalDone); }
  } catch (error) {
    if (token === animationVersion) {
      stopAnimation();
      notify(messages.errors[error.message] || messages.errors.unknown_error, true);
    }
  }
});

byId("fit-button").addEventListener("click", () => view.fit());
perform(refresh);
