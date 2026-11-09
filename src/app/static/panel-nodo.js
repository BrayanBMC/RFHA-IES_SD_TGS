// RFHA-IES · panel del nodo: carga de historiales (HU-03).
import { $, announce, api, errorText, setBusy, setMessage } from "/static/common.js";

// Datos FICTICIOS de ejemplo.
const EXAMPLE = {
  records: [
    {
      student_id: "20262678029",
      document_number: "1012345678",
      full_name: "Brayan Acosta Parrado",
      program: "Ingeniería en Telemática",
      academic_status: "ACTIVO",
      password: "Clave-2026-A",
      courses: [
        { code: "165-301", name: "Sistemas Distribuidos", credits: 3, grade: 4.8, semester: "2026-1" },
        { code: "165-302", name: "Teoría General de Sistemas", credits: 2, grade: 4.5, semester: "2026-1" },
        { code: "165-330", name: "Seguridad Informática", credits: 3, grade: null, semester: "2026-2" },
      ],
    },
    {
      student_id: "20251234501",
      document_number: "1098765432",
      full_name: "Laura Camila Ríos Herrera",
      program: "Ingeniería de Sistemas y Computación",
      academic_status: "ACTIVO",
      password: "Clave-2026-B",
      courses: [
        { code: "2015167", name: "Cálculo Integral", credits: 4, grade: 2.6, semester: "2024-2" },
        { code: "2015167", name: "Cálculo Integral", credits: 4, grade: 3.4, semester: "2025-1" },
      ],
    },
  ],
};

$("#btn-example").addEventListener("click", () => {
  $("#records-json").value = JSON.stringify(EXAMPLE, null, 2);
  setMessage("#sync-error", "");
  announce("Ejemplo cargado.");
});

$("#sync-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#sync-error", "");
  $("#sync-result").hidden = true;

  const apiKey = $("#api-key").value.trim();
  if (!apiKey) {
    setMessage("#sync-error", "Escribe la API Key del nodo.");
    $("#api-key").focus();
    return;
  }
  let payload;
  try {
    payload = JSON.parse($("#records-json").value);
  } catch {
    setMessage("#sync-error", "El JSON no es válido. Revisa comas y comillas, o pulsa «Cargar ejemplo».");
    $("#records-json").focus();
    return;
  }

  const button = $("#btn-sync");
  setBusy(button, true, "Sincronizando…", "Sincronizar historiales");
  const result = await api("POST", "/api/v1/node/sync-records", { headers: { "X-Node-API-Key": apiKey }, body: payload });
  setBusy(button, false, "", "Sincronizar historiales");

  if (result.status === 200) {
    $("#out-node").textContent = result.data.node_id;
    $("#out-received").textContent = result.data.received;
    $("#out-created").textContent = result.data.created;
    $("#out-updated").textContent = result.data.updated;
    $("#sync-result").hidden = false;
    $("#sync-result-title").setAttribute("tabindex", "-1");
    $("#sync-result-title").focus();
    announce(`Sincronización terminada: ${result.data.created} nuevos y ${result.data.updated} actualizados.`);
  } else {
    const message = result.status === 403 ? "API Key incorrecta o nodo no activo." : errorText(result, "No se pudo sincronizar.");
    setMessage("#sync-error", message);
    announce("La sincronización falló.");
  }
});
