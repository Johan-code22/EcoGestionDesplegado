"""
municipios.py — CRUD de municipios
Principio SOLID: Single Responsibility — solo maneja municipios
"""

import sqlite3
from typing import Optional


def crear_municipio(conn: sqlite3.Connection, data: dict) -> dict:
    """Registra un nuevo municipio en el sistema."""
    cur = conn.execute("""
        INSERT INTO municipios (nombre, departamento, codigo, activo)
        VALUES (?, ?, ?, 0)
    """, (
        data["nombre"],
        data.get("departamento", ""),
        data.get("codigo", ""),
    ))
    conn.commit()
    return obtener_municipio(conn, cur.lastrowid)


def obtener_municipio(conn: sqlite3.Connection,
                      municipio_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM municipios WHERE id = ?", (municipio_id,)
    ).fetchone()
    return dict(row) if row else None


def listar_municipios(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM municipios ORDER BY nombre"
    ).fetchall()
    return [dict(r) for r in rows]


def obtener_activo(conn: sqlite3.Connection) -> Optional[dict]:
    """Retorna el municipio actualmente activo."""
    row = conn.execute(
        "SELECT * FROM municipios WHERE activo = 1 LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def cambiar_municipio_activo(conn: sqlite3.Connection,
                              municipio_id: int) -> bool:
    """
    Cambia el municipio activo.
    Solo puede haber un municipio activo a la vez.
    """
    conn.execute("UPDATE municipios SET activo = 0")
    conn.execute(
        "UPDATE municipios SET activo = 1 WHERE id = ?",
        (municipio_id,)
    )
    conn.commit()
    return True


def calcular_indicadores_municipio(conn: sqlite3.Connection,
                                    municipio_id: int) -> dict:
    """
    Calcula indicadores independientes por municipio.
    SCRUM-19: Los datos se separan por municipio_id.
    """
    row = conn.execute("""
        SELECT SUM(organico)        as org,
               SUM(reciclable)      as rec,
               SUM(no_aprovechable) as no_ap,
               SUM(especial)        as esp,
               COUNT(*)             as cnt
        FROM cantidades
        WHERE municipio_id = ?
    """, (municipio_id,)).fetchone()

    org   = row["org"]   or 0
    rec   = row["rec"]   or 0
    no_ap = row["no_ap"] or 0
    esp   = row["esp"]   or 0
    total = org + rec + no_ap + esp

    def pct(v):
        return round(v / total * 100, 1) if total > 0 else 0.0

    mun = obtener_municipio(conn, municipio_id)

    return {
        "municipio_id":           municipio_id,
        "municipio_nombre":       mun["nombre"] if mun else "—",
        "total_general":          round(total, 2),
        "total_organico":         round(org, 2),
        "total_reciclable":       round(rec, 2),
        "total_no_aprovechable":  round(no_ap, 2),
        "total_especial":         round(esp, 2),
        "pct_organico":           pct(org),
        "pct_reciclable":         pct(rec),
        "pct_no_aprovechable":    pct(no_ap),
        "tasa_aprovechamiento":   pct(org + rec),
        "registros_cantidad":     row["cnt"] or 0,
    }