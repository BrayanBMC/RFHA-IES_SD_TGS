// RFHA-IES · portal del estudiante: generar (HU-04), ver y revocar (HU-05) autorizaciones.
// La cédula y la clave solo viven en esta página mientras está abierta (no se guardan en el navegador).
import { $, announce, api, copyText, el, errorText, formatDate, setBusy, setMessage } from "/static/common.js";

let credentials = null;
let lastToken = "";

async function loadTokens() {
  const result = await api("POST", "/api/v1/student/tokens/list", { body: credentials });
  if (result.status !== 200) return result;
  const body = $("#tokens-body");
  body.replaceChildren();
  result.data.tokens.forEach((token) => {
    const action = token.status === "ACTIVO"
      ? el("button", { type: "button", class: "btn", "aria-label": `Revocar autorización a ${token.audience_name || token.audience}`, onclick: (e) => revoke(token, e.currentTarget) }, "Revocar")
      : "—";
    body.append(el("tr", {},
      el("td", {}, token.audience_name || token.audience),
      el("td", {}, formatDate(token.issued_at)),
      el("td", {}, formatDate(token.expires_at)),
      el("td", {}, el("span", { class: "chip", "data-kind": token.status === "ACTIVO" ? "ACTIVO" : "RETIRADO" }, token.status === "ACTIVO" ? "Activo" : token.status === "REVOCADO" ? "Revocado" : "Expirado")),
      el("td", {}, action),
    ));
  });
  $("#empty-msg").hidden = result.data.tokens.length > 0;
  $("#table-wrap").hidden = result.data.tokens.length === 0;
  return result;
}

async function loadUniversities() {
  const result = await api("GET", "/api/v1/nodes/active");
  const select = $("#target");
  select.replaceChildren();
  const nodes = result.data.nodes || [];
  nodes.forEach((node) => select.append(el("option", { value: node.node_id }, `${node.name} (${node.node_id})`)));
  if (!nodes.length) select.append(el("option", { value: "" }, "No hay universidades activas"));
  $("#btn-token").disabled = nodes.length === 0;
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#login-error", "");
  const candidate = { document_number: $("#document_number").value.trim(), password: $("#password").value };
  if (!/^\d{5,15}$/.test(candidate.document_number) || !candidate.password) {
    setMessage("#login-error", "Escribe tu número de documento (solo dígitos) y tu clave.");
    $("#document_number").focus();
    return;
  }
  credentials = candidate;
  const button = $("#btn-login");
  setBusy(button, true, "Ingresando…", "Ingresar");
  const result = await loadTokens();
  setBusy(button, false, "", "Ingresar");
  if (result.status !== 200) {
    credentials = null;
    setMessage("#login-error", errorText(result, "No se pudo ingresar."));
    announce("No se pudo ingresar.");
    return;
  }
  await loadUniversities();
  $("#password").value = "";
  $("#login-card").hidden = true;
  $("#portal").hidden = false;
  $("#new-title").setAttribute("tabindex", "-1");
  $("#new-title").focus();
  announce("Ingreso correcto.");
});

$("#token-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#new-error", "");
  const target = $("#target").value;
  if (!target) return;
  const button = $("#btn-token");
  setBusy(button, true, "Generando…", "Generar autorización");
  const result = await api("POST", "/api/v1/student/auth-token", { body: { ...credentials, target_node_id: target } });
  setBusy(button, false, "", "Generar autorización");
  if (result.status === 201) {
    lastToken = result.data.student_auth_token;
    $("#token-value").value = lastToken;
    $("#token-summary").textContent = `Autorizada: ${$("#target").selectedOptions[0].textContent}. Vence el ${formatDate(result.data.expires_at)}.`;
    $("#token-result").hidden = false;
    announce("Autorización creada.");
    await loadTokens();
  } else {
    setMessage("#new-error", errorText(result, "No se pudo generar la autorización."));
    announce("No se pudo generar la autorización.");
  }
});

async function revoke(token, button) {
  setBusy(button, true, "Revocando…", "Revocar");
  const result = await api("POST", `/api/v1/student/tokens/${token.jti}/revoke`, { body: credentials });
  if (result.status === 200) {
    announce("Autorización revocada.");
    await loadTokens();
  } else {
    setBusy(button, false, "", "Revocar");
    setMessage("#new-error", errorText(result, "No se pudo revocar."));
  }
}

$("#btn-copy-token").addEventListener("click", () => copyText(lastToken));
$("#btn-logout").addEventListener("click", () => {
  credentials = null;
  lastToken = "";
  $("#token-value").value = "";
  $("#token-result").hidden = true;
  $("#portal").hidden = true;
  $("#login-card").hidden = false;
  $("#document_number").focus();
  announce("Sesión cerrada.");
});
