// RFHA-IES · panel del administrador general (HU-02).
import { $, announce, api, copyText, el, errorText, formatDate, setBusy, setMessage } from "/static/common.js";

const STATUS_LABEL = { PENDIENTE_APROBACION: "Pendiente de aprobación", ACTIVO: "Activo" };
let adminKey = "";
let lastKey = "";

const headers = () => ({ "X-Admin-Key": adminKey });

async function loadNodes() {
  setMessage("#list-error", "");
  const status = $("#status-filter").value;
  const result = await api("GET", `/api/v1/admin/nodes${status ? `?status=${status}` : ""}`, { headers: headers() });
  if (result.status !== 200) {
    $("#list-card").hidden = true;
    setMessage("#list-error", result.status === 403 ? "Clave de administrador incorrecta." : errorText(result, "No se pudieron cargar las solicitudes."));
    announce("No se pudieron cargar las solicitudes.");
    return;
  }
  renderNodes(result.data.nodes);
}

function renderNodes(nodes) {
  const body = $("#nodes-body");
  body.replaceChildren();
  nodes.forEach((node) => {
    const action = node.status === "PENDIENTE_APROBACION"
      ? el("button", { type: "button", class: "btn", "aria-label": `Aprobar ${node.name}`, onclick: (e) => approve(node, e.currentTarget) }, "Aprobar")
      : "—";
    body.append(el("tr", {},
      el("td", {}, el("code", {}, node.node_id)),
      el("td", {}, node.name),
      el("td", {}, node.nit),
      el("td", {}, node.domain),
      el("td", {}, `${STATUS_LABEL[node.status] || node.status} · ${formatDate(node.created_at)}`),
      el("td", {}, action),
    ));
  });
  $("#empty-msg").hidden = nodes.length > 0;
  $("#table-wrap").hidden = nodes.length === 0;
  $("#list-card").hidden = false;
  announce(`${nodes.length} nodos en la lista.`);
}

async function approve(node, button) {
  setBusy(button, true, "Aprobando…", "Aprobar");
  const result = await api("POST", `/api/v1/admin/nodes/${node.node_id}/approve`, { headers: headers() });
  if (result.status === 200) {
    lastKey = result.data.api_key;
    $("#key-node").textContent = result.data.node_id;
    $("#key-value").textContent = lastKey;
    $("#key-message").textContent = `${node.name}: ${result.data.message}`;
    $("#key-card").hidden = false;
    $("#key-result-title").setAttribute("tabindex", "-1");
    $("#key-result-title").focus();
    announce("Nodo aprobado. La API Key se muestra una sola vez.");
    await loadNodes();
  } else {
    setBusy(button, false, "", "Aprobar");
    setMessage("#list-error", errorText(result, "No se pudo aprobar el nodo."));
    announce("No se pudo aprobar el nodo.");
  }
}

$("#admin-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  adminKey = $("#admin-key").value.trim();
  if (!adminKey) {
    setMessage("#list-error", "Escribe la clave de administrador.");
    $("#admin-key").focus();
    return;
  }
  const button = $("#btn-load");
  setBusy(button, true, "Cargando…", "Cargar solicitudes");
  await loadNodes();
  setBusy(button, false, "", "Cargar solicitudes");
});

$("#btn-copy-key").addEventListener("click", () => copyText(lastKey));
$("#btn-hide-key").addEventListener("click", () => {
  lastKey = "";
  $("#key-value").textContent = "";
  $("#key-card").hidden = true;
});

$("#btn-download-pdf").addEventListener("click", async () => {
  const key = $("#admin-key").value.trim();
  if (!key) {
    setMessage("#list-error", "Escribe la clave de administrador para descargar el reporte.");
    $("#admin-key").focus();
    return;
  }
  const reportType = $("#admin-report-type") ? $("#admin-report-type").value : "general";
  const btn = $("#btn-download-pdf");
  setBusy(btn, true, "Generando PDF…", "⬇ Descargar Reporte PDF");
  try {
    const res = await fetch(`/api/v1/admin/reports/network-summary?type=${encodeURIComponent(reportType)}`, {
      headers: { "X-Admin-Key": key }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Error ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    a.href = url;
    a.download = `reporte-${reportType}-${today}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    announce("Reporte descargado correctamente.");
  } catch (e) {
    setMessage("#list-error", e.message || "Error al generar el reporte PDF.");
  } finally {
    setBusy(btn, false, "", "⬇ Descargar Reporte PDF");
  }
});
