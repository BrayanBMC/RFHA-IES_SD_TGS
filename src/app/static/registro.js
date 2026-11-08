// RFHA-IES · formulario de registro de nodo (HU-01). JavaScript nativo, sin dependencias.
// Seguridad: todo el contenido dinámico se inserta con textContent (nunca innerHTML).

const $ = (selector) => document.querySelector(selector);
const ENDPOINT = "/api/v1/nodes/register";

// Mismas reglas que el servidor (src/app/models.py). El servidor siempre vuelve a validar.
const RULES = {
  nit: {
    test: (v) => /^\d{6,12}(-\d)?$/.test(v),
    message: "Escribe entre 6 y 12 dígitos, con dígito de verificación opcional. Ejemplo: 899999063-3.",
  },
  name: {
    test: (v) => v.length >= 3 && v.length <= 200,
    message: "Escribe el nombre oficial de la institución (entre 3 y 200 caracteres).",
  },
  domain: {
    test: (v) => /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(v) && v.length <= 253,
    message: "Escribe solo el dominio, sin «https://» ni rutas. Ejemplo: unal.edu.co.",
  },
  contact_email: {
    test: (v) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v) && v.length <= 254,
    message: "Escribe un correo válido. Ejemplo: admisiones@unal.edu.co.",
  },
};
const FIELD_ERROR_ID = { nit: "nit-error", name: "name-error", domain: "domain-error", contact_email: "email-error" };

const form = $("#register-form");
const submit = $("#btn-submit");
let lastNodeId = "";

function announce(text) {
  $("#sr-status").textContent = text;
}

function setFieldError(field, message) {
  const input = $(`#${field}`);
  const error = $(`#${FIELD_ERROR_ID[field]}`);
  error.hidden = !message;
  error.textContent = message || "";
  input.setAttribute("aria-invalid", message ? "true" : "false");
}

function setFormError(message) {
  const box = $("#form-error");
  box.hidden = !message;
  box.textContent = message || "";
}

function clearErrors() {
  Object.keys(RULES).forEach((field) => setFieldError(field, ""));
  setFormError("");
}

function readValues() {
  const values = {
    nit: $("#nit").value.trim(),
    name: $("#name").value.trim(),
    domain: $("#domain").value.trim().toLowerCase(),
    contact_email: $("#contact_email").value.trim().toLowerCase(),
  };
  return values;
}

function validate(values) {
  let firstInvalid = null;
  Object.entries(RULES).forEach(([field, rule]) => {
    const valid = rule.test(values[field]);
    setFieldError(field, valid ? "" : rule.message);
    if (!valid && !firstInvalid) firstInvalid = field;
  });
  if (firstInvalid) $(`#${firstInvalid}`).focus();
  return !firstInvalid;
}

function showSuccess(values, result) {
  lastNodeId = result.node_id;
  $("#node-id").textContent = result.node_id;
  $("#success-message").textContent = result.message;
  $("#out-name").textContent = values.name;
  $("#out-nit").textContent = values.nit;
  $("#out-domain").textContent = values.domain;
  $("#out-email").textContent = values.contact_email;
  $("#form-card").hidden = true;
  $("#success-card").hidden = false;
  $("#success-title").setAttribute("tabindex", "-1");
  $("#success-title").focus();
  announce(`Solicitud enviada. Código del nodo ${result.node_id}. Estado: pendiente de aprobación.`);
}

// El servidor responde 422 con una lista de errores; los asociamos a su campo.
function showServerValidation(detail) {
  let shown = false;
  (Array.isArray(detail) ? detail : []).forEach((item) => {
    const field = item.loc?.[1];
    if (field in RULES) {
      setFieldError(field, RULES[field].message);
      shown = true;
    }
  });
  if (!shown) setFormError("Los datos enviados no son válidos. Revísalos e inténtalo de nuevo.");
}

async function onSubmit(event) {
  event.preventDefault();
  clearErrors();
  const values = readValues();
  if (!validate(values)) {
    announce("Hay campos por corregir.");
    return;
  }

  submit.disabled = true;
  submit.textContent = "Enviando…";
  try {
    const response = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    const payload = await response.json().catch(() => ({}));
    if (response.status === 201) {
      showSuccess(values, payload);
    } else if (response.status === 409) {
      setFieldError("nit", "Ya existe una solicitud o un nodo con este NIT.");
      $("#nit").focus();
      announce("Ya existe una solicitud con este NIT.");
    } else if (response.status === 422) {
      showServerValidation(payload.detail);
      announce("Hay campos por corregir.");
    } else {
      setFormError("No se pudo registrar la solicitud. Inténtalo de nuevo en unos minutos.");
    }
  } catch {
    setFormError("No se pudo conectar con el servidor. Revisa tu conexión; lo que escribiste se conserva.");
    announce("Error de conexión.");
  } finally {
    submit.disabled = false;
    submit.textContent = "Solicitar registro";
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(lastNodeId);
    announce("Código copiado al portapapeles.");
  } catch {
    announce("No se pudo copiar. Selecciona el código manualmente.");
  }
}

function again() {
  form.reset();
  clearErrors();
  $("#success-card").hidden = true;
  $("#form-card").hidden = false;
  $("#nit").focus();
}

form.addEventListener("submit", onSubmit);
$("#btn-copy").addEventListener("click", copyCode);
$("#btn-again").addEventListener("click", again);
