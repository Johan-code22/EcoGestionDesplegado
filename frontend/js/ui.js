/**
 * ui.js — Helpers de UI (render, alertas, limpieza de formularios)
 * Principio SOLID: Single Responsibility — solo manipula el DOM
 */

const UI = {
  showAlert(id, type, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = `alert alert-${type} show`;
    el.textContent = (type === "success" ? "✅ " : "❌ ") + msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove("show"), 4500);
  },

  fieldError(id, msg) {
    const el = document.getElementById(id);
    if (el) el.textContent = msg;
  },

  clearError(id) {
    const el = document.getElementById(id);
    if (el) el.textContent = "";
  },

  /** Limpia inputs por id y resetea selects */
  limpiarForm(inputIds = [], ...selectIds) {
    inputIds.forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });
    selectIds.forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });
  },

  badgeHtml(tipo) {
    const map = {
      "Orgánico": "badge-organico",
      "Reciclable": "badge-reciclable",
      "No Aprovechable": "badge-no-aprove",
      "Especial": "badge-especial",
      "administrador": "badge-admin",
      "operador": "badge-operador",
    };
    const cls = map[tipo] || "badge-operador";
    return `<span class="badge ${cls}">${tipo}</span>`;
  },

  fmtNum(n) {
    return typeof n === "number" ? n.toFixed(1) : "—";
  },

  renderTable(tbodyId, rows) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    tbody.innerHTML = rows.join("");
  },

  updateProgressBar(barId, labelId, pct) {
    const bar = document.getElementById(barId);
    const lbl = document.getElementById(labelId);
    if (bar) bar.style.width = pct + "%";
    if (lbl) lbl.textContent = pct + "%";
  },

  setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  },
};

// ── Helpers globales usados en el HTML ────────────────────────────────────────

function calcTotal() {
  const v = ["q-organico","q-reciclable","q-noaprove","q-especial"]
    .map(id => parseFloat(document.getElementById(id).value) || 0);
  document.getElementById("q-total-calc").textContent = v.reduce((a,b)=>a+b,0).toFixed(2) + " t";
}

function limpiarCantidades() {
  ["q-organico","q-reciclable","q-noaprove","q-especial"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("q-total-calc").textContent = "0.00 t";
}

function toggleMenu() {
  document.getElementById("sidebar").classList.toggle("open");
}
