"""
reportes.py — Generación de reportes en CSV
Principio SOLID: Single Responsibility — solo genera archivos de reporte
"""

import csv
import io
from typing import Optional


def generar_csv_completo(conn, periodo: Optional[str] = None) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")  # ; para compatibilidad con Excel español

    # ── ENCABEZADO ────────────────────────────────────────────────────
    writer.writerow(["ECOGESTION - REPORTE PGIRS MUNICIPAL"])
    writer.writerow(["Normativa:", "Decreto 1077/2015 - Ley 142/1994"])
    writer.writerow(["Periodo:", periodo or "Todos los periodos"])
    writer.writerow([])
    writer.writerow([])

    # ── SECCIÓN 1: DIAGNÓSTICOS ───────────────────────────────────────
    writer.writerow(["=" * 60])
    writer.writerow(["SECCION 1: DIAGNOSTICOS INICIALES"])
    writer.writerow(["=" * 60])
    writer.writerow([])
    writer.writerow(["ID", "Año", "Período",
                     "Organico (t)", "Reciclable (t)",
                     "No Aprovechable (t)", "Especial (t)",
                     "TOTAL (t)", "Observaciones"])

    query_diag = "SELECT * FROM diagnosticos"
    params = ()
    if periodo:
        query_diag += " WHERE periodo LIKE ?"
        params = (f"%{periodo}%",)
    query_diag += " ORDER BY anio DESC"

    filas_diag = conn.execute(query_diag, params).fetchall()
    for row in filas_diag:
        total = row["organico"] + row["reciclable"] + \
                row["no_aprovechable"] + row["especial"]
        writer.writerow([
            row["id"], row["anio"], row["periodo"],
            row["organico"], row["reciclable"],
            row["no_aprovechable"], row["especial"],
            round(total, 2), row["observaciones"] or ""
        ])

    if not filas_diag:
        writer.writerow(["Sin registros para el período seleccionado"])

    writer.writerow([])
    writer.writerow(["Subtotal diagnósticos:", len(filas_diag)])
    writer.writerow([])
    writer.writerow([])

    # ── SECCIÓN 2: METAS ──────────────────────────────────────────────
    writer.writerow(["=" * 60])
    writer.writerow(["SECCIÓN 2: METAS PGIRS"])
    writer.writerow(["=" * 60])
    writer.writerow([])
    writer.writerow(["ID", "Período", "Tipo Residuo",
                     "Meta (t)", "Indicador", "Diagnóstico Base"])

    query_meta = "SELECT * FROM metas"
    params = ()
    if periodo:
        query_meta += " WHERE periodo LIKE ?"
        params = (f"%{periodo}%",)
    query_meta += " ORDER BY id DESC"

    filas_meta = conn.execute(query_meta, params).fetchall()
    for row in filas_meta:
        writer.writerow([
            row["id"], row["periodo"], row["tipo_residuo"],
            row["valor_meta"], row["indicador"] or "",
            row["diagnostico_id"] or ""
        ])

    if not filas_meta:
        writer.writerow(["Sin registros para el período seleccionado"])

    writer.writerow([])
    writer.writerow(["Subtotal metas:", len(filas_meta)])
    writer.writerow([])
    writer.writerow([])

    # ── SECCIÓN 3: CANTIDADES ─────────────────────────────────────────
    writer.writerow(["=" * 60])
    writer.writerow(["SECCIÓN 3: CANTIDADES RECOLECTADAS"])
    writer.writerow(["=" * 60])
    writer.writerow([])
    writer.writerow(["ID", "Fecha", "Orgánico (t)", "Reciclable (t)",
                     "No Aprovechable (t)", "Especial (t)", "TOTAL (t)"])

    query_cant = "SELECT * FROM cantidades"
    params = ()
    if periodo:
        query_cant += " WHERE fecha LIKE ?"
        params = (f"{periodo}%",)
    query_cant += " ORDER BY fecha DESC"

    filas_cant = conn.execute(query_cant, params).fetchall()
    for row in filas_cant:
        writer.writerow([
            row["id"], row["fecha"],
            row["organico"], row["reciclable"],
            row["no_aprovechable"], row["especial"],
            row["total"]
        ])

    if not filas_cant:
        writer.writerow(["Sin registros para el período seleccionado"])

    writer.writerow([])
    writer.writerow(["Subtotal registros:", len(filas_cant)])
    writer.writerow([])
    writer.writerow([])

    # ── SECCIÓN 4: RESUMEN ────────────────────────────────────────────
    writer.writerow(["=" * 60])
    writer.writerow(["SECCIÓN 4: RESUMEN DE INDICADORES"])
    writer.writerow(["=" * 60])
    writer.writerow([])
    writer.writerow(["Indicador", "Valor", "Unidad"])

    query_ind = """
        SELECT SUM(organico)        as org,
               SUM(reciclable)      as rec,
               SUM(no_aprovechable) as no_ap,
               SUM(especial)        as esp
        FROM cantidades
    """
    params = ()
    if periodo:
        query_ind += " WHERE fecha LIKE ?"
        params = (f"{periodo}%",)

    row = conn.execute(query_ind, params).fetchone()
    org   = row["org"]   or 0
    rec   = row["rec"]   or 0
    no_ap = row["no_ap"] or 0
    esp   = row["esp"]   or 0
    total = org + rec + no_ap + esp

    writer.writerow(["Total recolectado",    round(total, 2), "toneladas"])
    writer.writerow(["Orgánico",             round(org, 2),   "toneladas"])
    writer.writerow(["Reciclable",           round(rec, 2),   "toneladas"])
    writer.writerow(["No Aprovechable",      round(no_ap, 2), "toneladas"])
    writer.writerow(["Especial",             round(esp, 2),   "toneladas"])
    writer.writerow(["Tasa aprovechamiento",
                     round((org + rec) / total * 100, 1) if total else 0, "%"])
    writer.writerow(["% No Aprovechable",
                     round(no_ap / total * 100, 1) if total else 0, "%"])

    return output.getvalue()