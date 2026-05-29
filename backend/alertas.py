"""
alertas.py — Lógica de alertas por almacenamiento orgánico
Principio SOLID: Single Responsibility — solo evalúa y genera alertas
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional


def evaluar_alertas_organico(conn: sqlite3.Connection) -> list[dict]:
    """
    Revisa clasificaciones de tipo Orgánico y genera alerta
    si han pasado más de 48 horas desde la fecha de recolección.
    """
    limite_horas = 48
    ahora = datetime.now()

    clasificaciones = conn.execute("""
        SELECT c.* FROM clasificaciones c
        WHERE c.tipo_residuo = 'Orgánico'
        AND c.id NOT IN (
            SELECT entidad_id FROM alertas
            WHERE entidad = 'clasificaciones'
        )
    """).fetchall()

    nuevas_alertas = []

    for c in clasificaciones:
        fecha_rec = None
        try:
            fecha_rec = datetime.strptime(c["fecha_recoleccion"], "%Y-%m-%d")
        except ValueError:
            continue  # Si la fecha no tiene formato válido, salta este registro

        diferencia = ahora - fecha_rec
        horas_transcurridas = diferencia.total_seconds() / 3600

        if horas_transcurridas > limite_horas:
            cur = conn.execute("""
                INSERT INTO alertas
                (tipo, mensaje, entidad, entidad_id, horas_transcurridas)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "organico_48h",
                f"Residuo orgánico lleva {int(horas_transcurridas)}h almacenado "
                f"(zona: {c['ruta_zona'] or 'sin especificar'})",
                "clasificaciones",
                c["id"],
                round(horas_transcurridas, 1),
            ))
            conn.commit()

            nuevas_alertas.append({
                "id": cur.lastrowid,
                "tipo": "organico_48h",
                "mensaje": f"Residuo orgánico lleva {int(horas_transcurridas)}h "
                           f"almacenado (zona: {c['ruta_zona'] or 'sin especificar'})",
                "entidad": "clasificaciones",
                "entidad_id": c["id"],
                "horas_transcurridas": round(horas_transcurridas, 1),
            })

    return nuevas_alertas


def listar_alertas(conn: sqlite3.Connection) -> list[dict]:
    """Retorna todas las alertas registradas, más recientes primero."""
    rows = conn.execute("""
        SELECT * FROM alertas ORDER BY generada_en DESC
    """).fetchall()
    return [dict(r) for r in rows]


def contar_alertas_activas(conn: sqlite3.Connection) -> int:
    """Retorna el número de alertas no resueltas."""
    row = conn.execute(
        "SELECT COUNT(*) FROM alertas WHERE resuelta = 0"
    ).fetchone()
    return row[0] or 0


def resolver_alerta(conn: sqlite3.Connection, alerta_id: int) -> bool:
    """Marca una alerta como resuelta."""
    conn.execute(
        "UPDATE alertas SET resuelta = 1 WHERE id = ?", (alerta_id,)
    )
    conn.commit()
    return True