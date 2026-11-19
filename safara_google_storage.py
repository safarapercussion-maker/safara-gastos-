"""Almacenamiento persistente de la versión de pruebas en Google Sheets y Drive.

Las credenciales nunca se guardan en el repositorio. Este módulo acepta solo la
configuración servida por Streamlit Secrets y usa una cuenta de servicio con
acceso limitado a una hoja y una carpeta concretas.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


class StorageConfigurationError(RuntimeError):
    """La integración se ha activado pero no está configurada de forma válida."""


class StorageOperationError(RuntimeError):
    """No se ha podido completar una operación remota sin riesgo de pérdida local."""


SHEET_SCHEMA: dict[str, list[str]] = {
    "Usuarios": [
        "Nombre", "rol", "password_salt", "password_hash", "email", "tel",
        "fnac", "instrumento", "rgpd",
    ],
    "Invitaciones": [
        "codigo_hash", "emitido_por", "creado_en", "caduca_en", "usado_por", "usado_en",
    ],
    "Votos": ["encuesta_id", "ciclo_id", "usuario_id", "respuesta", "actualizado_en"],
    "Actuaciones": ["id", "titulo", "fecha", "hora", "lugar", "estado", "sheet_col"],
    "Gastos": [
        "ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado",
        "Enlace Ticket", "Drive File ID", "MIME Type",
    ],
    "Confesionario": ["usuario", "mensaje", "fecha"],
    "Caja": ["clave", "valor"],
    "Auditoria": ["fecha_hora", "evento", "usuario", "detalle"],
}

# Estas pestañas son un informe de consulta, nunca la fuente de datos.
# Se excluyen contraseñas, hashes, fecha de nacimiento, teléfonos y códigos.
REPORT_SCHEMA: dict[str, list[str]] = {
    "Informe Socios": ["Nombre", "Rol", "Instrumento", "Activo desde"],
    "Informe Invitaciones": ["Emitida por", "Creada", "Caduca", "Usada por", "Usada el"],
    "Informe Votos": ["Encuesta", "Ciclo", "Persona", "Respuesta", "Actualizado"],
    "Informe Actuaciones": ["ID", "Título", "Fecha", "Hora", "Lugar", "Estado"],
    "Informe Gastos": ["ID", "Fecha", "Persona", "Concepto", "Importe", "Estado", "Ticket"],
    "Informe Caja": ["Concepto", "Importe", "Actualizado"],
    "Informe Sincronización": ["Estado", "Última actualización", "Origen"],
}

_GOOGLE_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def _drive_upload_error_message(error: Any) -> str:
    """Devuelve una explicación accionable sin mostrar credenciales ni respuestas crudas."""
    status = getattr(getattr(error, "resp", None), "status", 0)
    raw_content = getattr(error, "content", b"")
    if isinstance(raw_content, bytes):
        detail = raw_content.decode("utf-8", errors="ignore").lower()
    else:
        detail = str(raw_content).lower()

    if "storagequotaexceeded" in detail or "storage quota" in detail:
        return (
            "La cuenta técnica de Google no tiene cuota propia para crear archivos "
            "en una carpeta personal de Drive."
        )
    if status == 401:
        return "La credencial técnica de Google ya no es válida."
    if status == 403:
        return "La cuenta técnica de Google no tiene permiso para guardar en esa carpeta de Drive."
    if status == 404:
        return "No se encuentra la carpeta de justificantes configurada."
    return "Drive no ha aceptado el justificante."


def _as_plain_dict(value: Any) -> dict[str, Any]:
    """Convierte los objetos de Secrets de Streamlit sin tocar las claves."""
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return dict(value)


def is_enabled(secrets: Any) -> bool:
    try:
        value = secrets.get("enable_google_sheets_sync", False)
    except (AttributeError, TypeError):
        return False
    return value is True or str(value).strip().lower() in {"true", "1", "si", "sí"}


@dataclass(frozen=True)
class GoogleStorageConfig:
    spreadsheet_id: str
    receipts_folder_id: str
    service_account: dict[str, Any]

    @classmethod
    def from_secrets(cls, secrets: Any) -> "GoogleStorageConfig":
        try:
            storage = _as_plain_dict(secrets["safara_google_storage"])
            raw_json = secrets.get("gcp_service_account_json", "")
            service_account = (
                json.loads(str(raw_json))
                if str(raw_json).strip()
                else _as_plain_dict(secrets["gcp_service_account"])
            )
        except (KeyError, TypeError, ValueError) as error:
            raise StorageConfigurationError(
                "Falta la configuración segura de Google en Streamlit Secrets."
            ) from error

        spreadsheet_id = str(storage.get("spreadsheet_id", "")).strip()
        receipts_folder_id = str(storage.get("receipts_folder_id", "")).strip()
        required_account_keys = {"type", "project_id", "private_key", "client_email", "token_uri"}
        if (
            not _GOOGLE_ID.fullmatch(spreadsheet_id)
            or not _GOOGLE_ID.fullmatch(receipts_folder_id)
            or not required_account_keys.issubset(service_account)
        ):
            raise StorageConfigurationError(
                "La configuración de Google está incompleta o contiene un identificador no válido."
            )
        if service_account.get("type") != "service_account":
            raise StorageConfigurationError("La credencial de Google no es una cuenta de servicio.")
        return cls(spreadsheet_id, receipts_folder_id, service_account)


class GoogleSafaraStorage:
    """Adaptador pequeño y deliberadamente explícito para los datos de SAFARA."""

    def __init__(
        self,
        config: GoogleStorageConfig,
        drive_credentials: Any | None = None,
        receipts_folder_id: str | None = None,
    ):
        try:
            from google.oauth2.service_account import Credentials
        except ImportError as error:
            raise StorageConfigurationError(
                "Faltan dependencias de Google en requirements.txt."
            ) from error

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        try:
            self._service_credentials = Credentials.from_service_account_info(
                config.service_account, scopes=scopes
            )
            self._spreadsheet_id = config.spreadsheet_id
            self._drive_credentials = drive_credentials or self._service_credentials
            self._folder_id = str(receipts_folder_id or config.receipts_folder_id).strip()
            self._spreadsheet = None
            self._drive = None
        except Exception as error:
            raise StorageConfigurationError(
                "No se puede acceder al espacio de pruebas de Google. Revisa los permisos de la cuenta técnica."
            ) from error

    def _spreadsheet_client(self):
        """Conecta Sheets solo al generar informes, nunca al subir un ticket."""
        if self._spreadsheet is not None:
            return self._spreadsheet
        try:
            import gspread
            self._spreadsheet = gspread.authorize(self._service_credentials).open_by_key(
                self._spreadsheet_id
            )
            return self._spreadsheet
        except Exception as error:
            raise StorageConfigurationError(
                "No se puede acceder al informe de Google Sheets. Los datos seguros siguen disponibles."
            ) from error

    def _drive_client(self):
        """Conecta Drive bajo demanda para no bloquear gastos por un fallo de Sheets."""
        if self._drive is not None:
            return self._drive
        try:
            from googleapiclient.discovery import build
            self._drive = build(
                "drive", "v3", credentials=self._drive_credentials, cache_discovery=False
            )
            return self._drive
        except Exception as error:
            raise StorageOperationError(
                "No se ha podido preparar la conexión segura con Google Drive."
            ) from error

    def crear_carpeta_justificantes_propietaria(self) -> str:
        """Crea una carpeta propia de la aplicación con la autorización del dueño."""
        try:
            folder = self._drive_client().files().create(
                body={
                    "name": "SAFARA GASTOS — Justificantes",
                    "mimeType": "application/vnd.google-apps.folder",
                    "appProperties": {"safara_tipo": "justificantes"},
                },
                fields="id",
                supportsAllDrives=True,
            ).execute()
            folder_id = str(folder.get("id", "")).strip()
            if not folder_id:
                raise StorageOperationError("Google Drive no confirmó la carpeta de justificantes.")
            self._folder_id = folder_id
            return folder_id
        except StorageOperationError:
            raise
        except Exception as error:
            raise StorageOperationError(
                "Google Drive no pudo preparar la carpeta privada de justificantes."
            ) from error

    def ensure_schema(self) -> None:
        """Establece cabeceras solo en pestañas todavía vacías; nunca migra datos."""
        spreadsheet = self._spreadsheet_client()
        for sheet_name, headers in SHEET_SCHEMA.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                values = worksheet.get_all_values()
                if not values or (len(values) == 1 and values[0] != headers):
                    worksheet.clear()
                    worksheet.update("A1", [headers], value_input_option="RAW")
                elif values[0] != headers:
                    raise StorageConfigurationError(
                        f"La pestaña {sheet_name} contiene una estructura inesperada."
                    )
            except StorageConfigurationError:
                raise
            except Exception as error:
                raise StorageConfigurationError(
                    f"No se ha podido preparar la pestaña {sheet_name}."
                ) from error

    def read_records(self, sheet_name: str) -> list[dict[str, str]]:
        headers = SHEET_SCHEMA[sheet_name]
        try:
            worksheet = self._spreadsheet_client().worksheet(sheet_name)
            values = worksheet.get_all_values()
        except Exception as error:
            raise StorageOperationError("No se ha podido leer la información guardada.") from error
        if not values:
            return []
        if values[0] != headers:
            raise StorageConfigurationError(f"La pestaña {sheet_name} no tiene la cabecera esperada.")
        records: list[dict[str, str]] = []
        for row in values[1:]:
            padded = (row + [""] * len(headers))[: len(headers)]
            if any(padded):
                records.append(dict(zip(headers, padded)))
        return records

    def replace_records(self, sheet_name: str, records: Iterable[dict[str, Any]]) -> None:
        """Sustituye una tabla completa tras haber validado todo en memoria.

        Este método está reservado a las tablas pequeñas de la fase de pruebas.
        Si la escritura remota falla, la app conserva el estado anterior en sesión.
        """
        headers = SHEET_SCHEMA[sheet_name]
        rows = [headers]
        for record in records:
            rows.append([self._cell_value(record.get(header, "")) for header in headers])
        try:
            worksheet = self._spreadsheet_client().worksheet(sheet_name)
            worksheet.clear()
            worksheet.update("A1", rows, value_input_option="RAW")
        except Exception as error:
            raise StorageOperationError("No se han podido guardar los cambios en Google.") from error

    def append_audit(self, event: str, user: str = "", detail: str = "", when: str = "") -> None:
        try:
            self._spreadsheet_client().worksheet("Auditoria").append_row(
                [when, event, user, detail.replace("\n", " ")], value_input_option="RAW"
            )
        except Exception:
            # La auditoría no puede impedir una acción ya confirmada, pero nunca incluye secretos.
            return

    def upload_receipt(self, filename: str, content: bytes, mime_type: str) -> tuple[str, str]:
        """Sube un justificante validado y devuelve id y enlace de Drive."""
        try:
            from google.auth.exceptions import RefreshError
            from googleapiclient.http import MediaIoBaseUpload
            from googleapiclient.errors import HttpError

            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
            if not self._folder_id:
                raise StorageOperationError("No está preparada la carpeta segura de justificantes.")
            file_data = self._drive_client().files().create(
                body={"name": filename, "parents": [self._folder_id]},
                media_body=media,
                fields="id,webViewLink",
                supportsAllDrives=True,
            ).execute()
            return str(file_data["id"]), str(file_data.get("webViewLink", ""))
        except HttpError as error:
            raise StorageOperationError(_drive_upload_error_message(error)) from error
        except RefreshError as error:
            raise StorageOperationError(
                "La credencial técnica de Google no se puede validar."
            ) from error
        except Exception as error:
            raise StorageOperationError(
                "No se ha podido guardar el justificante en Drive. "
                "La administración debe revisar la conexión técnica de Google."
            ) from error

    def delete_uploaded_file(self, file_id: str) -> None:
        """Elimina un ticket recién subido cuando falla el registro económico asociado."""
        if not file_id:
            return
        try:
            self._drive_client().files().delete(fileId=file_id).execute()
        except Exception:
            # No ocultamos el fallo económico original. La copia queda identificable
            # en Drive para que administración pueda revisarla si fuese necesario.
            return

    def write_report_snapshot(self, reports: dict[str, Iterable[dict[str, Any]]]) -> None:
        """Actualiza las vistas de consulta sin exponer datos sensibles.

        ``Gastos`` se conserva como una vista compatible para la administración:
        no es una fuente de datos ni contiene credenciales, pero permite revisar
        los gastos en la pestaña que ya conocen las personas usuarias. La fuente
        de verdad sigue siendo Supabase y los informes reducidos continúan en
        las pestañas ``Informe ...``.
        """
        try:
            spreadsheet = self._spreadsheet_client()
            for sheet_name, headers in REPORT_SCHEMA.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                except Exception:
                    worksheet = spreadsheet.add_worksheet(
                        title=sheet_name, rows=100, cols=max(8, len(headers))
                    )
                rows = [headers]
                for record in reports.get(sheet_name, []):
                    rows.append([self._cell_value(record.get(header, "")) for header in headers])
                worksheet.clear()
                worksheet.update("A1", rows, value_input_option="RAW")

            # La hoja original de Gastos es una consulta administrativa, no una
            # segunda base de datos. Se reconstruye siempre desde el informe de
            # Supabase para evitar filas duplicadas o datos desactualizados.
            expense_headers = SHEET_SCHEMA["Gastos"]
            try:
                expense_sheet = spreadsheet.worksheet("Gastos")
            except Exception:
                expense_sheet = spreadsheet.add_worksheet(
                    title="Gastos", rows=100, cols=len(expense_headers)
                )
            expense_rows = [expense_headers]
            for expense in reports.get("Informe Gastos", []):
                expense_rows.append([
                    self._cell_value(expense.get("ID", "")),
                    self._cell_value(expense.get("Fecha", "")),
                    self._cell_value(expense.get("Persona", "")),
                    self._cell_value(expense.get("Concepto", "")),
                    self._cell_value(expense.get("Importe", "")),
                    "",  # El nombre del archivo no es necesario para la consulta.
                    self._cell_value(expense.get("Estado", "")),
                    self._cell_value(expense.get("Ticket", "")),
                    "",  # El identificador interno de Drive no se expone en Sheets.
                    "",  # El tipo MIME tampoco es necesario para la consulta.
                ])
            expense_sheet.clear()
            expense_sheet.update("A1", expense_rows, value_input_option="RAW")
        except Exception as error:
            raise StorageOperationError("No se ha podido actualizar el informe de Google Sheets.") from error

    def upload_backup(self, filename: str, content: bytes) -> str:
        """Guarda una copia técnica sin duplicarla si se repite el mismo día."""
        try:
            from googleapiclient.http import MediaIoBaseUpload

            query = (
                "name = 'SAFARA_GASTOS_COPIAS' and "
                "mimeType = 'application/vnd.google-apps.folder' and "
                f"'{self._folder_id}' in parents and trashed = false"
            )
            drive = self._drive_client()
            found = drive.files().list(
                q=query, fields="files(id)", supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute().get("files", [])
            if found:
                backup_folder_id = found[0]["id"]
            else:
                folder = drive.files().create(
                    body={
                        "name": "SAFARA_GASTOS_COPIAS",
                        "mimeType": "application/vnd.google-apps.folder",
                        "parents": [self._folder_id],
                    },
                    fields="id",
                    supportsAllDrives=True,
                ).execute()
                backup_folder_id = folder["id"]
            existing = drive.files().list(
                q=(f"name = '{filename}' and '{backup_folder_id}' in parents "
                   "and trashed = false"),
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute().get("files", [])
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/zip", resumable=False)
            if existing:
                updated = drive.files().update(
                    fileId=existing[0]["id"], media_body=media, fields="id",
                    supportsAllDrives=True,
                ).execute()
                return str(updated["id"])
            created = drive.files().create(
                body={"name": filename, "parents": [backup_folder_id]},
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            ).execute()
            return str(created["id"])
        except Exception as error:
            raise StorageOperationError("No se ha podido guardar la copia de seguridad en Drive.") from error

    @staticmethod
    def _cell_value(value: Any) -> str | int | float:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        return value if isinstance(value, (str, int, float)) else str(value)
