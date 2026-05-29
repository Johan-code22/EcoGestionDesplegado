/**
 * auth.js — Manejo de sesión en el frontend
 * Principio SOLID: Single Responsibility — solo gestiona autenticación
 */

const SESSION_KEY = "ecogestion_token";
const USER_KEY    = "ecogestion_user";

const Auth = {

  // Guarda sesión en sessionStorage (se borra al cerrar el navegador)
  guardarSesion(data) {
    sessionStorage.setItem(SESSION_KEY, data.token);
    sessionStorage.setItem(USER_KEY, JSON.stringify({
      id: data.id, nombre: data.nombre, rol: data.rol
    }));
  },

  obtenerToken() {
    return sessionStorage.getItem(SESSION_KEY);
  },

  obtenerUsuario() {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  estaAutenticado() {
    return !!this.obtenerToken();
  },

  async login() {
    const usuario  = document.getElementById("login-usuario").value.trim();
    const password = document.getElementById("login-password").value;
    const errorEl  = document.getElementById("login-error");

    if (!usuario || !password) {
      errorEl.textContent = "Completa todos los campos.";
      errorEl.classList.add("show");
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario, password }),
      });

      if (!res.ok) {
        errorEl.textContent = "Usuario o contraseña incorrectos.";
        errorEl.classList.add("show");
        return;
      }

      const data = await res.json();
      this.guardarSesion(data);
      errorEl.classList.remove("show");
      this.mostrarApp();

    } catch {
      errorEl.textContent = "No se pudo conectar con el servidor.";
      errorEl.classList.add("show");
    }
  },

  async logout() {
    const token = this.obtenerToken();
    if (token) {
      await fetch("http://127.0.0.1:8000/api/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      }).catch(() => {});
    }
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(USER_KEY);
    this.mostrarLogin();
  },

  mostrarApp() {
    document.getElementById("login-overlay").style.display = "none";
    document.querySelector(".sidebar").style.display = "";
    document.querySelector(".main").style.display    = "";

    const user = this.obtenerUsuario();
    if (!user) return;

    // Actualiza info del usuario en sidebar y topbar
    document.getElementById("sb-name").textContent   = user.nombre;
    document.getElementById("sb-role").textContent   = user.rol;
    document.getElementById("sb-avatar").textContent =
      user.nombre.slice(0, 2).toUpperCase();
    document.getElementById("topbar-rol").textContent = user.rol;

    // Aplica permisos al sidebar
    const PERMISOS_ROL = {
      administrador: [
        "dashboard", "diagnostico", "metas",
        "indicadores", "reportes", "alertas",
        "horarios", "roles", "cantidades"
      ],
      operador: [
        "dashboard", "clasificar",
        "cantidades", "horarios"
      ],
    };
    const permitidos = PERMISOS_ROL[user.rol] || PERMISOS_ROL["operador"];

    document.querySelectorAll(".nav-item[data-page]").forEach(el => {
      el.style.display = permitidos.includes(el.dataset.page) ? "" : "none";
    });

    // Sección admin en roles
    const adminOnly = document.getElementById("admin-only");
    if (adminOnly) {
      adminOnly.style.display = user.rol === "administrador" ? "" : "none";
    }

    // Formulario de horarios admin
    const horariosAdmin = document.getElementById("horarios-admin-section");
    if (horariosAdmin) {
      horariosAdmin.style.display = user.rol === "administrador" ? "" : "none";
    }

    // ← AQUÍ VA EL CÓDIGO DEL ARCHIVO — vista de cantidades según rol
    const cantForm     = document.getElementById("cant-form-section");
    const cantAdmin    = document.getElementById("cant-admin-section");
    const cantSubtitle = document.getElementById("cant-subtitle");

    if (user.rol === "administrador") {
      if (cantForm)     cantForm.style.display   = "none";
      if (cantAdmin)    cantAdmin.style.display  = "block";
      if (cantSubtitle) cantSubtitle.textContent =
        "Solo lectura — los registros son ingresados por los operadores";
    } else {
      if (cantForm)     cantForm.style.display   = "";
      if (cantAdmin)    cantAdmin.style.display  = "none";
      if (cantSubtitle) cantSubtitle.textContent =
        "Cantidades validadas (no negativos) → POST /api/cantidades";
    }

    // Oculta badge de alertas si es operador
    const badgeAlertas  = document.getElementById("badge-alertas");
    const topbarAlertas = document.getElementById("topbar-alertas");
    if (user.rol === "operador") {
      if (badgeAlertas)  badgeAlertas.style.display  = "none";
      if (topbarAlertas) topbarAlertas.style.display = "none";
    }

    setCurrentUser(user.id);
    if (typeof goTo === "function") goTo("dashboard");

    const campanasAdmin = document.getElementById("campanas-admin-section");
    if (campanasAdmin) {
      campanasAdmin.style.display =
        user.rol === "administrador" ? "" : "none";
    }
  },

  mostrarLogin() {
    document.getElementById("login-overlay").style.display = "flex";
    document.querySelector(".sidebar").style.display = "none";
    document.querySelector(".main").style.display    = "none";
  },

  inicializar() {
    if (this.estaAutenticado()) {
      this.mostrarApp();
      // Espera a que app.js esté completamente cargado
      window.addEventListener("load", () => {
        if (typeof checkAlertas === "function") checkAlertas();
      });
    } else {
      this.mostrarLogin();
    }
  }
};