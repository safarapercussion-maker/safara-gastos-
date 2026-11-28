"""Primitivas locales de autenticación para la aplicación de pruebas.

No contiene usuarios, contraseñas ni secretos. Los secretos de despliegue
se configuran exclusivamente en Streamlit Secrets.
"""

import base64
import hashlib
import hmac
import re
import secrets
import unicodedata


PBKDF2_ITERATIONS = 390_000
MIN_PASSWORD_LENGTH = 12
MAX_RECEIPT_BYTES = 10 * 1024 * 1024

_RECEIPT_SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "pdf": b"%PDF-",
}


def normalize_display_name(value):
  """Normaliza un nombre visible sin convertirlo en una identidad distinta."""
  return " ".join(unicodedata.normalize("NFC", str(value or "")).split())


def normalized_name_key(value):
  return normalize_display_name(value).casefold()


def validate_display_name(value):
  name = normalize_display_name(value)
  if len(name) < 3 or len(name) > 80:
    return "El nombre debe tener entre 3 y 80 caracteres."
  if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+", name):
    return "El nombre solo puede incluir letras, espacios, apóstrofes y guiones."
  return None


def validate_password(password):
  password = str(password or "")
  if len(password) < MIN_PASSWORD_LENGTH:
    return f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
  if not re.search(r"[a-záéíóúüñ]", password, re.IGNORECASE):
    return "La contraseña debe incluir al menos una letra."
  if not re.search(r"\d", password):
    return "La contraseña debe incluir al menos un número."
  return None


def validate_email(value):
  email = str(value or "").strip()
  if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
    return None
  return email


def validate_phone(value):
  phone = re.sub(r"[\s().-]", "", str(value or ""))
  if phone.startswith("00"):
    phone = "+" + phone[2:]
  if phone and phone[0] != "+":
    phone = "+34" + phone
  if phone.startswith("+34") and not re.fullmatch(r"\+34[0-9]{9}", phone):
    return None
  if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
    return None
  return phone


def hash_password(password):
  """Devuelve sal y hash PBKDF2 codificados para guardar en Excel."""
  salt = secrets.token_bytes(16)
  digest = hashlib.pbkdf2_hmac(
      "sha256", str(password).encode("utf-8"), salt, PBKDF2_ITERATIONS
  )
  return (
      base64.b64encode(salt).decode("ascii"),
      base64.b64encode(digest).decode("ascii"),
  )


def verify_password(password, password_salt, password_hash):
  """Comprueba una contraseña sin conservarla ni compararla en texto plano."""
  try:
    salt = base64.b64decode(str(password_salt).encode("ascii"), validate=True)
    expected = base64.b64decode(
        str(password_hash).encode("ascii"), validate=True
    )
  except (ValueError, TypeError):
    return False
  actual = hashlib.pbkdf2_hmac(
      "sha256", str(password).encode("utf-8"), salt, PBKDF2_ITERATIONS
  )
  return hmac.compare_digest(actual, expected)


def verify_bootstrap_token(provided, configured):
  """Verifica el secreto inicial sin exponerlo ni aceptarlo por defecto."""
  configured = str(configured or "")
  provided = str(provided or "")
  return len(configured) >= 32 and hmac.compare_digest(
      provided.encode("utf-8"), configured.encode("utf-8")
  )


def generate_invitation_code():
  """Genera un código de alta de alta entropía para un único uso."""
  return secrets.token_urlsafe(18)


def hash_invitation_code(code):
  return hashlib.sha256(str(code or "").strip().encode("utf-8")).hexdigest()


def verify_invitation_code(code, expected_hash):
  provided_hash = hash_invitation_code(code)
  return hmac.compare_digest(provided_hash, str(expected_hash or ""))


def validate_receipt_upload(filename, size_bytes, content):
  """Valida tamaño, extensión y firma de un justificante antes de guardarlo."""
  if not filename or not isinstance(filename, str):
    return None, "El justificante no tiene un nombre de archivo válido."
  extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
  if extension not in _RECEIPT_SIGNATURES:
    return None, "Solo se permiten archivos PNG, JPG, JPEG o PDF."
  if not isinstance(size_bytes, int) or size_bytes <= 0:
    return None, "El justificante está vacío o no se ha podido leer."
  if size_bytes > MAX_RECEIPT_BYTES:
    return None, "El justificante supera el límite de 10 MB."
  if not isinstance(content, (bytes, bytearray)) or not content.startswith(
      _RECEIPT_SIGNATURES[extension]
  ):
    return None, "El contenido del justificante no coincide con su formato."
  return extension, None
