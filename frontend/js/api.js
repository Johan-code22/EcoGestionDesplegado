/**
 * api.js — Cliente HTTP para la API REST de EcoGestión
 * Principio SOLID: Single Responsibility + Dependency Inversion
 * Todas las llamadas a FastAPI pasan por este módulo.
 */

const BASE_URL = "http://127.0.0.1:8000/api";

// ── Estado del rol activo ─────────────────────────────────────────────────────
let currentUserId = 1;  // 1 = Admin por defecto

function setCurrentUser(id) { currentUserId = id; }

// ── Utilitario fetch con manejo de errores ────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.detail
      ? (Array.isArray(data.detail) ? data.detail.map(e => e.msg).join("; ") : data.detail)
      : "Error en el servidor";
    throw new Error(msg);
  }
  return data;
}

// ── Health check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    await apiFetch("/health");
    return true;
  } catch { return false; }
}

// ════════════════════════════════════════════════════════════════════
// API — operaciones CRUD (cada función: una responsabilidad)
// ════════════════════════════════════════════════════════════════════

const API = {

  // ── SCRUM-7: Diagnósticos ────────────────────────────────────────
  async guardarDiagnostico() {
    const anio     = document.getElementById("d-anio").value;
    const periodo  = document.getElementById("d-periodo").value;
    const organico = parseFloat(document.getElementById("d-organico").value) || 0;
    const reciclable = parseFloat(document.getElementById("d-reciclable").value) || 0;
    const no_aprovechable = parseFloat(document.getElementById("d-noaprove").value) || 0;
    const especial = parseFloat(document.getElementById("d-especial").value) || 0;
    const observaciones = document.getElementById("d-obs").value;

    // Validación frontend (SRP: validar ≠ enviar)
    let valid = true;
    if (!anio) { UI.fieldError("e-d-anio", "El año es obligatorio"); valid = false; }
    else UI.clearError("e-d-anio");
    if (!periodo) { UI.fieldError("e-d-periodo", "El período es obligatorio"); valid = false; }
    else UI.clearError("e-d-periodo");
    if (valid && organico + reciclable + no_aprovechable + especial === 0) {
      UI.showAlert("alert-diag", "error", "Ingrese al menos una cantidad de residuos.");
      return;
    }
    if (!valid) { UI.showAlert("alert-diag", "error", "Corrija los campos obligatorios."); return; }

    try {
      const diag = await apiFetch("/diagnosticos", {
        method: "POST",
        body: JSON.stringify({ anio: parseInt(anio), periodo, organico, reciclable, no_aprovechable, especial, observaciones, usuario_id: currentUserId }),
      });
      UI.showAlert("alert-diag", "success", "Diagnóstico registrado correctamente.");
      UI.limpiarForm(["d-anio","d-organico","d-reciclable","d-noaprove","d-especial","d-obs"], "d-periodo");
      loadDiagnosticos();
      loadMetasDiagSelects();
    } catch (e) {
      UI.showAlert("alert-diag", "error", e.message);
    }
  },

  async getDiagnosticos() { return apiFetch("/diagnosticos"); },

  // ── SCRUM-8: Metas ────────────────────────────────────────────────
  async guardarMeta() {
    const periodo      = document.getElementById("m-periodo").value;
    const tipo_residuo = document.getElementById("m-tipo").value;
    const valor_meta   = parseFloat(document.getElementById("m-valor").value);
    const indicador    = document.getElementById("m-indicador").value;
    const diag_id      = document.getElementById("m-diag").value;

    let valid = true;
    if (!periodo) { UI.fieldError("e-m-periodo", "Campo obligatorio"); valid = false; } else UI.clearError("e-m-periodo");
    if (!tipo_residuo) { UI.fieldError("e-m-tipo", "Seleccione un tipo"); valid = false; } else UI.clearError("e-m-tipo");
    if (isNaN(valor_meta) || valor_meta < 0) { UI.fieldError("e-m-valor", "Valor numérico válido requerido"); valid = false; } else UI.clearError("e-m-valor");
    if (!valid) { UI.showAlert("alert-meta", "error", "Corrija los campos obligatorios."); return; }

    try {
      await apiFetch("/metas", {
        method: "POST",
        body: JSON.stringify({ periodo, tipo_residuo, valor_meta, indicador, diagnostico_id: diag_id ? parseInt(diag_id) : null, usuario_id: currentUserId }),
      });
      UI.showAlert("alert-meta", "success", "Meta registrada y asociada al diagnóstico base.");
      UI.limpiarForm(["m-valor","m-indicador"], "m-periodo", "m-tipo", "m-diag");
      loadMetas();
    } catch (e) {
      UI.showAlert("alert-meta", "error", e.message);
    }
  },

  async getMetas() { return apiFetch("/metas"); },

  // ── SCRUM-9: Clasificaciones ──────────────────────────────────────
  async guardarClasificacion() {
    const tipo_residuo       = document.getElementById("c-tipo").value;
    const fecha_recoleccion  = document.getElementById("c-fecha").value;
    const ruta_zona          = document.getElementById("c-ruta").value;
    const vehiculo           = document.getElementById("c-vehiculo").value;
    const observaciones      = document.getElementById("c-obs").value;

    let valid = true;
    if (!tipo_residuo) { UI.fieldError("e-c-tipo", "El tipo de residuo es obligatorio"); valid = false; } else UI.clearError("e-c-tipo");
    if (!fecha_recoleccion) { UI.fieldError("e-c-fecha", "La fecha es obligatoria"); valid = false; } else UI.clearError("e-c-fecha");
    if (!valid) { UI.showAlert("alert-clas", "error", "Corrija los campos obligatorios."); return; }

    try {
      await apiFetch("/clasificaciones", {
        method: "POST",
        body: JSON.stringify({ tipo_residuo, fecha_recoleccion, ruta_zona, vehiculo, observaciones, usuario_id: currentUserId }),
      });
      UI.showAlert("alert-clas", "success", "Clasificación registrada correctamente.");
      UI.limpiarForm(["c-ruta","c-vehiculo","c-obs"], "c-tipo");
      loadClasificaciones();
      loadIndicadores();
    } catch (e) {
      UI.showAlert("alert-clas", "error", e.message);
    }
  },

  async getClasificaciones() { return apiFetch("/clasificaciones"); },

  // ── SCRUM-10: Cantidades ──────────────────────────────────────────
  async guardarCantidad() {
    const fecha           = document.getElementById("q-fecha").value;
    const organico        = parseFloat(document.getElementById("q-organico").value) || 0;
    const reciclable      = parseFloat(document.getElementById("q-reciclable").value) || 0;
    const no_aprovechable = parseFloat(document.getElementById("q-noaprove").value) || 0;
    const especial        = parseFloat(document.getElementById("q-especial").value) || 0;

    let valid = true;
    if (organico < 0)        { UI.fieldError("e-q-organico", "No puede ser negativo"); valid = false; } else UI.clearError("e-q-organico");
    if (!valid) { UI.showAlert("alert-cant", "error", "Los valores no pueden ser negativos."); return; }

    try {
      await apiFetch("/cantidades", {
        method: "POST",
        body: JSON.stringify({ fecha: fecha || null, organico, reciclable, no_aprovechable, especial, usuario_id: currentUserId }),
      });
      UI.showAlert("alert-cant", "success", "Registro guardado. Visible para el administrador.");
      limpiarCantidades();
      loadCantidades();
      loadIndicadores();
    } catch (e) {
      UI.showAlert("alert-cant", "error", e.message);
    }
  },

  async getCantidades() { return apiFetch("/cantidades"); },

  // ── SCRUM-11: Indicadores ─────────────────────────────────────────
  async getIndicadores(periodo = "") {
    const q = periodo ? `?periodo=${encodeURIComponent(periodo)}` : "";
    return apiFetch(`/indicadores${q}`);
  },

  async getHistorico() {
  return apiFetch("/indicadores/historico");
  },

  descargarCSV(periodo = "") {
    const q = periodo ? `?periodo=${encodeURIComponent(periodo)}` : "";
    const url = `${BASE_URL}/reportes/csv${q}`;

    // Crea un enlace invisible y lo dispara para forzar descarga
    const a = document.createElement("a");
    a.href     = url;
    a.download = `reporte_pgirs_${periodo || "completo"}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },

  
  async getAlertas() {
    return apiFetch("/alertas");
  },

  async getAlertasCount() {
    return apiFetch("/alertas/count");
  },

  async resolverAlerta(id) {
    return apiFetch(`/alertas/${id}/resolver`, { method: "PATCH" });
  },

  async getHorarios(zona = "") {
    const q = zona ? `?zona=${encodeURIComponent(zona)}` : "";
    return apiFetch(`/horarios${q}`);
  },

  // ── SCRUM-18: Campañas ────────────────────────────────────────────
  async getCampanas(soloActivas = false) {
    const q = soloActivas ? "?solo_activas=true" : "";
    return apiFetch(`/campanas${q}`);
  },

  async crearCampana(data) {
    return apiFetch("/campanas", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async cambiarEstadoCampana(id, activa) {
    return apiFetch(`/campanas/${id}/estado?activa=${activa}`,
      { method: "PATCH" }
    );
  },

  async eliminarCampana(id) {
    return apiFetch(`/campanas/${id}`, { method: "DELETE" });
  },

  async getZonas() {
    return apiFetch("/horarios/zonas");
  },

  async crearHorario(data) {
    return apiFetch("/horarios", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Usuarios / trazabilidad ─────────────────────────────
  async crearUsuario() {
    const nombre = document.getElementById("u-nombre").value.trim();
    const rol    = document.getElementById("u-rol").value;

    if (!nombre) { UI.showAlert("alert-user", "error", "El nombre es obligatorio."); return; }

    try {
      await apiFetch("/usuarios", {
        method: "POST",
        body: JSON.stringify({ nombre, rol }),
      });
      UI.showAlert("alert-user", "success", `Usuario '${nombre}' creado como ${rol}.`);
      document.getElementById("u-nombre").value = "";
      loadUsuarios();
      loadAcciones();
    } catch (e) {
      UI.showAlert("alert-user", "error", e.message);
    }
  },

  async getUsuarios()  { return apiFetch("/usuarios"); },
  async getAcciones()  { return apiFetch("/acciones"); },

  // ── SCRUM-14: Puntos críticos ─────────────────────────────────────
  async getPuntosCriticos(estado = "") {
    const q = estado ? `?estado=${encodeURIComponent(estado)}` : "";
    return apiFetch(`/puntos-criticos${q}`);
  },

  async crearPuntoCritico(data) {
    return apiFetch("/puntos-criticos", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async actualizarEstadoPC(id, estado) {
    return apiFetch(
      `/puntos-criticos/${id}/estado?estado=${encodeURIComponent(estado)}`,
      { method: "PATCH" }
    );
  },

  async getResumenPC() {
    return apiFetch("/puntos-criticos/resumen");
  },

  // ── SCRUM-19: Municipios ──────────────────────────────────────────
  async getMunicipios() {
    return apiFetch("/municipios");
  },

  async getMunicipioActivo() {
    return apiFetch("/municipios/activo");
  },

  async crearMunicipio(data) {
    return apiFetch("/municipios", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async activarMunicipio(id) {
    return apiFetch(`/municipios/${id}/activar`, { method: "PATCH" });
  },

  async getIndicadoresMunicipio(id) {
    return apiFetch(`/municipios/${id}/indicadores`);
  },
};


// ── Monitor de tiempo de respuesta ───────────────────────────────────────────
const PerformanceMonitor = {

  // Mide el tiempo de respuesta de un endpoint
  async medirTiempo(endpoint) {
    const inicio   = performance.now();
    const url      = `${BASE_URL}${endpoint}`;
    let   status   = "ok";
    let   error    = null;

    try {
      const res = await fetch(url);
      if (!res.ok) status = `error ${res.status}`;
    } catch (e) {
      status = "sin conexión";
      error  = e.message;
    }

    const fin      = performance.now();
    const duracion = Math.round(fin - inicio);

    return {
      endpoint,
      duracion_ms: duracion,
      estado: status,
      cumple_500ms: duracion < 500,
      cumple_3s:    duracion < 3000,
      error,
      medido_en: new Date().toLocaleTimeString("es-CO"),
    };
  },

  // Mide todos los endpoints principales de una vez
  async medirTodos() {
    const endpoints = [
      "/health",
      "/diagnosticos",
      "/metas",
      "/clasificaciones",
      "/cantidades",
      "/indicadores",
      "/indicadores/historico",
      "/alertas/count",
      "/horarios",
      "/usuarios",
      "/acciones",
    ];

    const resultados = await Promise.all(
      endpoints.map(ep => this.medirTiempo(ep))
    );

    return resultados;
  },

  // Muestra los resultados en la consola con formato visual
  async reporteConsola() {
    console.log("%c⏱ EcoGestión — Reporte de tiempos de respuesta",
      "color:#4ade80;font-weight:bold;font-size:14px;");
    console.log("%c" + "─".repeat(60), "color:#2d5540");

    const resultados = await this.medirTodos();

    resultados.forEach(r => {
      const icono  = r.cumple_500ms ? "✅" : r.cumple_3s ? "⚠️" : "❌";
      const color  = r.cumple_500ms ? "color:#4ade80"
                   : r.cumple_3s    ? "color:#fb923c"
                   : "color:#f87171";
      console.log(
        `%c${icono} ${r.endpoint.padEnd(30)} ${r.duracion_ms}ms — ${r.estado}`,
        color
      );
    });

    const tiempos  = resultados.map(r => r.duracion_ms);
    const promedio = Math.round(tiempos.reduce((a,b)=>a+b,0) / tiempos.length);
    const maximo   = Math.max(...tiempos);
    const minimo   = Math.min(...tiempos);
    const fallidos = resultados.filter(r => !r.cumple_3s).length;

    console.log("%c" + "─".repeat(60), "color:#2d5540");
    console.log(`%cPromedio: ${promedio}ms | Mín: ${minimo}ms | Máx: ${maximo}ms`,
      "color:#a3c4ab;font-weight:bold");
    console.log(`%cFuera de límite (<3s): ${fallidos} endpoint(s)`,
      fallidos > 0 ? "color:#f87171" : "color:#4ade80");

    return resultados;
  },
};
