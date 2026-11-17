// RFHA-IES · panel del nodo: carga de historiales (HU-03).
import { $, announce, api, errorText, setBusy, setMessage } from "/static/common.js";

// ---- Generador de datos de ejemplo aleatorios (nuevo en cada ejecución) ----
const FIRST_NAMES = ["Brayan","Laura","Sebastián","Valentina","Andrés","Camila","Diego","Mariana","Felipe","Daniela","Julián","Sofía","Miguel","Isabella","Carlos","Natalia","Samuel","Paula","Esteban","Sara"];
const LAST_NAMES = ["Acosta","Ríos","Gómez","Herrera","Martínez","López","Torres","Ramírez","García","Vargas","Moreno","Jiménez","Castro","Rojas","Peña","Suárez","Mendoza","Salazar","Ortiz","Silva"];
const PROGRAMS = ["Ingeniería en Telemática","Ingeniería de Sistemas y Computación","Ingeniería Electrónica","Ingeniería de Software","Ciencias de la Computación","Ingeniería en Redes","Matemáticas Aplicadas","Física Computacional"];
const COURSES = [
  { code:"165-301", name:"Sistemas Distribuidos", credits:3 },
  { code:"165-302", name:"Teoría General de Sistemas", credits:2 },
  { code:"165-330", name:"Seguridad Informática", credits:3 },
  { code:"2015167", name:"Cálculo Integral", credits:4 },
  { code:"2015168", name:"Álgebra Lineal", credits:3 },
  { code:"165-401", name:"Redes de Computadoras", credits:3 },
  { code:"165-402", name:"Bases de Datos Distribuidas", credits:3 },
  { code:"165-403", name:"Computación en la Nube", credits:2 },
  { code:"165-404", name:"Inteligencia Artificial", credits:3 },
  { code:"165-405", name:"Programación Funcional", credits:2 },
];
const STATUSES = ["ACTIVO","ACTIVO","ACTIVO","GRADUADO","RETIRADO"];
const SEMESTERS = ["2024-1","2024-2","2025-1","2025-2","2026-1","2026-2"];

function _rnd(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
function _rndInt(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function _rndFloat(min, max) { return Math.round((Math.random() * (max - min) + min) * 10) / 10; }
function _rndId(len) { return Array.from({length: len}, () => _rndInt(0,9)).join(""); }

function generateExample() {
  const count = _rndInt(2, 4);
  const usedIds = new Set();
  const records = [];
  for (let i = 0; i < count; i++) {
    let sid;
    do { sid = _rndId(_rndInt(10, 11)); } while (usedIds.has(sid));
    usedIds.add(sid);
    const doc = _rndId(10);
    const firstName = _rnd(FIRST_NAMES);
    const lastName1 = _rnd(LAST_NAMES);
    const lastName2 = _rnd(LAST_NAMES);
    const numCourses = _rndInt(2, 4);
    const shuffled = [...COURSES].sort(() => Math.random() - 0.5).slice(0, numCourses);
    const courses = shuffled.map((c, idx) => ({
      code: c.code,
      name: c.name,
      credits: c.credits,
      grade: idx === numCourses - 1 ? null : _rndFloat(1.5, 5.0),
      semester: _rnd(SEMESTERS),
    }));
    records.push({
      student_id: sid,
      document_number: doc,
      full_name: `${firstName} ${lastName1} ${lastName2}`,
      program: _rnd(PROGRAMS),
      academic_status: _rnd(STATUSES),
      password: `Demo-${doc.slice(-4)}-${_rndInt(10,99)}`,
      courses,
    });
  }
  return { records };
}

$("#btn-example").addEventListener("click", () => {
  $("#records-json").value = JSON.stringify(generateExample(), null, 2);
  setMessage("#sync-error", "");
  announce("Ejemplo de demostración generado.");
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
