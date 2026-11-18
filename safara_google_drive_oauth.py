"""Autorización de Drive en nombre de la cuenta propietaria de SAFARA.

El permiso renovable se cifra antes de guardarse en Supabase. La clave de
cifrado solo existe en Streamlit Secrets y nunca se añade al repositorio.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any


class GoogleDriveOAuthConfigurationError(RuntimeError):
    """Falta o no es válida la configuración privada de OAuth."""


class GoogleDriveOAuthOperationError(RuntimeError):
    """No se pudo completar la autorización de Drive."""


_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
_TOKEN_URI = "https://oauth2.googleapis.com/token"
_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


@dataclass(frozen=True)
class GoogleDriveOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    encryption_key: str

    @classmethod
    def from_secrets(cls, secrets_source: Any) -> "GoogleDriveOAuthConfig":
        try:
            section = secrets_source["safara_google_drive_oauth"]
            raw = section.to_dict() if hasattr(section, "to_dict") else dict(section)
            config = cls(
                client_id=str(raw.get("client_id", "")).strip(),
                client_secret=str(raw.get("client_secret", "")).strip(),
                redirect_uri=str(raw.get("redirect_uri", "")).strip(),
                encryption_key=str(raw.get("encryption_key", "")).strip(),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise GoogleDriveOAuthConfigurationError(
                "Falta la autorización privada de Google Drive en Streamlit Secrets."
            ) from error
        if not config.client_id or not config.client_secret or not config.redirect_uri.startswith("https://"):
            raise GoogleDriveOAuthConfigurationError(
                "La autorización privada de Google Drive está incompleta."
            )
        try:
            from cryptography.fernet import Fernet

            Fernet(config.encryption_key.encode("ascii"))
        except Exception as error:
            raise GoogleDriveOAuthConfigurationError(
                "La clave privada de cifrado de Google Drive no es válida."
            ) from error
        return config

    def client_config(self) -> dict[str, dict[str, Any]]:
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": _AUTH_URI,
                "token_uri": _TOKEN_URI,
                "redirect_uris": [self.redirect_uri],
            }
        }


def is_configured(secrets_source: Any) -> bool:
    try:
        GoogleDriveOAuthConfig.from_secrets(secrets_source)
        return True
    except GoogleDriveOAuthConfigurationError:
        return False


def _state_signing_key(config: GoogleDriveOAuthConfig) -> bytes:
    return base64.urlsafe_b64decode(config.encryption_key.encode("ascii"))


def create_state(config: GoogleDriveOAuthConfig) -> str:
    """Crea un estado firmado y breve; no depende de la sesión del navegador."""
    payload = f"{int(time.time())}.{secrets.token_urlsafe(24)}"
    signature = hmac.new(
        _state_signing_key(config), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def verify_state(config: GoogleDriveOAuthConfig, state: str, maximum_age_seconds: int = 900) -> bool:
    try:
        issued_at, nonce, signature = state.split(".", 2)
        payload = f"{issued_at}.{nonce}"
        expected = hmac.new(
            _state_signing_key(config), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return (
            hmac.compare_digest(signature, expected)
            and 0 <= time.time() - int(issued_at) <= maximum_age_seconds
        )
    except (TypeError, ValueError):
        return False


def authorization_url(config: GoogleDriveOAuthConfig) -> str:
    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            config.client_config(), scopes=[_DRIVE_SCOPE], redirect_uri=config.redirect_uri
        )
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=create_state(config),
        )
        return str(url)
    except Exception as error:
        raise GoogleDriveOAuthOperationError(
            "No se ha podido iniciar la autorización de Google Drive."
        ) from error


def exchange_code_for_encrypted_token(config: GoogleDriveOAuthConfig, code: str, state: str) -> str:
    """Canjea el código de un solo uso y cifra solo su permiso renovable."""
    if not verify_state(config, state):
        raise GoogleDriveOAuthOperationError(
            "La autorización de Google Drive ha caducado. Iníciala de nuevo desde Administración."
        )
    try:
        from cryptography.fernet import Fernet
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            config.client_config(), scopes=[_DRIVE_SCOPE], redirect_uri=config.redirect_uri
        )
        flow.fetch_token(code=code)
        refresh_token = str(flow.credentials.refresh_token or "").strip()
        if not refresh_token:
            raise GoogleDriveOAuthOperationError(
                "Google no entregó un permiso renovable. Revoca el acceso de pruebas y vuelve a autorizarlo."
            )
        return Fernet(config.encryption_key.encode("ascii")).encrypt(
            refresh_token.encode("utf-8")
        ).decode("ascii")
    except GoogleDriveOAuthOperationError:
        raise
    except Exception as error:
        raise GoogleDriveOAuthOperationError(
            "Google no ha completado la autorización de Drive."
        ) from error


def credentials_from_encrypted_token(config: GoogleDriveOAuthConfig, encrypted_token: str):
    """Reconstruye credenciales renovables sin exponer nunca el permiso."""
    try:
        from cryptography.fernet import Fernet, InvalidToken
        from google.oauth2.credentials import Credentials

        refresh_token = Fernet(config.encryption_key.encode("ascii")).decrypt(
            encrypted_token.encode("ascii")
        ).decode("utf-8")
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=_TOKEN_URI,
            client_id=config.client_id,
            client_secret=config.client_secret,
            scopes=[_DRIVE_SCOPE],
        )
    except (InvalidToken, UnicodeDecodeError, ValueError) as error:
        raise GoogleDriveOAuthOperationError(
            "El permiso guardado de Google Drive no se puede descifrar. Autorízalo de nuevo."
        ) from error
    except Exception as error:
        raise GoogleDriveOAuthOperationError(
            "No se ha podido preparar la autorización segura de Google Drive."
        ) from error
