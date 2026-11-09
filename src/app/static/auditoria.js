// RFHA-IES · Bitácora de auditoría (HU-09).
import { $, announce, api, el, errorText, setBusy } from "/static/common.js";

const formatDate = (iso) => {
  try {
    return new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "medium" });
  } catch {
    return iso;
  }
};

const credType = $("#cred-type");
const credLabel = $("#cred-label");
const credValue = $("#cred-value");

credType.addEventListener("change", () => {
  if (credType.value === "admin") {
    credLabel.textContent = "Clave de administrador (ADMIN_KEY)";
    credValue.placeholder = "Pega tu clave de administrador";
  } else {
    credLabel.textContent = "API Key de tu universidad (rfha_...)";
    credValue.placeholder = "rfha_...";
  }
});

function showStatus(status, message) {
  const row = $("#status-row");
  const chip = $("#status-chip");
  row.hidden = false;
  chip.textContent = status === 0 ? "Sin conexión" : `HTTP ${status}`;
  chip.dataset.kind = status === 200 ? "ok" : "bad";
  $("#status-msg").textContent = message;
}

$("#audit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const cred = credValue.value.trim();
  if (!cred) {
    showStatus(422, "Ingresa tu credencial para consultar la bitácora.");
    return;
  }

  const headers = {};
  if (credType.value === "admin") {
    headers["X-Admin-Key"] = cred;
  } else {
    headers["X-Node-API-Key"] = cred;
  }

  const limit = $("#limit-value").value;
  const button = $("#btn-load");
  setBusy(button, true, "Cargando…", "Cargar bitácora");

  const result = await api("GET", `/api/v1/audit/logs?limit=${limit}`, { headers });
  setBusy(button, false, "", "Cargar bitácora");

  const resultBox = $("#result-box");
  const tableWrap = $("#table-wrap");
  const tbody = $("#audit-body");
  resultBox.hidden = false;

  if (result.status === 200) {
    $("#status-row").hidden = true;
    const logs = result.data.logs || [];
    $("#count-badge").textContent = `${logs.length} eventos`;

    if (logs.length === 0) {
      tableWrap.hidden = true;
      showStatus(200, "No hay eventos registrados aún en la bitácora.");
      return;
    }

    tableWrap.hidden = false;
    tbody.replaceChildren();

    logs.forEach((log) => {
      const outcomeBadge = el("span", {
        class: "badge",
        "data-kind": log.outcome === "SUCCESS" ? "ok" : log.outcome === "DENIED" ? "bad" : "warn",
      }, log.outcome);

      const sourceBadge = el("span", {
        class: "badge",
        "data-kind": log.data_source === "Primary" ? "ok" : log.data_source === "Replica" ? "warn" : "neutral",
      }, log.data_source || "None");

      tbody.append(el("tr", {},
        el("td", {}, formatDate(log.timestamp)),
        el("td", {}, el("code", {}, log.consulting_node_id || "—")),
        el("td", {}, log.target_student_id || "—"),
        el("td", {}, el("code", {}, log.origin_node_id || "—")),
        el("td", {}, outcomeBadge),
        el("td", {}, sourceBadge),
        el("td", {}, log.reason || "—"),
      ));
    });

    announce(`Se cargaron ${logs.length} eventos de auditoría.`);
  } else {
    tableWrap.hidden = true;
    $("#count-badge").textContent = "0 eventos";
    showStatus(result.status, errorText(result, "No se pudo consultar la bitácora."));
    announce("Error al cargar la bitácora.");
  }
});
