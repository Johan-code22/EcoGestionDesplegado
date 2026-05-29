"""
horarios.py — CRUD de horarios de recolección por zona
Principio SOLID: Single Responsibility — solo maneja horarios
Acceso público sin autenticación (criterio de aceptación SCRUM-13)
"""

import sqlite3
from typing import Optional


def crear_horario(conn: sqlite3.Connection, data: dict) -> dict:
    """Crea un horario de recolección para una zona."""
    cur = conn.execute("""
        INSERT INTO horarios_recoleccion
        (zona, dias, hora_inicio, hora_fin, tipo_residuo, activo)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (
        data["zona"],
        data["dias"],
        data["hora_inicio"],
        data["hora_fin"],
        data.get("tipo_residuo", "General"),
    ))
    conn.commit()
    return obtener_horario(conn, cur.lastrowid)


def obtener_horario(conn: sqlite3.Connection, horario_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM horarios_recoleccion WHERE id = ?", (horario_id,)
    ).fetchone()
    return dict(row) if row else None


def listar_horarios(conn: sqlite3.Connection,
                    zona: Optional[str] = None) -> list[dict]:
    """Lista horarios activos, con filtro opcional por zona."""
    if zona:
        rows = conn.execute("""
            SELECT * FROM horarios_recoleccion
            WHERE activo = 1 AND zona LIKE ?
            ORDER BY zona, hora_inicio
        """, (f"%{zona}%",)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM horarios_recoleccion
            WHERE activo = 1
            ORDER BY zona, hora_inicio
        """).fetchall()
    return [dict(r) for r in rows]


def listar_zonas(conn: sqlite3.Connection) -> list[str]:
    """Retorna la lista de zonas únicas con horarios activos."""
    rows = conn.execute("""
        SELECT DISTINCT zona FROM horarios_recoleccion
        WHERE activo = 1 ORDER BY zona
    """).fetchall()
    return [r["zona"] for r in rows]


def activar_desactivar(conn: sqlite3.Connection,
                       horario_id: int, activo: bool) -> bool:
    """Activa o desactiva un horario."""
    conn.execute(
        "UPDATE horarios_recoleccion SET activo = ? WHERE id = ?",
        (1 if activo else 0, horario_id)
    )
    conn.commit()
    return True