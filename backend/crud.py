"""
crud.py — Operaciones de base de datos
Principio SOLID: cada función tiene una única responsabilidad.
Separado de main.py (Dependency Inversion / Single Responsibility).
"""

import sqlite3
from datetime import date
from typing import Optional

from models import (
    DiagnosticoCreate, MetaCreate,
    ClasificacionCreate, CantidadCreate,
    UsuarioCreate,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _log(conn: sqlite3.Connection, accion: str, entidad: str,
         detalle: str = "", usuario_id: Optional[int] = None):
    conn.execute(
        "INSERT INTO acciones_log (accion, entidad, detalle, usuario_id) VALUES (?,?,?,?)",
        (accion, entidad, detalle, usuario_id),
    )


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ── USUARIOS ──────────────────────────────────────────────────────────────────

def crear_usuario(conn, data: UsuarioCreate):
    cur = conn.execute(
        "INSERT INTO usuarios (nombre, rol) VALUES (?,?)",
        (data.nombre, data.rol),
    )
    _log(conn, "CREATE", "usuarios", f"Usuario '{data.nombre}' ({data.rol})")
    return obtener_usuario(conn, cur.lastrowid)


def obtener_usuario(conn, uid: int):
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
    return _row_to_dict(row) if row else None


def listar_usuarios(conn):
    rows = conn.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [_row_to_dict(r) for r in rows]


# ── DIAGNÓSTICO (SCRUM-7) ────────────────────────────────────────────────────

def crear_diagnostico(conn, data: DiagnosticoCreate):
    cur = conn.execute(
        """INSERT INTO diagnosticos
           (anio, periodo, organico, reciclable, no_aprovechable, especial, observaciones, usuario_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (data.anio, data.periodo, data.organico, data.reciclable,
         data.no_aprovechable, data.especial, data.observaciones, data.usuario_id),
    )
    _log(conn, "CREATE", "diagnosticos",
         f"Diagnóstico {data.anio}/{data.periodo} registrado", data.usuario_id)
    return obtener_diagnostico(conn, cur.lastrowid)


def obtener_diagnostico(conn, diag_id: int):
    row = conn.execute("SELECT * FROM diagnosticos WHERE id=?", (diag_id,)).fetchone()
    if not row:
        return None
    d = _row_to_dict(row)
    d["total"] = d["organico"] + d["reciclable"] + d["no_aprovechable"] + d["especial"]
    return d


def listar_diagnosticos(conn):
    rows = conn.execute(
        "SELECT * FROM diagnosticos ORDER BY anio DESC, id DESC"
    ).fetchall()
    result = []
    for r in rows:
        d = _row_to_dict(r)
        d["total"] = d["organico"] + d["reciclable"] + d["no_aprovechable"] + d["especial"]
        result.append(d)
    return result


# ── METAS (SCRUM-8) ──────────────────────────────────────────────────────────

def crear_meta(conn, data: MetaCreate):
    cur = conn.execute(
        """INSERT INTO metas
           (periodo, tipo_residuo, valor_meta, indicador, diagnostico_id, usuario_id)
           VALUES (?,?,?,?,?,?)""",
        (data.periodo, data.tipo_residuo, data.valor_meta,
         data.indicador, data.diagnostico_id, data.usuario_id),
    )
    _log(conn, "CREATE", "metas",
         f"Meta {data.tipo_residuo} para {data.periodo}: {data.valor_meta} t",
         data.usuario_id)
    row = conn.execute("SELECT * FROM metas WHERE id=?", (cur.lastrowid,)).fetchone()
    return _row_to_dict(row)


def listar_metas(conn, periodo: Optional[str] = None):
    if periodo:
        rows = conn.execute(
            "SELECT * FROM metas WHERE periodo=? ORDER BY id DESC", (periodo,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM metas ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


# ── CLASIFICACIONES (SCRUM-9) ────────────────────────────────────────────────

def crear_clasificacion(conn, data: ClasificacionCreate):
    cur = conn.execute(
        """INSERT INTO clasificaciones
           (tipo_residuo, fecha_recoleccion, ruta_zona, vehiculo, observaciones, usuario_id)
           VALUES (?,?,?,?,?,?)""",
        (data.tipo_residuo, data.fecha_recoleccion, data.ruta_zona,
         data.vehiculo, data.observaciones, data.usuario_id),
    )
    _log(conn, "CREATE", "clasificaciones",
         f"Clasificación {data.tipo_residuo} — {data.ruta_zona}", data.usuario_id)
    row = conn.execute("SELECT * FROM clasificaciones WHERE id=?", (cur.lastrowid,)).fetchone()
    return _row_to_dict(row)


def listar_clasificaciones(conn):
    rows = conn.execute(
        "SELECT * FROM clasificaciones ORDER BY fecha_recoleccion DESC, id DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── CANTIDADES (SCRUM-10) ────────────────────────────────────────────────────

def crear_cantidad(conn, data: CantidadCreate):
    fecha = data.fecha or date.today().isoformat()
    cur = conn.execute(
        """INSERT INTO cantidades
           (fecha, organico, reciclable, no_aprovechable, especial, usuario_id)
           VALUES (?,?,?,?,?,?)""",
        (fecha, data.organico, data.reciclable,
         data.no_aprovechable, data.especial, data.usuario_id),
    )
    total = data.organico + data.reciclable + data.no_aprovechable + data.especial
    _log(conn, "CREATE", "cantidades",
         f"Cantidad registrada: {total:.2f} t — {fecha}", data.usuario_id)
    row = conn.execute("SELECT * FROM cantidades WHERE id=?", (cur.lastrowid,)).fetchone()
    return _row_to_dict(row)


def listar_cantidades(conn, limite: int = 100) -> list[dict]:
    """
    SCRUM-20: Límite de registros para mantener respuesta rápida.
    """
    rows = conn.execute(
        "SELECT * FROM cantidades ORDER BY fecha DESC, id DESC LIMIT ?",
        (limite,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── INDICADORES (SCRUM-11) ───────────────────────────────────────────────────

def calcular_indicadores(conn, periodo: Optional[str] = None):
    """
    Agrega las cantidades recolectadas.
    Si se pasa `periodo` (ej. '2025-03'), filtra por mes.
    Los indicadores se calculan siempre desde los registros reales.
    """
    query = "SELECT SUM(organico), SUM(reciclable), SUM(no_aprovechable), SUM(especial), COUNT(*) FROM cantidades"
    params = ()
    if periodo:
        query += " WHERE fecha LIKE ?"
        params = (f"{periodo}%",)

    row = conn.execute(query, params).fetchone()
    org   = row[0] or 0.0
    rec   = row[1] or 0.0
    no_ap = row[2] or 0.0
    esp   = row[3] or 0.0
    cnt   = row[4] or 0
    total = org + rec + no_ap + esp

    def pct(v):
        return round(v / total * 100, 1) if total > 0 else 0.0

    return {
        "periodo": periodo,
        "total_general": round(total, 2),
        "total_organico": round(org, 2),
        "total_reciclable": round(rec, 2),
        "total_no_aprovechable": round(no_ap, 2),
        "total_especial": round(esp, 2),
        "pct_organico": pct(org),
        "pct_reciclable": pct(rec),
        "pct_no_aprovechable": pct(no_ap),
        "tasa_aprovechamiento": pct(org + rec),
        "registros_cantidad": cnt,
    }


# ── TRAZABILIDAD (SCRUM-12) ──────────────────────────────────────────────────

def listar_acciones(conn, limite: int = 50) -> list[dict]:
    """
    Retorna el historial de acciones con límite configurable.
    SCRUM-20: Paginación para mantener rendimiento estable.
    """
    rows = conn.execute(
        "SELECT * FROM acciones_log ORDER BY fecha_hora DESC LIMIT ?",
        (limite,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def obtener_historico_cantidades(conn):
    """
    Agrupa cantidades por fecha para la gráfica de evolución.
    Retorna los últimos 7 registros ordenados por fecha.
    """
    rows = conn.execute("""
        SELECT fecha,
               SUM(organico)        as organico,
               SUM(reciclable)      as reciclable,
               SUM(no_aprovechable) as no_aprovechable,
               SUM(organico + reciclable + no_aprovechable + especial) as total
        FROM cantidades
        GROUP BY fecha
        ORDER BY fecha DESC
        LIMIT 7
    """).fetchall()
    # Invertir para que la gráfica vaya de más antiguo a más reciente
    return [_row_to_dict(r) for r in reversed(rows)]