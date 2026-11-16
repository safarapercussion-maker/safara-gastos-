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

_GOOGLE_ID = re.compile(r"^[A-Za-z0-9_-]{20,}$")


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

    def __init__(self, config: GoogleStorageConfig):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
        except ImportError as error:
            raise StorageConfigurationError(
                "Faltan dependencias de Google en requirements.txt."
            ) from error

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            # El alcance permite subir en la carpeta compartida; el acceso real
            # sigue limitado a los elementos que se han compartido con la cuenta.
            "https://www.googleapis.com/auth/drive",
        ]
        try:
            credentials = Credentials.from_service_account_info(
                config.service_account, scopes=scopes
            )
            self._spreadsheet = gspread.authorize(credentials).open_by_key(
                config.spreadsheet_id
            )
            self._drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
            self._folder_id = config.receipts_folder_id
        except Exception as error:
            raise StorageConfigurationError(
                "No se puede acceder al espacio de pruebas de Google. Revisa los permisos de la cuenta técnica."
            ) from error

    def ensure_schema(self) -> None:
        """Establece cabeceras solo en pestañas todavía vacías; nunca migra datos."""
        for sheet_name, headers in SHEET_SCHEMA.items():
            try:
                worksheet = self._spreadsheet.worksheet(sheet_name)
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
            worksheet = self._spreadsheet.worksheet(sheet_name)
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
            worksheet = self._spreadsheet.worksheet(sheet_name)
            worksheet.clear()
            worksheet.update("A1", rows, value_input_option="RAW")
        except Exception as error:
            raise StorageOperationError("No se han podido guardar los cambios en Google.") from error

    def append_audit(self, event: str, user: str = "", detail: str = "", when: str = "") -> None:
        try:
            self._spreadsheet.worksheet("Auditoria").append_row(
                [when, event, user, detail.replace("\n", " ")], value_input_option="RAW"
            )
        except Exception:
            # La auditoría no puede impedir una acción ya confirmada, pero nunca incluye secretos.
            return

    def upload_receipt(self, filename: str, content: bytes, mime_type: str) -> tuple[str, str]:
        """Sube un justificante validado y devuelve id y enlace de Drive."""
        try:
            from googleapiclient.http import MediaIoBaseUpload

            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
            file_data = self._drive.files().create(
                body={"name": filename, "parents": [self._folder_id]},
                media_body=media,
                fields="id,webViewLink",
            ).execute()
            return str(file_data["id"]), str(file_data.get("webViewLink", ""))
        except Exception as error:
            raise StorageOperationError("No se ha podido guardar el justificante en Drive.") from error

    @staticmethod
    def _cell_value(value: Any) -> str | int | float:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        return value if isinstance(value, (str, int, float)) else str(value)
