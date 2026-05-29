"""
puntos_criticos.py — CRUD de puntos críticos de residuos
Principio SOLID: Single Responsibility — solo maneja puntos críticos
Acceso: ciudadano crea reportes, administrador los consulta
"""

import sqlite3
from typing import Optional


def crear_reporte(conn: sqlite3.Connection, data: dict) -> dict:
    """Crea un reporte de punto crítico de residuos."""
    cur = conn.execute("""
        INSERT INTO puntos_criticos
        (descripcion, ubicacion, imagen_url, estado)
        VALUES (?, ?, ?, 'pendiente')
    """, (
        data["descripcion"],
        data.get("ubicacion", "Sin especificar"),
        data.get("imagen_url", ""),
    ))
    conn.commit()
    return obtener_reporte(conn, cur.lastrowid)


def obtener_reporte(conn: sqlite3.Connection, reporte_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM puntos_criticos WHERE id = ?", (reporte_id,)
    ).fetchone()
    return dict(row) if row else None


def listar_reportes(conn: sqlite3.Connection,
                    estado: Optional[str] = None) -> list[dict]:
    """Lista reportes con filtro opcional por estado."""
    if estado:
        rows = conn.execute("""
            SELECT * FROM puntos_criticos
            WHERE estado = ?
            ORDER BY creado_en DESC
        """, (estado,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM puntos_criticos
            ORDER BY creado_en DESC
        """).fetchall()
    return [dict(r) for r in rows]


def cambiar_estado(conn: sqlite3.Connection,
                   reporte_id: int, estado: str) -> bool:
    """Cambia el estado de un reporte: pendiente, en_proceso, resuelto."""
    estados_validos = ("pendiente", "en_proceso", "resuelto")
    if estado not in estados_validos:
        return False
    conn.execute(
        "UPDATE puntos_criticos SET estado = ? WHERE id = ?",
        (estado, reporte_id)
    )
    conn.commit()
    return True


def contar_por_estado(conn: sqlite3.Connection) -> dict:
    """Retorna conteo de reportes agrupados por estado."""
    rows = conn.execute("""
        SELECT estado, COUNT(*) as total
        FROM puntos_criticos
        GROUP BY estado
    """).fetchall()
    resultado = {"pendiente": 0, "en_proceso": 0, "resuelto": 0}
    for r in rows:
        resultado[r["estado"]] = r["total"]
    return resultado