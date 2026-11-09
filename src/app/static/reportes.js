// RFHA-IES · Generación y descarga de reportes PDF.
import { $, announce, setMessage, setBusy } from "/static/common.js";

const form = $("#report-form");
const btn = $("#btn-download");
const statusMsg = $("#status-msg");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const adminKey = $("#admin-key").value.trim();
  const reportType = $("#report-type") ? $("#report-type").value : "general";

  if (!adminKey) {
    setMessage("#error-msg", "Ingresa la clave de administrador para generar el reporte.");
    $("#admin-key").focus();
    return;
  }

  setMessage("#error-msg", "");
  setBusy(btn, true, "Generando PDF…", "Generar y Descargar Reporte");
  if (statusMsg) statusMsg.hidden = false;

  try {
    const response = await fetch(`/api/v1/admin/reports/network-summary?type=${encodeURIComponent(reportType)}`, {
      method: "GET",
      headers: { "X-Admin-Key": adminKey },
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const detail = data.detail || (response.status === 403 ? "Clave de administrador incorrecta." : `Error ${response.status}`);
      throw new Error(detail);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    anchor.href = url;
    anchor.download = `reporte-${reportType}-${today}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);

    announce("Reporte PDF descargado correctamente.");
  } catch (err) {
    setMessage("#error-msg", err.message || "Error al generar el reporte PDF.");
    announce("Error al generar el reporte PDF.");
  } finally {
    setBusy(btn, false, "", "Generar y Descargar Reporte");
    if (statusMsg) statusMsg.hidden = true;
  }
});
