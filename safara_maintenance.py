"""Sincronización no bloqueante de informes y copias administrativas."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from datetime import date
from typing import Any

import pandas as pd

from safara_google_storage import GoogleSafaraStorage, StorageOperationError
from safara_supabase_storage import SupabaseSafaraStorage, SupabaseStorageOperationError


def _csv_bytes(records: list[dict[str, Any]]) -> bytes:
    columns = list(records[0].keys()) if records else []
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    if columns:
        writer.writeheader()
        writer.writerows(records)
    return output.getvalue().encode("utf-8")


def crear_paquete_financiero_descargable(
    snapshot: dict[str, list[dict[str, Any]]],
) -> bytes:
    """Crea una descarga fiscal desde datos actuales, sin exponer credenciales.

    Los justificantes permanecen en Drive, donde conservan su control de acceso;
    el libro incluye sus enlaces para localizar cada documento de inmediato.
    """
    files: dict[str, bytes] = {
        f"{name}.csv": _csv_bytes(records) for name, records in snapshot.items()
    }
    workbook = io.BytesIO()
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        pd.DataFrame([
            {
                "Generado": date.today().isoformat(),
                "Origen": "Base segura SAFARA",
                "Alcance": "Gastos, caja y actuaciones",
                "Justificantes": "Enlaces incluidos en la hoja gastos; originales protegidos en Google Drive.",
            }
        ]).to_excel(writer, sheet_name="Resumen", index=False)
        for name, records in snapshot.items():
            pd.DataFrame(records).to_excel(
                writer, sheet_name=name.capitalize()[:31], index=False
            )
    files["SAFARA_Archivo_Financiero.xlsx"] = workbook.getvalue()
    manifest = {
        "fecha": date.today().isoformat(),
        "contenido": {name: len(records) for name, records in snapshot.items()},
        "nota": (
            "Copia administrativa generada desde Supabase; los tickets originales "
            "permanecen protegidos en Google Drive y se localizan con sus enlaces."
        ),
        "sha256_archivos": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in files.items()
        },
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        for name, payload in files.items():
            package.writestr(name, payload)
        package.writestr("MANIFIESTO.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return archive.getvalue()


# Nombre privado conservado para que las copias automáticas existentes sigan
# llamando al mismo generador validado.
_create_financial_archive = crear_paquete_financiero_descargable


def run_google_maintenance(
    database: SupabaseSafaraStorage,
    google: GoogleSafaraStorage | None,
) -> bool:
    """Sincroniza una copia de consulta sin interrumpir ninguna acción de la app."""
    if google is None:
        return False
    try:
        # La organización de Drive es una mejora documental: conserva los
        # identificadores y enlaces existentes, y nunca puede bloquear los
        # informes ni una acción principal del grupo.
        try:
            for ticket in google.organizar_justificantes_archivados(
                database.listar_justificantes_para_archivar()
            ):
                database.confirmar_nombre_justificante(
                    int(ticket["gasto_id"]), str(ticket["fichero"])
                )
        except Exception:
            pass
        work = database.iniciar_mantenimiento_google()
        if not work:
            return False
        reports = database.obtener_informes_google()
        reports["Informe Sincronización"] = [{
            "Estado": "Sincronizado desde Supabase",
            "Última actualización": date.today().isoformat(),
            "Origen": "SAFARA GASTOS — pruebas",
        }]
        google.write_report_snapshot(reports)
        # Desde este punto los informes ya están actualizados. La copia diaria
        # de Drive es una protección adicional y no puede deshacer Sheets.
        database.confirmar_informes_google(int(work["sheets_revision"]))
        backup_done = False
        if work["respaldo_pendiente"]:
            try:
                archive = _create_financial_archive(database.obtener_archivo_financiero())
                google.upload_backup(f"SAFARA_GASTOS_{date.today().isoformat()}.zip", archive)
                backup_done = True
            except Exception as error:
                database.fallar_respaldo_google(
                    str(error) or "No se pudo guardar la copia adicional de Drive."
                )
                return True
        database.terminar_mantenimiento_google(int(work["sheets_revision"]), backup_done)
        return True
    except Exception as error:
        # Google es únicamente una vista de consulta y una copia adicional:
        # una incidencia suya jamás debe propagarse a quien acaba de registrar
        # un gasto, votar o gestionar una actuación en Supabase.
        database.fallar_mantenimiento_google(str(error) or "No se pudo actualizar Google.")
        return False
