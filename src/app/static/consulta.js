// RFHA-IES · consulta federada del historial (HU-06 y HU-07).
import { $, announce, api, el, errorText, setBusy } from "/static/common.js";

const grade = (value) => (value === null ? "En curso" : value.toLocaleString("es-CO", { minimumFractionDigits: 1 }));

function showResult(status, message) {
  const chip = $("#status-chip");
  chip.textContent = status === 0 ? "Sin conexión" : `HTTP ${status}`;
  chip.dataset.kind = status === 200 ? "ok" : "bad";
  $("#result-message").textContent = message;
  $("#record").hidden = status !== 200;
  $("#result").hidden = false;
  $("#r-title").setAttribute("tabindex", "-1");
  $("#r-title").focus();
}

function showRecord(body) {
  const d = body.data;
  $("#out-name").textContent = d.full_name;
  $("#out-program").textContent = d.program;
  $("#out-node").textContent = d.node_id;
  $("#out-source").textContent = body.data_source === "Primary"
    ? "Nodo primario de origen (Primary)"
    : "Réplica autorizada de respaldo (Replica)";
  $("#out-gpa").textContent = d.gpa === null ? "—" : d.gpa.toLocaleString("es-CO", { minimumFractionDigits: 2 });
  $("#out-credits").textContent = d.credits_completed;
  const rows = $("#courses-body");
  rows.replaceChildren();
  d.courses.forEach((c) => rows.append(el("tr", {},
    el("td", {}, c.code), el("td", {}, c.name), el("td", {}, c.semester),
    el("td", { class: "num" }, String(c.credits)), el("td", { class: "num" }, grade(c.grade)), el("td", {}, c.status),
  )));
}

$("#query-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const studentId = $("#student-id").value.trim();
  if (!/^\d{6,15}$/.test(studentId)) {
    showResult(422, "Escribe el código del estudiante (solo dígitos).");
    return;
  }
  const headers = { "X-Node-API-Key": $("#api-key").value.trim() };
  const token = $("#token").value.trim();
  if (token) headers["X-Student-Consent-Token"] = token;
  if ($("#simulate-down") && $("#simulate-down").checked) {
    headers["X-Simulate-Down"] = "true";
  }

  const button = $("#btn-query");
  setBusy(button, true, "Consultando…", "Consultar historial");
  const result = await api("GET", `/api/v1/federated/academic-history/${studentId}`, { headers });
  setBusy(button, false, "", "Consultar historial");

  if (result.status === 200) {
    showRecord(result.data);
    showResult(200, "Consulta autorizada: el estudiante dio su permiso.");
    announce("Consulta autorizada.");
  } else {
    showResult(result.status, errorText(result, "No se pudo consultar."));
    announce("La consulta fue rechazada.");
  }
});
