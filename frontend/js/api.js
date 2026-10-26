/** Same-origin REST client. Error codes are translated by the controller. */
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new Error("network_error");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.code || "unknown_error");
  }
  return response.json();
}

export const api = {
  tree: () => request("/tree"),
  add: (product) => request("/nodes", { method: "POST", body: JSON.stringify(product) }),
  remove: (sku) => request(`/nodes/${encodeURIComponent(sku)}`, { method: "DELETE" }),
  search: (query) => request(`/search?${new URLSearchParams({ query })}`),
  traverse: (order) => request(`/traversal/${encodeURIComponent(order)}`),
  example: (products) => request("/example", { method: "POST", body: JSON.stringify(products) }),
};
