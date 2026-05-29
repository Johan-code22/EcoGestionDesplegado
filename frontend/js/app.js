/**
 * app.js — Controlador principal de la aplicación
 * Principio SOLID: Orchestrates UI + API, no conoce detalles de implementación
 */

// ── Navegación ────────────────────────────────────────────────────────────────
const PAGE_TITLES = {
  dashboard:    "Dashboard",
  diagnostico:  "Diagnóstico Inicial",
  metas:        "Metas PGIRS",
  clasificar:   "Clasificar Residuos",
  cantidades:   "Cantidades Recolectadas",
  indicadores:  "Indicadores PGIRS",
  reportes: "Reportes CSV",
  roles:        "Roles y Trazabilidad",
  alertas: "Alertas Orgánico >48h",
  horarios: "Horarios de Recolección",
  campanas: "Campañas de Educación Ambiental",
  "puntos-criticos": "Puntos Críticos",
  municipios: "Gestión de Municipios",
};

// ── Permisos por rol ──────────────────────────────────────────────
const PERMISOS = {
  administrador: [
    "dashboard", "diagnostico", "metas",
    "indicadores", "reportes", "alertas",
    "horarios", "roles", "cantidades",
    "campanas", "puntos-criticos", "municipios" // ← agrega
  ],
  operador: [
    "dashboard", "clasificar", "cantidades",
    "horarios", "campanas", "puntos-criticos"
  ],
};

function goTo(page) {
  // Verificar permiso del rol activo
  const user = Auth.obtenerUsuario();
  const rol  = user ? user.rol : "operador";
  const permitidos = PERMISOS[rol] || PERMISOS["operador"];

  if (!permitidos.includes(page)) {
    mostrarAccesoDenegado();
    return;
  }

  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const section = document.getElementById(`page-${page}`);
  if (section) section.classList.add("active");

  const navEl = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (navEl) navEl.classList.add("active");

  document.getElementById("topbar-title").textContent =
    PAGE_TITLES[page] || page;

  if (window.innerWidth <= 900)
    document.getElementById("sidebar").classList.remove("open");

  const loaders = {
    dashboard: () => medirCargaPagina("dashboard", () =>
      Promise.all([loadIndicadores(), loadDiagnosticos(), loadHistorico()])
    ),
    diagnostico: loadDiagnosticos,
    metas:       () => { loadMetas(); loadMetasDiagSelects(); },
    cantidades:  () => {
      const user = Auth.obtenerUsuario();
      if (user && user.rol === "administrador") {
        loadCantidadesAdmin();
      } else {
        loadCantidades();
      }
    },
    clasificar:  loadClasificaciones,
    indicadores: () => medirCargaPagina("indicadores", () =>
      Promise.all([loadIndicadores(), loadCounts()])
    ),
    reportes:    () => {},
    alertas:     loadAlertas,
    horarios:    () => { loadHorarios(); loadZonas(); },
    roles:       () => { loadUsuarios(); loadAcciones(); },
    campanas: () => loadCampanas(false),
    "puntos-criticos": () => { loadPuntosCriticos(); loadResumenPC(); },
    municipios: () => { loadMunicipios(); loadMunicipioActivo(); },
  };
  if (loaders[page]) loaders[page]();
}

function mostrarAccesoDenegado() {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  document.getElementById("topbar-title").textContent = "Acceso denegado";

  // Muestra mensaje inline sin página separada
  const temp = document.createElement("div");
  temp.id = "page-denegado";
  temp.className = "page active";
  temp.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;min-height:60vh;gap:16px;text-align:center;">
      <div style="font-size:48px;">🔒</div>
      <h2 style="font-family:var(--font-display);font-size:28px;color:var(--text);">
        Acceso Denegado
      </h2>
      <p style="color:var(--text2);font-size:14px;max-width:400px;">
        No tienes permisos para acceder a este módulo.
        Contacta al administrador si crees que esto es un error.
      </p>
      <button class="btn btn-ghost" onclick="goTo('dashboard')">
        ← Volver al Dashboard
      </button>
    </div>`;

  // Elimina el temporal anterior si existe
  const anterior = document.getElementById("page-denegado");
  if (anterior) anterior.remove();

  document.querySelector(".main").appendChild(temp);
}

// Bind nav items
document.querySelectorAll(".nav-item[data-page]").forEach(el => {
  el.addEventListener("click", () => goTo(el.dataset.page));
});

// ── Role switch ───────────────────────────────────────────────────────────────
function switchRole(role, btn) {
  document.querySelectorAll(".role-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const isAdmin = role === "administrador";
  setCurrentUser(isAdmin ? 1 : 2);

  document.getElementById("sb-name").textContent = isAdmin ? "Admin Municipal" : "Operador de Aseo";
  document.getElementById("sb-role").textContent = isAdmin ? "Administrador" : "Operador";
  document.getElementById("sb-avatar").textContent = isAdmin ? "AD" : "OP";

  const adminOnly = document.getElementById("admin-only");
  if (adminOnly) adminOnly.style.display = isAdmin ? "" : "none";
}

// ── Loaders (GET desde API) ───────────────────────────────────────────────────

async function loadDiagnosticos() {
  try {
    const items = await API.getDiagnosticos();
    UI.renderTable("tbody-diag", items.map(d => `
      <tr>
        <td><strong style="color:var(--text)">${d.anio} / ${d.periodo}</strong></td>
        <td>${UI.fmtNum(d.organico)}</td>
        <td>${UI.fmtNum(d.reciclable)}</td>
        <td>${UI.fmtNum(d.no_aprovechable)}</td>
        <td><strong style="color:var(--accent)">${UI.fmtNum(d.total)} t</strong></td>
      </tr>`));
  } catch (e) { console.warn("loadDiagnosticos:", e.message); }
}

async function loadMetasDiagSelects() {
  try {
    const diags = await API.getDiagnosticos();
    const sel = document.getElementById("m-diag");
    if (!sel) return;
    sel.innerHTML = '<option value="">Sin asociar</option>' +
      diags.map(d => `<option value="${d.id}">${d.anio} / ${d.periodo}</option>`).join("");
  } catch {}
}

async function loadMetas() {
  try {
    const items = await API.getMetas();
    UI.renderTable("tbody-metas", items.map(m => `
      <tr>
        <td>${m.periodo}</td>
        <td>${UI.badgeHtml(m.tipo_residuo)}</td>
        <td><strong style="color:var(--text)">${UI.fmtNum(m.valor_meta)} t</strong></td>
        <td style="font-size:11px;color:var(--text3)">${m.diagnostico_id ? "Diag. #" + m.diagnostico_id : "—"}</td>
      </tr>`));
  } catch (e) { console.warn("loadMetas:", e.message); }
}

async function loadClasificaciones() {
  try {
    const items = await API.getClasificaciones();
    UI.renderTable("tbody-clas", items.map(c => `
      <tr>
        <td style="font-family:var(--font-mono);font-size:12px;">${c.fecha_recoleccion}</td>
        <td>${UI.badgeHtml(c.tipo_residuo)}</td>
        <td>${c.ruta_zona || "—"}</td>
      </tr>`));
  } catch (e) { console.warn("loadClasificaciones:", e.message); }
}

async function loadCantidades() {
  try {
    const items = await API.getCantidades();
    UI.renderTable("tbody-cant", items.map(c => `
      <tr>
        <td style="font-family:var(--font-mono);font-size:11px;">${c.fecha}</td>
        <td>${UI.fmtNum(c.organico)}</td>
        <td>${UI.fmtNum(c.reciclable)}</td>
        <td>${UI.fmtNum(c.no_aprovechable)}</td>
        <td><strong style="color:var(--accent)">${UI.fmtNum(c.total)}</strong></td>
      </tr>`));
  } catch (e) { console.warn("loadCantidades:", e.message); }
}

async function loadCantidadesAdmin() {
  try {
    const items = await API.getCantidades();
    UI.renderTable("tbody-cant-admin", items.length ? items.map(c => `
      <tr>
        <td style="font-family:var(--font-mono);font-size:11px;">${c.fecha}</td>
        <td>${UI.fmtNum(c.organico)}</td>
        <td>${UI.fmtNum(c.reciclable)}</td>
        <td>${UI.fmtNum(c.no_aprovechable)}</td>
        <td><strong style="color:var(--accent)">${UI.fmtNum(c.total)}</strong></td>
      </tr>`) : [`
      <tr>
        <td colspan="5" style="text-align:center;color:var(--text3);
            font-family:var(--font-mono);font-size:12px;padding:20px;">
          No hay registros de cantidades aún.
        </td>
      </tr>`]);
  } catch (e) {
    console.warn("loadCantidadesAdmin:", e.message);
  }
}
async function loadIndicadores() {
  try {
    const ind = await API.getIndicadores();

    // Dashboard
    UI.setText("d-total", ind.total_general);
    UI.setText("d-rec",   ind.total_reciclable);
    UI.setText("d-org",   ind.total_organico);
    UI.setText("d-no",    ind.total_no_aprovechable);

    // Indicators page
    UI.setText("i-total", ind.total_general);
    UI.setText("i-org",   ind.total_organico);
    UI.setText("i-rec",   ind.total_reciclable);
    UI.setText("i-no",    ind.total_no_aprovechable);

    UI.updateProgressBar("ib-aprov", "i-aprov", ind.tasa_aprovechamiento);
    UI.updateProgressBar("ib-no",    "i-no-pct", ind.pct_no_aprovechable);
    UI.updateProgressBar("ib-rec",   "i-rec-pct", ind.pct_reciclable);

    // Dashboard bars
    UI.updateProgressBar("bar-aprov", "ind-aprov-pct", ind.tasa_aprovechamiento);
    UI.updateProgressBar("bar-no",    "ind-no-pct",    ind.pct_no_aprovechable);
    UI.updateProgressBar("bar-rec",   "ind-rec-pct",   ind.pct_reciclable);

    // Donut
    updateDonut(ind);
  } catch (e) { console.warn("loadIndicadores:", e.message); }
}

function updateDonut(ind) {
  const total = ind.total_general;
  if (!total) return;
  const pOrg = ind.pct_organico, pRec = ind.pct_reciclable, pNo = ind.pct_no_aprovechable;

  // offset calc: arc starts at top (offset 25)
  document.getElementById("arc-org").setAttribute("stroke-dasharray", `${pOrg} ${100-pOrg}`);
  document.getElementById("arc-org").setAttribute("stroke-dashoffset", "25");

  const offRec = 25 - pOrg;
  document.getElementById("arc-rec").setAttribute("stroke-dasharray", `${pRec} ${100-pRec}`);
  document.getElementById("arc-rec").setAttribute("stroke-dashoffset", String(offRec));

  const offNo = offRec - pRec;
  document.getElementById("arc-no").setAttribute("stroke-dasharray", `${pNo} ${100-pNo}`);
  document.getElementById("arc-no").setAttribute("stroke-dashoffset", String(offNo));

  document.getElementById("donut-label").textContent = total + "t";

  UI.setText("leg-org", `Orgánico — ${ind.total_organico}t (${pOrg}%)`);
  UI.setText("leg-rec", `Reciclable — ${ind.total_reciclable}t (${pRec}%)`);
  UI.setText("leg-no",  `No Aprovechable — ${ind.total_no_aprovechable}t (${pNo}%)`);
}

async function loadCounts() {
  try {
    const [diags, metas, clas, cants, users, ind] = await Promise.all([
      API.getDiagnosticos(), API.getMetas(), API.getClasificaciones(),
      API.getCantidades(),   API.getUsuarios(), API.getIndicadores(),
    ]);
    UI.setText("cnt-diag",  diags.length);
    UI.setText("cnt-metas", metas.length);
    UI.setText("cnt-clas",  clas.length);
    UI.setText("cnt-cant",  cants.length);
    UI.setText("cnt-usr",   users.length);
  } catch {}
}

async function loadUsuarios() {
  try {
    const items = await API.getUsuarios();
    UI.renderTable("tbody-users", items.map(u => `
      <tr>
        <td><strong style="color:var(--text)">${u.nombre}</strong></td>
        <td>${UI.badgeHtml(u.rol)}</td>
        <td style="font-size:11px;font-family:var(--font-mono);">${u.creado_en}</td>
      </tr>`));
  } catch (e) { console.warn("loadUsuarios:", e.message); }
}

async function loadAcciones() {
  try {
    const items = await API.getAcciones();
    const colors = { CREATE: "var(--accent)", UPDATE: "#60a5fa", DELETE: "var(--danger)" };
    const container = document.getElementById("log-container");
    if (!container) return;
    container.innerHTML = items.map(a => `
      <div class="log-entry">
        <div class="log-dot" style="background:${colors[a.accion]||"var(--accent)"}"></div>
        <div>
          <div class="log-msg">${a.detalle || a.accion + " en " + a.entidad}</div>
          <div class="log-meta">Usuario #${a.usuario_id || "?"} · ${a.fecha_hora}</div>
        </div>
      </div>`).join("");
  } catch (e) { console.warn("loadAcciones:", e.message); }
}

// ── Verificación de API al cargar ─────────────────────────────────────────────
async function pingAPI() {
  const ok = await checkHealth();
  const dot  = document.getElementById("status-dot");
  const text = document.getElementById("status-text");
  if (ok) {
    dot.classList.add("ok");
    text.textContent = "API conectada";
  } else {
    dot.classList.remove("ok");
    text.textContent = "API no disponible";
  }
}

// ── Set default date on date inputs ──────────────────────────────────────────
function initDates() {
  const today = new Date().toISOString().split("T")[0];
  ["c-fecha","q-fecha"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });
}

// Recarga silenciosa de indicadores cada 30 segundos
function iniciarRecargaAutomatica() {
  setInterval(() => {
    // SCRUM-20: No recarga si la pestaña está en segundo plano
    if (document.hidden) return;

    const dashActivo = document.getElementById("page-dashboard")
                               .classList.contains("active");
    const indActivo  = document.getElementById("page-indicadores")
                               .classList.contains("active");
    if (dashActivo || indActivo) {
      loadIndicadores();
      loadHistorico();
    }
    checkAlertas();
  }, 30000);
}

// ── Gráfica de barras con Canvas API ─────────────────────────────────────────

// Guarda los datos del histórico para poder redibujar si es necesario
let _datosHistorico = [];

async function loadHistorico() {
  try {
    const datos = await API.getHistorico();
    _datosHistorico = datos;

    // Dibuja después de que loadIndicadores termine (200ms de margen)
    setTimeout(() => {
      const canvas = document.getElementById("grafica-barras");
      if (!canvas || !datos.length) return;

      const W = canvas.parentElement.offsetWidth - 48;
      const H = 180;
      canvas.width  = W;
      canvas.height = H;

      const ctx    = canvas.getContext("2d");
      const pad    = 40;
      const maxVal = Math.max(...datos.map(d => d.total || 0)) || 1;
      const barW   = (W - pad * 2) / datos.length;

      ctx.fillStyle = "#1c3326";
      ctx.fillRect(0, 0, W, H);

      const pasos = 4;
      for (let i = 0; i <= pasos; i++) {
        const valor = Math.round((maxVal / pasos) * i * 10) / 10;
        const y     = H - 30 - (i / pasos) * (H - 50);

        // Línea guía horizontal
        ctx.strokeStyle = "rgba(45,85,64,0.5)";
        ctx.lineWidth   = 0.5;
        ctx.beginPath();
        ctx.moveTo(pad, y);
        ctx.lineTo(W - 10, y);
        ctx.stroke();

        // Etiqueta del valor
        ctx.fillStyle = "#6b9478";
        ctx.font      = "9px monospace";
        ctx.textAlign = "right";
        ctx.fillText(valor, pad - 4, y + 3);
      }

      datos.forEach((d, i) => {
        const x = pad + i * barW;
        ["organico","reciclable","no_aprovechable"].forEach((tipo, j) => {
          const subW    = (barW - 12) / 3;
          const offsetX = x + 4 + j * subW;
          const val     = d[tipo] || 0;
          const barH    = Math.max((val / maxVal) * (H - 50), val > 0 ? 4 : 0);
          ctx.fillStyle = ["#4ade80","#60a5fa","#fb923c"][j];
          ctx.fillRect(offsetX, H - 30 - barH, subW - 2, barH);
        });

        ctx.fillStyle = "#6b9478";
        ctx.font      = "10px monospace";
        ctx.textAlign = "center";
        ctx.fillText(d.fecha ? d.fecha.slice(5) : "", x + barW / 2, H - 12);
      });

      // Leyenda
      const leyenda = [
        { color: "#4ade80", label: "Orgánico" },
        { color: "#60a5fa", label: "Reciclable" },
        { color: "#fb923c", label: "No Aprovechable" },
      ];
      let lx = pad;
      ctx.textAlign = "left";
      leyenda.forEach(l => {
        ctx.fillStyle = l.color;
        ctx.fillRect(lx, 8, 10, 10);
        ctx.fillStyle = "#a3c4ab";
        ctx.font      = "10px monospace";
        ctx.fillText(l.label, lx + 14, 17);
        lx += ctx.measureText(l.label).width + 30;
      });

    }, 50);
  } catch (e) {
    console.warn("loadHistorico:", e.message);
  }
}

function descargarReporte() {
  const periodo = document.getElementById("rep-periodo").value;
  API.descargarCSV(periodo);
}

async function checkAlertas() {
  try {
    const data = await API.getAlertasCount();
    actualizarBadgeAlertas(data.count);
  } catch {}
}

async function loadAlertas() {
  try {
    const items = await API.getAlertas();
    const container = document.getElementById("alertas-lista");
    if (!container) return;

    if (!items.length) {
      container.innerHTML = `
        <div style="color:var(--accent);font-size:13px;
                    font-family:var(--font-mono);padding:20px 0;">
          ✅ No hay alertas activas. Todos los residuos orgánicos
          están dentro del límite de 48 horas.
        </div>`;
      return;
    }

    container.innerHTML = items.map(a => `
      <div class="alerta-item ${a.resuelta ? 'resuelta' : ''}"
           id="alerta-${a.id}">
        <div class="alerta-icon">${a.resuelta ? '✅' : '🚨'}</div>
        <div class="alerta-body">
          <div class="alerta-msg">${a.mensaje}</div>
          <div class="alerta-horas">
            ${a.resuelta ? 'Resuelta' : a.horas_transcurridas + 'h almacenado'}
          </div>
          <div class="alerta-meta">${a.generada_en}</div>
        </div>
        ${!a.resuelta ? `
          <button class="btn btn-ghost btn-sm"
                  onclick="resolverAlerta(${a.id})">
            ✅ Resolver
          </button>` : ''}
      </div>`).join("");

    actualizarBadgeAlertas(items.filter(a => !a.resuelta).length);
  } catch (e) {
    console.warn("loadAlertas:", e.message);
  }
}

async function resolverAlerta(id) {
  try {
    await API.resolverAlerta(id);
    loadAlertas();
  } catch (e) {
    console.warn("resolverAlerta:", e.message);
  }
}

function actualizarBadgeAlertas(count) {
  const badge    = document.getElementById("badge-alertas");
  const topbar   = document.getElementById("topbar-alertas");
  const topCount = document.getElementById("topbar-alertas-count");

  if (badge) {
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline-flex" : "none";
  }
  if (topCount) topCount.textContent = count;
  if (topbar) topbar.style.display = count > 0 ? "inline-flex" : "none";
}

async function loadHorarios(zona = "") {
  try {
    const items = await API.getHorarios(zona);
    const badgeMap = {
      "General":    "badge-no-aprove",
      "Reciclable": "badge-reciclable",
      "Orgánico":   "badge-organico",
      "Especial":   "badge-especial",
    };

    UI.renderTable("tbody-horarios", items.length ? items.map(h => `
      <tr>
        <td><strong style="color:var(--text)">${h.zona}</strong></td>
        <td style="font-size:12px;">${h.dias}</td>
        <td style="font-family:var(--font-mono);font-size:12px;">
          ${h.hora_inicio} – ${h.hora_fin}
        </td>
        <td>
          <span class="badge ${badgeMap[h.tipo_residuo] || 'badge-operador'}">
            ${h.tipo_residuo}
          </span>
        </td>
      </tr>`) : [`
      <tr>
        <td colspan="4" style="text-align:center;
                               color:var(--text3);
                               font-family:var(--font-mono);
                               font-size:12px;padding:20px;">
          No hay horarios registrados para esta zona.
        </td>
      </tr>`]);
  } catch (e) {
    console.warn("loadHorarios:", e.message);
  }
}

async function loadZonas() {
  try {
    const zonas = await API.getZonas();
    const sel   = document.getElementById("h-zona-filtro");
    if (!sel) return;
    sel.innerHTML = '<option value="">Todas las zonas</option>' +
      zonas.map(z => `<option value="${z}">${z}</option>`).join("");
  } catch (e) {
    console.warn("loadZonas:", e.message);
  }
}

function filtrarHorarios() {
  const zona = document.getElementById("h-zona-filtro").value;
  loadHorarios(zona);
}

function limpiarFiltroHorarios() {
  document.getElementById("h-zona-filtro").value = "";
  loadHorarios();
}

async function guardarHorario() {
  const zona       = document.getElementById("h-zona").value.trim();
  const dias       = document.getElementById("h-dias").value.trim();
  const hora_inicio = document.getElementById("h-inicio").value;
  const hora_fin   = document.getElementById("h-fin").value;
  const tipo_residuo = document.getElementById("h-tipo").value;

  if (!zona || !dias || !hora_inicio || !hora_fin) {
    UI.showAlert("alert-horario", "error",
                 "Zona, días y horario son obligatorios.");
    return;
  }

  try {
    await API.crearHorario({ zona, dias, hora_inicio, hora_fin, tipo_residuo });
    UI.showAlert("alert-horario", "success", "Horario creado correctamente.");
    UI.limpiarForm(["h-zona","h-dias","h-inicio","h-fin"]);
    loadHorarios();
    loadZonas();
  } catch (e) {
    UI.showAlert("alert-horario", "error", e.message);
  }
}

let _soloActivasCampanas = false;

async function loadCampanas(soloActivas = false) {
  _soloActivasCampanas = soloActivas;
  try {
    const items = await API.getCampanas(soloActivas);
    const user  = Auth.obtenerUsuario();
    const isAdmin = user && user.rol === "administrador";
    const container = document.getElementById("campanas-lista");
    if (!container) return;

    // Actualiza estilo de botones tab
    const btnTodas   = document.getElementById("btn-todas");
    const btnActivas = document.getElementById("btn-activas");
    if (btnTodas && btnActivas) {
      btnTodas.className   = soloActivas
        ? "btn btn-ghost btn-sm" : "btn btn-primary btn-sm";
      btnActivas.className = soloActivas
        ? "btn btn-primary btn-sm" : "btn btn-ghost btn-sm";
    }

    if (!items.length) {
      container.innerHTML = `
        <div style="color:var(--text3);font-size:13px;
                    font-family:var(--font-mono);padding:20px 0;">
          No hay campañas ${soloActivas ? "activas " : ""}registradas.
        </div>`;
      return;
    }

    container.innerHTML = items.map(c => `
      <div class="campana-card ${c.activa ? 'activa' : 'inactiva'}">
        <div class="campana-titulo">
          ${c.activa ? '📢' : '📭'} ${c.titulo}
        </div>
        <div class="campana-desc">${c.descripcion}</div>
        <div class="campana-meta">
          ${c.periodo ? '📅 ' + c.periodo + ' · ' : ''}
          ${c.activa
            ? '<span style="color:var(--accent)">● Activa</span>'
            : '<span style="color:var(--text3)">○ Inactiva</span>'}
        </div>
        ${isAdmin ? `
          <div class="campana-actions">
            <button class="btn btn-ghost btn-sm"
                    onclick="toggleCampana(${c.id}, ${c.activa})">
              ${c.activa ? '⏸ Desactivar' : '▶ Activar'}
            </button>
            <button class="btn btn-danger btn-sm"
                    onclick="confirmarEliminarCampana(${c.id})">
              🗑 Eliminar
            </button>
          </div>` : ''}
      </div>`).join("");

  } catch (e) {
    console.warn("loadCampanas:", e.message);
  }
}

function verCampanas(soloActivas) {
  loadCampanas(soloActivas);
}

async function guardarCampana() {
  const titulo      = document.getElementById("camp-titulo").value.trim();
  const descripcion = document.getElementById("camp-desc").value.trim();
  const periodo     = document.getElementById("camp-periodo").value;

  if (!titulo || !descripcion) {
    UI.showAlert("alert-campana", "error",
                 "El título y la descripción son obligatorios.");
    return;
  }

  try {
    await API.crearCampana({ titulo, descripcion, periodo });
    UI.showAlert("alert-campana", "success", "Campaña creada correctamente.");
    UI.limpiarForm(["camp-titulo","camp-desc"], "camp-periodo");
    loadCampanas(_soloActivasCampanas);
  } catch (e) {
    UI.showAlert("alert-campana", "error", e.message);
  }
}

async function toggleCampana(id, activa) {
  try {
    await API.cambiarEstadoCampana(id, !activa);
    loadCampanas(_soloActivasCampanas);
  } catch (e) {
    console.warn("toggleCampana:", e.message);
  }
}

async function confirmarEliminarCampana(id) {
  if (!confirm("¿Eliminar esta campaña permanentemente?")) return;
  try {
    await API.eliminarCampana(id);
    loadCampanas(_soloActivasCampanas);
  } catch (e) {
    console.warn("eliminarCampana:", e.message);
  }
}

let _filtroPC = "";

async function loadPuntosCriticos(estado = "") {
  _filtroPC = estado;
  try {
    const items   = await API.getPuntosCriticos(estado);
    const user    = Auth.obtenerUsuario();
    const isAdmin = user && user.rol === "administrador";
    const container = document.getElementById("pc-lista");
    if (!container) return;

    // Actualiza botones de filtro
    ["pcf-todos","pcf-pendiente","pcf-proceso","pcf-resuelto"]
      .forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = "btn btn-ghost btn-sm";
      });
    const activo = estado === ""           ? "pcf-todos"
                 : estado === "pendiente"  ? "pcf-pendiente"
                 : estado === "en_proceso" ? "pcf-proceso"
                 : "pcf-resuelto";
    const btnActivo = document.getElementById(activo);
    if (btnActivo) btnActivo.className = "btn btn-primary btn-sm";

    if (!items.length) {
      container.innerHTML = `
        <div style="color:var(--text3);font-size:13px;
                    font-family:var(--font-mono);padding:20px 0;">
          No hay reportes ${estado ? 'con estado ' + estado : ''}.
        </div>`;
      return;
    }

    const iconos = {
      pendiente:  "⏳", en_proceso: "🔧", resuelto: "✅"
    };

    container.innerHTML = items.map(p => `
      <div class="pc-card ${p.estado}">
        ${p.imagen_url ? `
          <img class="pc-img" src="${p.imagen_url}"
               alt="Punto crítico"
               onerror="this.style.display='none'">` : ""}
        <div class="pc-desc">📍 ${p.descripcion}</div>
        <div class="pc-ubicacion">📌 ${p.ubicacion}</div>
        <div class="pc-meta">${p.creado_en}</div>
        <div style="display:flex;align-items:center;
                    justify-content:space-between;flex-wrap:wrap;gap:8px;">
          <span class="pc-estado ${p.estado}">
            ${iconos[p.estado] || "●"} ${p.estado.replace("_"," ")}
          </span>
          ${isAdmin ? `
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              ${p.estado !== "en_proceso" ? `
                <button class="btn btn-ghost btn-sm"
                        onclick="cambiarEstadoPC(${p.id},'en_proceso')">
                  🔧 En proceso
                </button>` : ""}
              ${p.estado !== "resuelto" ? `
                <button class="btn btn-ghost btn-sm"
                        onclick="cambiarEstadoPC(${p.id},'resuelto')">
                  ✅ Resolver
                </button>` : ""}
            </div>` : ""}
        </div>
      </div>`).join("");
  } catch (e) {
    console.warn("loadPuntosCriticos:", e.message);
  }
}

async function loadResumenPC() {
  try {
    const r = await API.getResumenPC();
    UI.setText("pc-pendiente", r.pendiente  || 0);
    UI.setText("pc-en-proceso", r.en_proceso || 0);
    UI.setText("pc-resuelto",  r.resuelto   || 0);
    UI.setText("pc-total",
      (r.pendiente || 0) + (r.en_proceso || 0) + (r.resuelto || 0));
  } catch (e) {
    console.warn("loadResumenPC:", e.message);
  }
}

function filtrarPC(estado) {
  loadPuntosCriticos(estado);
}

async function cambiarEstadoPC(id, estado) {
  try {
    await API.actualizarEstadoPC(id, estado);
    loadPuntosCriticos(_filtroPC);
    loadResumenPC();
  } catch (e) {
    console.warn("cambiarEstadoPC:", e.message);
  }
}

async function guardarPuntoCritico() {
  const descripcion = document.getElementById("pc-desc").value.trim();
  const ubicacion   = document.getElementById("pc-ubicacion").value.trim();
  const imagen_url  = document.getElementById("pc-imagen").value.trim();

  if (!descripcion || !ubicacion) {
    UI.showAlert("alert-pc", "error",
                 "La descripción y la ubicación son obligatorias.");
    return;
  }

  try {
    await API.crearPuntoCritico({ descripcion, ubicacion, imagen_url });
    UI.showAlert("alert-pc", "success",
                 "Reporte enviado correctamente. El operador lo atenderá pronto.");
    UI.limpiarForm(["pc-desc","pc-ubicacion","pc-imagen"]);
    ocultarPreviewPC();
    loadPuntosCriticos(_filtroPC);
    loadResumenPC();
  } catch (e) {
    UI.showAlert("alert-pc", "error", e.message);
  }
}

// Vista previa de imagen al escribir la URL
document.addEventListener("DOMContentLoaded", () => {
  // Se agrega después de que el DOM cargue
  setTimeout(() => {
    const inputImg = document.getElementById("pc-imagen");
    if (inputImg) {
      inputImg.addEventListener("input", () => {
        const url     = inputImg.value.trim();
        const preview = document.getElementById("pc-preview");
        const img     = document.getElementById("pc-img-preview");
        if (url && preview && img) {
          img.src = url;
          preview.style.display = "block";
        } else if (preview) {
          preview.style.display = "none";
        }
      });
    }
  }, 1000);
});

function ocultarPreviewPC() {
  const preview = document.getElementById("pc-preview");
  if (preview) preview.style.display = "none";
}

// ── SCRUM-19: Municipios ──────────────────────────────────────────

async function loadMunicipioActivo() {
  try {
    const mun = await API.getMunicipioActivo();
    UI.setText("municipio-activo-nombre", mun.nombre);
    UI.setText("topbar-badge", `🏛 ${mun.nombre}`);
  } catch {
    UI.setText("municipio-activo-nombre", "Sin municipio");
  }
}

async function loadMunicipios() {
  try {
    const items     = await API.getMunicipios();
    const container = document.getElementById("municipios-lista");
    if (!container) return;

    container.innerHTML = items.map(m => `
      <div class="municipio-card ${m.activo ? 'activo' : ''}">
        <div class="municipio-icon">
          ${m.activo ? '🟢' : '⚪'}
        </div>
        <div class="municipio-info">
          <div class="municipio-nombre">${m.nombre}</div>
          <div class="municipio-sub">
            ${m.departamento || '—'} · Código: ${m.codigo || '—'}
            ${m.activo
              ? ' · <span style="color:var(--accent)">● Activo</span>'
              : ''}
          </div>
        </div>
        <div style="display:flex;gap:6px;flex-direction:column;">
          ${!m.activo ? `
            <button class="btn btn-primary btn-sm"
                    onclick="activarMunicipio(${m.id})">
              Activar
            </button>` : `
            <span style="font-size:11px;color:var(--accent);
                         font-family:var(--font-mono);">
              Activo
            </span>`}
          <button class="btn btn-ghost btn-sm"
                  onclick="verIndicadoresMunicipio(${m.id})">
            📊 Ver datos
          </button>
        </div>
      </div>`).join("");

  } catch (e) {
    console.warn("loadMunicipios:", e.message);
  }
}

async function activarMunicipio(id) {
  try {
    const res = await API.activarMunicipio(id);
    UI.showAlert("alert-municipio", "success", res.mensaje);
    loadMunicipios();
    loadMunicipioActivo();
  } catch (e) {
    UI.showAlert("alert-municipio", "error", e.message);
  }
}

async function verIndicadoresMunicipio(id) {
  try {
    const ind = await API.getIndicadoresMunicipio(id);
    const container = document.getElementById("municipio-indicadores");
    if (!container) return;

    container.innerHTML = `
      <div class="meta-row">
        <div class="meta-key">Municipio</div>
        <div class="meta-val">${ind.municipio_nombre}</div>
      </div>
      <div class="meta-row">
        <div class="meta-key">Total recolectado</div>
        <div class="meta-val"
             style="color:var(--accent)">${ind.total_general} t</div>
      </div>
      <div class="meta-row">
        <div class="meta-key">Orgánico</div>
        <div class="meta-val">${ind.total_organico} t
          (${ind.pct_organico}%)</div>
      </div>
      <div class="meta-row">
        <div class="meta-key">Reciclable</div>
        <div class="meta-val">${ind.total_reciclable} t
          (${ind.pct_reciclable}%)</div>
      </div>
      <div class="meta-row">
        <div class="meta-key">No Aprovechable</div>
        <div class="meta-val">${ind.total_no_aprovechable} t
          (${ind.pct_no_aprovechable}%)</div>
      </div>
      <div class="meta-row">
        <div class="meta-key">Tasa aprovechamiento</div>
        <div class="meta-val"
             style="color:var(--accent)">
          ${ind.tasa_aprovechamiento}%
        </div>
      </div>
      <div class="meta-row">
        <div class="meta-key">Registros</div>
        <div class="meta-val">${ind.registros_cantidad}</div>
      </div>`;
  } catch (e) {
    console.warn("verIndicadoresMunicipio:", e.message);
  }
}

async function guardarMunicipio() {
  const nombre       = document.getElementById("mun-nombre").value.trim();
  const departamento = document.getElementById("mun-depto").value.trim();
  const codigo       = document.getElementById("mun-codigo").value.trim();

  if (!nombre) {
    UI.showAlert("alert-municipio", "error",
                 "El nombre del municipio es obligatorio.");
    return;
  }

  try {
    await API.crearMunicipio({ nombre, departamento, codigo });
    UI.showAlert("alert-municipio", "success",
                 `Municipio '${nombre}' registrado correctamente.`);
    UI.limpiarForm(["mun-nombre","mun-depto","mun-codigo"]);
    loadMunicipios();
  } catch (e) {
    UI.showAlert("alert-municipio", "error", e.message);
  }
}
// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Oculta app hasta verificar sesión
  document.querySelector(".sidebar").style.display = "none";
  document.querySelector(".main").style.display    = "none";

  initDates();
  Auth.inicializar();   // <-- controla login/app
  await pingAPI();
  setInterval(pingAPI, 30000);
  iniciarRecargaAutomatica();
  setTimeout(checkAlertas, 500);
  setTimeout(loadMunicipioActivo, 600);
});

// SCRUM-20: Monitor de rendimiento de navegación
function medirCargaPagina(page, loader) {
  const inicio = performance.now();
  const resultado = loader();

  // Si el loader retorna una promesa, mide cuando resuelve
  if (resultado && typeof resultado.then === "function") {
    resultado.then(() => {
      const duracion = Math.round(performance.now() - inicio);
      if (duracion > 3000) {
        console.warn(
          `⚠️ SCRUM-20: La página '${page}' tardó ${duracion}ms en cargar` +
          ` (límite: 3000ms)`
        );
      }
    });
  }
}
