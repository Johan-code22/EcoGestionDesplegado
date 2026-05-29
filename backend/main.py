"""
EcoGestión — Backend principal
FastAPI + SQLite | Arquitectura cliente-servidor
Normativa: Decreto 1077/2015, Ley 142/1994
"""
import campanas as campanas_module
import puntos_criticos as pc_module
import municipios as municipios_module
from pydantic import BaseModel as PydanticBaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
from auth import verificar_credenciales, crear_sesion, cerrar_sesion, obtener_sesion
from fastapi import Header
from fastapi.responses import StreamingResponse
import reportes
import alertas as alertas_module
import horarios as horarios_module
from pydantic import BaseModel as PydanticBase

from database import init_db, get_db
from models import (
    DiagnosticoCreate, DiagnosticoResponse,
    MetaCreate, MetaResponse,
    ClasificacionCreate, ClasificacionResponse,
    CantidadCreate, CantidadResponse,
    IndicadorResponse,
    UsuarioCreate, UsuarioResponse,
    AccionLogResponse,
)
import crud

# ── Lifespan: inicializa BD al arrancar ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="EcoGestión API",
    description="API REST para la gestión integral de residuos sólidos (PGIRS)",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS: permite llamadas desde el frontend HTML ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════════════
# Diagnóstico Inicial
# ════════════════════════════════════════════════════════════════════

@app.post("/api/diagnosticos", response_model=DiagnosticoResponse, tags=["Diagnóstico"])
def crear_diagnostico(data: DiagnosticoCreate, db=Depends(get_db)):
    """Registra el diagnóstico inicial de residuos (línea base PGIRS)."""
    return crud.crear_diagnostico(db, data)

@app.get("/api/diagnosticos", response_model=list[DiagnosticoResponse], tags=["Diagnóstico"])
def listar_diagnosticos(db=Depends(get_db)):
    """Consulta todos los diagnósticos registrados."""
    return crud.listar_diagnosticos(db)

@app.get("/api/diagnosticos/{diagnostico_id}", response_model=DiagnosticoResponse, tags=["Diagnóstico"])
def obtener_diagnostico(diagnostico_id: int, db=Depends(get_db)):
    diag = crud.obtener_diagnostico(db, diagnostico_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    return diag

# ════════════════════════════════════════════════════════════════════
# Metas PGIRS
# ════════════════════════════════════════════════════════════════════

@app.post("/api/metas", response_model=MetaResponse, tags=["Metas"])
def crear_meta(data: MetaCreate, db=Depends(get_db)):
    """Define una meta de reducción/aprovechamiento de residuos."""
    return crud.crear_meta(db, data)

@app.get("/api/metas", response_model=list[MetaResponse], tags=["Metas"])
def listar_metas(periodo: Optional[str] = None, db=Depends(get_db)):
    """Lista todas las metas, con filtro opcional por período."""
    return crud.listar_metas(db, periodo)

# ════════════════════════════════════════════════════════════════════
# Clasificación de Residuos
# ════════════════════════════════════════════════════════════════════

@app.post("/api/clasificaciones", response_model=ClasificacionResponse, tags=["Clasificación"])
def crear_clasificacion(data: ClasificacionCreate, db=Depends(get_db)):
    """Registra la clasificación de residuos recolectados."""
    return crud.crear_clasificacion(db, data)

@app.get("/api/clasificaciones", response_model=list[ClasificacionResponse], tags=["Clasificación"])
def listar_clasificaciones(db=Depends(get_db)):
    """Consulta todos los registros de clasificación."""
    return crud.listar_clasificaciones(db)

# ════════════════════════════════════════════════════════════════════
# Cantidades Recolectadas
# ════════════════════════════════════════════════════════════════════

@app.post("/api/cantidades", response_model=CantidadResponse, tags=["Cantidades"])
def registrar_cantidad(data: CantidadCreate, db=Depends(get_db)):
    """Registra las cantidades de residuos recolectados por tipo."""
    return crud.crear_cantidad(db, data)

@app.get("/api/cantidades", response_model=list[CantidadResponse], tags=["Cantidades"])
def listar_cantidades(db=Depends(get_db)):
    """Lista el historial de cantidades recolectadas."""
    return crud.listar_cantidades(db)

# ════════════════════════════════════════════════════════════════════
# Indicadores PGIRS
# ════════════════════════════════════════════════════════════════════

@app.get("/api/indicadores", response_model=IndicadorResponse, tags=["Indicadores"])
def obtener_indicadores(periodo: Optional[str] = None, db=Depends(get_db)):
    """
    Devuelve los indicadores consolidados por categoría.
    Se actualizan dinámicamente con base en los registros almacenados.
    """
    return crud.calcular_indicadores(db, periodo)

@app.get("/api/indicadores/historico", tags=["Indicadores"])
def obtener_historico(db=Depends(get_db)):
    """
    Retorna cantidades agrupadas por fecha para gráfica de evolución.
    """
    return crud.obtener_historico_cantidades(db)

# ════════════════════════════════════════════════════════════════════
#  Usuarios / Roles / Trazabilidad
# ════════════════════════════════════════════════════════════════════

@app.post("/api/usuarios", response_model=UsuarioResponse, tags=["Usuarios"])
def crear_usuario(data: UsuarioCreate, db=Depends(get_db)):
    """Crea un usuario con rol administrador u operador."""
    return crud.crear_usuario(db, data)

@app.get("/api/usuarios", response_model=list[UsuarioResponse], tags=["Usuarios"])
def listar_usuarios(db=Depends(get_db)):
    return crud.listar_usuarios(db)

@app.get("/api/acciones", response_model=list[AccionLogResponse], tags=["Trazabilidad"])
def listar_acciones(db=Depends(get_db)):
    """Retorna el historial de acciones del sistema (auditoría)."""
    return crud.listar_acciones(db)

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Sistema"])
def health(db=Depends(get_db)):
    """
    SCRUM-20: Health check ampliado que verifica BD y tablas críticas.
    Usado para monitorear disponibilidad del sistema.
    """
    try:
        # Verifica que la BD responde
        db.execute("SELECT 1").fetchone()

        # Verifica tablas críticas
        tablas = ["usuarios", "diagnosticos", "cantidades",
                  "clasificaciones", "alertas", "horarios_recoleccion"]
        for tabla in tablas:
            db.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()

        return {
            "status": "ok",
            "sistema": "EcoGestión",
            "version": "1.0.0",
            "base_datos": "conectada",
            "tablas": "verificadas",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Sistema no disponible: {str(e)}"
        )

# ════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ════════════════════════════════════════════════════════════════════

@app.post("/api/login", tags=["Autenticación"])
def login(data: dict, db=Depends(get_db)):
    """Valida credenciales y retorna token de sesión."""
    usuario = verificar_credenciales(db, data.get("usuario"), data.get("password"))
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = crear_sesion(usuario)
    return {
        "token": token,
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
    }

@app.post("/api/logout", tags=["Autenticación"])
def logout(authorization: str = Header(None)):
    """Cierra la sesión eliminando el token."""
    if authorization:
        cerrar_sesion(authorization.replace("Bearer ", ""))
    return {"mensaje": "Sesión cerrada"}

@app.get("/api/me", tags=["Autenticación"])
def me(authorization: str = Header(None)):
    """Retorna los datos del usuario autenticado."""
    token = (authorization or "").replace("Bearer ", "")
    sesion = obtener_sesion(token)
    if not sesion:
        raise HTTPException(status_code=401, detail="No autenticado")
    return sesion   

# ════════════════════════════════════════════════════════════════════
# Reportes CSV
# ════════════════════════════════════════════════════════════════════

@app.get("/api/reportes/csv", tags=["Reportes"])
def descargar_reporte_csv(periodo: Optional[str] = None, db=Depends(get_db)):
    """
    Genera y descarga un reporte CSV con diagnósticos,
    metas y cantidades del período indicado.
    """
    contenido = reportes.generar_csv_completo(db, periodo)

    nombre = f"reporte_pgirs_{periodo or 'completo'}.csv"

    return StreamingResponse(
        iter([contenido]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre}"}
    )

# ════════════════════════════════════════════════════════════════════
# SCRUM-15 · Alertas orgánico >48h
# ════════════════════════════════════════════════════════════════════

@app.get("/api/alertas", tags=["Alertas"])
def obtener_alertas(db=Depends(get_db)):
    """
    Evalúa clasificaciones orgánicas y retorna todas las alertas.
    Genera nuevas alertas si encuentra residuos con más de 48h.
    """
    alertas_module.evaluar_alertas_organico(db)
    return alertas_module.listar_alertas(db)

@app.get("/api/alertas/count", tags=["Alertas"])
def contar_alertas(db=Depends(get_db)):
    """Retorna el número de alertas activas para el badge."""
    alertas_module.evaluar_alertas_organico(db)
    count = alertas_module.contar_alertas_activas(db)
    return {"count": count}

@app.patch("/api/alertas/{alerta_id}/resolver", tags=["Alertas"])
def resolver_alerta(alerta_id: int, db=Depends(get_db)):
    """Marca una alerta como resuelta."""
    alertas_module.resolver_alerta(db, alerta_id)
    _log_accion(db, alerta_id)
    return {"mensaje": "Alerta resuelta correctamente"}

def _log_accion(db, alerta_id: int):
    db.execute(
        "INSERT INTO acciones_log (accion, entidad, detalle) VALUES (?,?,?)",
        ("UPDATE", "alertas", f"Alerta #{alerta_id} marcada como resuelta")
    )

# ════════════════════════════════════════════════════════════════════
# SCRUM-13 · Horarios de recolección (acceso público)
# ════════════════════════════════════════════════════════════════════

class HorarioCreate(PydanticBase):
    zona: str
    dias: str
    hora_inicio: str
    hora_fin: str
    tipo_residuo: Optional[str] = "General"


@app.get("/api/horarios", tags=["Horarios"])
def listar_horarios(zona: Optional[str] = None, db=Depends(get_db)):
    """
    Lista horarios de recolección activos.
    Acceso público — no requiere autenticación.
    """
    return horarios_module.listar_horarios(db, zona)


@app.get("/api/horarios/zonas", tags=["Horarios"])
def listar_zonas(db=Depends(get_db)):
    """Retorna las zonas disponibles con horarios activos."""
    return horarios_module.listar_zonas(db)


@app.post("/api/horarios", tags=["Horarios"])
def crear_horario(data: HorarioCreate, db=Depends(get_db)):
    """Crea un horario nuevo. Solo administradores."""
    return horarios_module.crear_horario(db, data.model_dump())


@app.patch("/api/horarios/{horario_id}/estado", tags=["Horarios"])
def cambiar_estado_horario(horario_id: int,
                           activo: bool = True,
                           db=Depends(get_db)):
    """Activa o desactiva un horario."""
    horarios_module.activar_desactivar(db, horario_id, activo)
    return {"mensaje": f"Horario {'activado' if activo else 'desactivado'}"}

# ════════════════════════════════════════════════════════════════════
# SCRUM-18 · Campañas de educación ambiental
# ════════════════════════════════════════════════════════════════════

class CampanaCreate(PydanticBaseModel):
    titulo: str
    descripcion: str
    periodo: Optional[str] = ""


@app.get("/api/campanas", tags=["Campañas"])
def listar_campanas(solo_activas: bool = False, db=Depends(get_db)):
    """
    Lista campañas de educación ambiental.
    Con solo_activas=true retorna solo las visibles para ciudadanos.
    """
    return campanas_module.listar_campanas(db, solo_activas)


@app.post("/api/campanas", tags=["Campañas"])
def crear_campana(data: CampanaCreate, db=Depends(get_db)):
    """Crea una nueva campaña. Solo administradores."""
    campana = campanas_module.crear_campana(db, data.model_dump())
    return campana


@app.patch("/api/campanas/{campana_id}/estado", tags=["Campañas"])
def cambiar_estado_campana(campana_id: int,
                           activa: bool = True,
                           db=Depends(get_db)):
    """Activa o desactiva una campaña."""
    campanas_module.cambiar_estado(db, campana_id, activa)
    return {"mensaje": f"Campaña {'activada' if activa else 'desactivada'}"}


@app.delete("/api/campanas/{campana_id}", tags=["Campañas"])
def eliminar_campana(campana_id: int, db=Depends(get_db)):
    """Elimina una campaña permanentemente."""
    campanas_module.eliminar_campana(db, campana_id)
    return {"mensaje": "Campaña eliminada correctamente"}

# ════════════════════════════════════════════════════════════════════
# SCRUM-14 · Puntos críticos de residuos
# ════════════════════════════════════════════════════════════════════

class PuntoCriticoCreate(PydanticBaseModel):
    descripcion: str
    ubicacion:   Optional[str] = "Sin especificar"
    imagen_url:  Optional[str] = ""


@app.get("/api/puntos-criticos", tags=["Puntos Críticos"])
def listar_puntos_criticos(estado: Optional[str] = None,
                            db=Depends(get_db)):
    """
    Lista reportes de puntos críticos.
    Acceso: administrador consulta todos los reportes.
    Filtro opcional por estado: pendiente, en_proceso, resuelto.
    """
    return pc_module.listar_reportes(db, estado)


@app.post("/api/puntos-criticos", tags=["Puntos Críticos"])
def crear_punto_critico(data: PuntoCriticoCreate,
                         db=Depends(get_db)):
    """
    Crea un reporte de punto crítico.
    Acceso público — cualquier ciudadano puede reportar.
    """
    return pc_module.crear_reporte(db, data.model_dump())


@app.patch("/api/puntos-criticos/{reporte_id}/estado",
           tags=["Puntos Críticos"])
def actualizar_estado_reporte(reporte_id: int,
                               estado: str,
                               db=Depends(get_db)):
    """Actualiza el estado de un reporte. Solo administradores."""
    ok = pc_module.cambiar_estado(db, reporte_id, estado)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Use: pendiente, en_proceso, resuelto"
        )
    return {"mensaje": f"Estado actualizado a '{estado}'"}


@app.get("/api/puntos-criticos/resumen", tags=["Puntos Críticos"])
def resumen_puntos_criticos(db=Depends(get_db)):
    """Retorna conteo de reportes por estado para el dashboard."""
    return pc_module.contar_por_estado(db)

# ════════════════════════════════════════════════════════════════════
# SCRUM-19 · Multi-municipio
# ════════════════════════════════════════════════════════════════════

class MunicipioCreate(PydanticBaseModel):
    nombre:       str
    departamento: Optional[str] = ""
    codigo:       Optional[str] = ""


@app.get("/api/municipios", tags=["Municipios"])
def listar_municipios(db=Depends(get_db)):
    """Lista todos los municipios registrados."""
    return municipios_module.listar_municipios(db)


@app.get("/api/municipios/activo", tags=["Municipios"])
def municipio_activo(db=Depends(get_db)):
    """Retorna el municipio actualmente activo."""
    mun = municipios_module.obtener_activo(db)
    if not mun:
        raise HTTPException(status_code=404,
                            detail="No hay municipio activo")
    return mun


@app.post("/api/municipios", tags=["Municipios"])
def crear_municipio(data: MunicipioCreate, db=Depends(get_db)):
    """Registra un nuevo municipio. Solo administradores."""
    return municipios_module.crear_municipio(db, data.model_dump())


@app.patch("/api/municipios/{municipio_id}/activar", tags=["Municipios"])
def activar_municipio(municipio_id: int, db=Depends(get_db)):
    """
    Cambia el municipio activo.
    Todos los registros nuevos se asociarán a este municipio.
    """
    municipios_module.cambiar_municipio_activo(db, municipio_id)
    mun = municipios_module.obtener_municipio(db, municipio_id)
    return {"mensaje": f"Municipio activo: {mun['nombre']}"}


@app.get("/api/municipios/{municipio_id}/indicadores",
         tags=["Municipios"])
def indicadores_por_municipio(municipio_id: int, db=Depends(get_db)):
    """
    Calcula indicadores independientes para un municipio específico.
    SCRUM-19: Los datos se separan completamente por municipio.
    """
    return municipios_module.calcular_indicadores_municipio(
        db, municipio_id
    )