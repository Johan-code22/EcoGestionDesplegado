"""
campanas.py — CRUD de campañas de educación ambiental
Principio SOLID: Single Responsibility — solo maneja campañas
"""

import sqlite3
from typing import Optional


def crear_campana(conn: sqlite3.Connection, data: dict) -> dict:
    """Crea una nueva campaña de educación ambiental."""
    cur = conn.execute("""
        INSERT INTO campanas
        (titulo, descripcion, periodo, activa)
        VALUES (?, ?, ?, 1)
    """, (
        data["titulo"],
        data["descripcion"],
        data.get("periodo", ""),
    ))
    conn.commit()
    return obtener_campana(conn, cur.lastrowid)


def obtener_campana(conn: sqlite3.Connection, campana_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM campanas WHERE id = ?", (campana_id,)
    ).fetchone()
    return dict(row) if row else None


def listar_campanas(conn: sqlite3.Connection,
                    solo_activas: bool = False) -> list[dict]:
    """Lista campañas. Si solo_activas=True retorna solo las activas."""
    if solo_activas:
        rows = conn.execute("""
            SELECT * FROM campanas
            WHERE activa = 1
            ORDER BY creado_en DESC
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM campanas
            ORDER BY creado_en DESC
        """).fetchall()
    return [dict(r) for r in rows]


def cambiar_estado(conn: sqlite3.Connection,
                   campana_id: int, activa: bool) -> bool:
    """Activa o desactiva una campaña."""
    conn.execute(
        "UPDATE campanas SET activa = ? WHERE id = ?",
        (1 if activa else 0, campana_id)
    )
    conn.commit()
    return True


def eliminar_campana(conn: sqlite3.Connection, campana_id: int) -> bool:
    """Elimina una campaña permanentemente."""
    conn.execute("DELETE FROM campanas WHERE id = ?", (campana_id,))
    conn.commit()
    return True