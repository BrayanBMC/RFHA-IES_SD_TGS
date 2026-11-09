// RFHA-IES · utilidades compartidas por las pantallas. JavaScript nativo, sin dependencias.
// Seguridad: el contenido dinámico siempre entra como texto (textContent) y las claves y tokens
// viven solo en la memoria de la página: no se guardan en el almacenamiento del navegador.

export const $ = (selector) => document.querySelector(selector);

export function announce(text) {
  $("#sr-status").textContent = text;
}

export function setMessage(selector, message) {
  const box = $(selector);
  box.hidden = !message;
  box.textContent = message || "";
}

// Crea un elemento con texto seguro. props: {class, type, ...atributos}; children: textos o nodos.
export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(props).forEach(([key, value]) => {
    if (key === "class") node.className = value;
    else if (key === "onclick") node.addEventListener("click", value);
    else node.setAttribute(key, value);
  });
  children.forEach((child) => node.append(child));
  return node;
}

// Llama a la API y devuelve {status, data}. Si no hay red devuelve status 0.
export async function api(method, url, { headers = {}, body } = {}) {
  try {
    const response = await fetch(url, {
      method,
      headers: { ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json().catch(() => ({}));
    return { status: response.status, data };
  } catch {
    return { status: 0, data: {} };
  }
}

// Texto legible de un error de la API (detail puede ser texto o la lista de FastAPI).
export function errorText(result, fallback) {
  if (result.status === 0) return "No se pudo conectar con el servidor. Revisa tu conexión; lo que escribiste se conserva.";
  const detail = result.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .slice(0, 5)
      .map((item) => `${(item.loc || []).slice(1).join(" › ") || "dato"}: ${item.msg}`)
      .join(" · ");
  }
  return fallback;
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    announce("Copiado al portapapeles.");
  } catch {
    announce("No se pudo copiar. Selecciona el texto manualmente.");
  }
}

export function formatDate(iso) {
  return new Date(iso).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}

export function setBusy(button, busy, busyText, idleText) {
  button.disabled = busy;
  button.textContent = busy ? busyText : idleText;
}
