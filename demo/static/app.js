// RFHA-IES · interfaz de la demo. JavaScript nativo (módulo ES), sin dependencias.
// Seguridad: todo el contenido dinámico se inserta con textContent (nunca innerHTML).

const $ = (selector) => document.querySelector(selector);
const API = "/api/v1/federated/academic-history/";
const STEPS = ["token", "signature", "owner", "lookup"];
const STATE_LABEL = { idle: "Pendiente", pass: "Aprobado", fail: "Rechazado", skipped: "Omitido" };
const ID_PATTERN = /^[0-9A-Za-z_-]{1,32}$/;

const els = {
  form: $("#query-form"),
  student: $("#student-id"),
  studentError: $("#student-error"),
  token: $("#token"),
  tools: $("#demo-tools"),
  submit: $("#btn-submit"),
  empty: $("#result-empty"),
  body: $("#result-body"),
  badge: $("#http-badge"),
  message: $("#http-message"),
  card: $("#student-card"),
  json: $("#json-view"),
  status: $("#sr-status"),
};

let lastRequest = null;

function announce(text) {
  els.status.textContent = text;
}

function setPipeline(failedIndex) {
  // failedIndex: null = reiniciar, -1 = todo aprobado, n = falló el paso n
  STEPS.forEach((step, index) => {
    let state = "idle";
    if (failedIndex === -1) state = "pass";
    else if (failedIndex !== null) state = index < failedIndex ? "pass" : index === failedIndex ? "fail" : "skipped";
    const item = document.querySelector(`[data-step="${step}"]`);
    item.dataset.state = state;
    item.querySelector(".state").textContent = STATE_LABEL[state];
  });
}

function failedStep(status, detail) {
  if (status === 200) return -1;
  if (status === 404) return 3;
  if (status === 403) {
    const text = String(detail).toLowerCase();
    if (text.includes("falta")) return 0;
    if (text.includes("no autoriza")) return 2;
    return 1; // expirado o inválido
  }
  return null;
}

function setStudentError(message) {
  els.studentError.hidden = !message;
  els.studentError.textContent = message || "";
  els.student.setAttribute("aria-invalid", message ? "true" : "false");
}

function row(...cells) {
  const tr = document.createElement("tr");
  cells.forEach(({ text, num }) => {
    const td = document.createElement("td");
    td.textContent = text;
    if (num) td.className = "num";
    tr.append(td);
  });
  return tr;
}

function renderStudent(data) {
  $("#student-name").textContent = data.full_name;
  $("#student-university").textContent = data.university;
  $("#student-program").textContent = data.program;
  $("#student-gpa").textContent = Number(data.gpa).toLocaleString("es-CO", { minimumFractionDigits: 2 });
  const body = $("#courses-body");
  body.replaceChildren(
    ...data.courses.map((course) =>
      row({ text: course.code }, { text: course.name }, { text: Number(course.grade).toLocaleString("es-CO", { minimumFractionDigits: 1 }), num: true }),
    ),
  );
  els.card.hidden = false;
}

function showResult({ status, kind, message, payload }) {
  els.empty.hidden = true;
  els.body.hidden = false;
  els.badge.textContent = status ? `HTTP ${status}` : "Sin conexión";
  els.badge.dataset.kind = kind;
  els.message.textContent = message;
  els.card.hidden = true;
  if (kind === "ok" && payload?.data) renderStudent(payload.data);
  els.json.textContent = JSON.stringify(payload ?? {}, null, 2);
}

async function query(event) {
  event.preventDefault();
  const studentId = els.student.value.trim();
  if (!ID_PATTERN.test(studentId)) {
    setStudentError("Escribe un código válido: solo letras, números, guion o guion bajo (máximo 32).");
    els.student.focus();
    return;
  }
  setStudentError("");
  const token = els.token.value.trim();
  const headers = token ? { "X-Student-Consent-Token": token } : {};
  lastRequest = { studentId, token };

  els.submit.disabled = true;
  els.submit.textContent = "Consultando…";
  setPipeline(null);
  try {
    const response = await fetch(API + encodeURIComponent(studentId), { headers });
    const payload = await response.json().catch(() => ({}));
    const step = failedStep(response.status, payload.detail);
    setPipeline(step);
    const ok = response.status === 200;
    showResult({
      status: response.status,
      kind: ok ? "ok" : "bad",
      message: ok ? "Acceso concedido: el estudiante autorizó la consulta." : payload.detail || "La solicitud no pudo completarse.",
      payload,
    });
    announce(ok ? "Consulta exitosa. Expediente mostrado." : `Consulta rechazada. ${payload.detail || ""}`);
  } catch {
    setPipeline(null);
    showResult({ status: 0, kind: "bad", message: "No se pudo conectar con el servidor. Verifica que la API esté en ejecución.", payload: {} });
    announce("Error de conexión.");
  } finally {
    els.submit.disabled = false;
    els.submit.textContent = "Consultar expediente";
  }
}

async function mintToken(expired) {
  const studentId = els.student.value.trim();
  if (!ID_PATTERN.test(studentId)) {
    setStudentError("Escribe un código válido antes de generar el token.");
    els.student.focus();
    return;
  }
  setStudentError("");
  try {
    const response = await fetch("/api/v1/demo/consent-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, expired }),
    });
    if (!response.ok) throw new Error(String(response.status));
    const { token } = await response.json();
    els.token.value = token;
    announce(expired ? "Token expirado generado." : "Token válido generado.");
  } catch {
    announce("No se pudo generar el token.");
  }
}

async function copyCurl() {
  if (!lastRequest) return;
  const header = lastRequest.token ? ` -H "X-Student-Consent-Token: ${lastRequest.token}"` : "";
  const command = `curl -i${header} "${location.origin}${API}${encodeURIComponent(lastRequest.studentId)}"`;
  try {
    await navigator.clipboard.writeText(command);
    announce("Comando curl copiado al portapapeles.");
  } catch {
    announce("No se pudo copiar. Selecciona el texto manualmente.");
  }
}

async function init() {
  const local = ["127.0.0.1", "localhost", "[::1]"].includes(location.hostname);
  $("#env-name").textContent = local ? "Local" : "Nube (AWS)";
  els.form.addEventListener("submit", query);
  $("#btn-valid").addEventListener("click", () => mintToken(false));
  $("#btn-expired").addEventListener("click", () => mintToken(true));
  $("#btn-clear").addEventListener("click", () => {
    els.token.value = "";
    announce("Token borrado.");
  });
  $("#btn-curl").addEventListener("click", copyCurl);
  try {
    const config = await (await fetch("/api/v1/demo/config")).json();
    els.tools.hidden = !config.demo_mode;
  } catch {
    els.tools.hidden = true;
  }
}

init();
