import base64
import datetime
import html
import io
import os
import random
import re
import uuid
import zipfile

try:
  from zoneinfo import ZoneInfo
except ImportError:
  from backports.zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from safara_security import (
    generate_invitation_code,
    hash_invitation_code,
    hash_password,
    normalize_display_name,
    normalized_name_key,
    validate_display_name,
    validate_email,
    validate_password,
    validate_phone,
    validate_receipt_upload,
    verify_bootstrap_token,
    verify_invitation_code,
    verify_password,
)
from safara_google_storage import (
    GoogleSafaraStorage,
    StorageConfigurationError,
    StorageOperationError,
    is_enabled as google_storage_enabled,
    GoogleStorageConfig,
)
from safara_google_drive_oauth import (
    GoogleDriveOAuthConfig,
    GoogleDriveOAuthConfigurationError,
    GoogleDriveOAuthOperationError,
    authorization_url as google_drive_authorization_url,
    credentials_from_encrypted_token,
    exchange_code_for_encrypted_token,
    returning_user_from_state,
)
from safara_supabase_storage import (
    SupabaseSafaraStorage,
    SupabaseStorageAuthenticationError,
    SupabaseStorageConfig,
    SupabaseStorageConfigurationError,
    SupabaseStorageOperationError,
    is_enabled as supabase_storage_enabled,
)
from safara_maintenance import run_google_maintenance
from safara_ensayos import (
    QUORUM_ENSAYO_MINIMO,
    ciclos_que_deben_cerrarse,
    informacion_ensayo,
)

st.set_page_config(
    page_title="Safara Percussion - App Oficial",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- FRASES DE CHAPAS SAFARA PARA LA CABECERA ---
FRASES_SAFARA = [
    "Safara • Yo toco pero bailo",
    "Safara • Chupinazo y luego terapia",
    "Safara • La última y pa casa",
    "Safara • Tocamos y luego hablamos",
    "Safara • Pues güeno depende... si no Gomito",
    "Safara • Me vine arriba y aquí estoy",
    "Safara • On Fire",
]

# --- FRASES FELICITACIÓN CUMPLEAÑOS ---
FRASES_CUMPLE = [
    "Hoy el surdo retumba por ti. Feliz cumpleaños.",
    "Un año más en el DNI pero sigues dándole duro al palo. Felicidades.",
    "Hoy no hay excusa: te toca pagar las cervezas post-ensayo. Feliz cumple.",
    "Que el ritmo no pare. Disfruta de tu día con toda la energía de Safara.",
    "Cumpleaños On Fire. A celebrarlo como se merece.",
]

# --- UBICACIONES HABITUALES DE ENSAYO ---
UBICACIONES_ENSAYO = {
    "Baragazte (Barañain)": "https://maps.app.goo.gl/U1M1adwLtcDgEqKE9?g_st=ic",
    "Gaztetxe de Zizur": "https://maps.app.goo.gl/jf44LrvY41HtXxhZA?g_st=ic",
}

QUORUM_BOLO_MINIMO = 8  # Quórum automático para confirmar un bolo


# --- FUNCIONES DE APOYO Y CICLO SEMANAL ---
def obtener_ciclo_semanal_actual():
  tz_madrid = ZoneInfo("Europe/Madrid")
  ahora_madrid = datetime.datetime.now(tz_madrid)
  anio, semana, _ = ahora_madrid.isocalendar()
  return f"{anio}-W{semana:02d}"


def obtener_fecha_espanol():
  tz_madrid = ZoneInfo("Europe/Madrid")
  hoy = datetime.datetime.now(tz_madrid).date()
  dias = [
      "Lunes",
      "Martes",
      "Miércoles",
      "Jueves",
      "Viernes",
      "Sábado",
      "Domingo",
  ]
  meses = [
      "enero",
      "febrero",
      "marzo",
      "abril",
      "mayo",
      "junio",
      "julio",
      "agosto",
      "septiembre",
      "octubre",
      "noviembre",
      "diciembre",
  ]
  return f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]}"


def formato_espanol(valor):
  try:
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
  except:
    return "0,00"


def escapar_html(valor):
  """Evita que texto introducido por usuarios se interprete como HTML."""
  return html.escape(str(valor or ""), quote=True)


def render_logo_png(filename, width=210):
  encoded, mime = cargar_recurso_visual(filename)
  if encoded:
    try:
      return f"""
                <div class="sparta-logo-container">
                    <div class="sparta-circle-logo">
                        <img src="data:{mime};base64,{encoded}" width="{width}" />
                    </div>
                </div>
            """
    except Exception:
      return None
  return None


def render_logo_inline_b64(filename):
  encoded, mime = cargar_recurso_visual(filename)
  return f"data:{mime};base64,{encoded}" if encoded else None


@st.cache_data(show_spinner=False)
def cargar_recurso_visual(filename):
  """Memoriza imágenes estáticas para que cada interacción no las vuelva a leer."""
  if not filename or not os.path.exists(filename):
    return "", ""
  try:
    with open(filename, "rb") as f:
      encoded = base64.b64encode(f.read()).decode()
    ext = filename.rsplit(".", 1)[-1].lower()
    return encoded, "image/png" if ext == "png" else "image/jpeg"
  except OSError:
    return "", ""


def buscar_logo_fuego():
  for f in os.listdir("."):
    f_lower = f.lower()
    if "detra" in f_lower and f_lower.endswith((".png", ".jpg", ".jpeg")):
      return f
  return "Logo detrás PNG.png"


def buscar_logo_delante():
  for f in os.listdir("."):
    f_lower = f.lower()
    if "delant" in f_lower and f_lower.endswith((".png", ".jpg", ".jpeg")):
      return f
  return "Logo delante PNG.png"


# --- ESTILOS CSS INTACTOS ---
logo_fuego_file = buscar_logo_fuego()
logo_delante_file = buscar_logo_delante()
logo_b64_inline = render_logo_inline_b64(logo_fuego_file) or ""

bg_b64, _ = cargar_recurso_visual("IMG_0753.jpeg")

bg_css_login = (
    f"background: linear-gradient(rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.88)),"
    f" url('data:image/jpeg;base64,{bg_b64}'); background-size: cover;"
    " background-position: center; background-attachment: fixed;"
    if bg_b64
    else "background-color: #050505;"
)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=Cinzel:wght@700&display=swap');

    * {{
        font-family: 'Montserrat', sans-serif !important;
    }}

    .stApp {{
        {bg_css_login}
        color: #FFFFFF !important;
    }}

    [data-testid="stStatusWidget"], header {{
        visibility: hidden !important;
        display: none !important;
    }}

    .sparta-logo-container {{
        text-align: center;
        margin-top: 0.6rem;
        margin-bottom: 0.4rem;
    }}
    .sparta-circle-logo {{
        width: 210px;
        height: 210px;
        border-radius: 50%;
        border: 2.5px solid rgba(231, 76, 60, 0.9);
        box-shadow: 0 0 35px rgba(231, 76, 60, 0.65);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: transparent !important;
        padding: 12px;
        overflow: hidden;
        margin: 0 auto;
    }}
    .sparta-circle-logo img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        filter: drop-shadow(0px 0px 12px rgba(231, 76, 60, 0.85));
    }}

    .frase-chapa-badge {{
        text-align: center;
        font-size: 13px;
        color: #E74C3C;
        font-weight: 700;
        font-style: italic;
        margin-bottom: 18px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    @keyframes flame-effect {{
        0% {{ background-position: 0% 50%; filter: drop-shadow(0 0 8px rgba(255, 69, 0, 0.8)); }}
        50% {{ background-position: 100% 50%; filter: drop-shadow(0 0 16px rgba(255, 140, 0, 0.9)); }}
        100% {{ background-position: 0% 50%; filter: drop-shadow(0 0 8px rgba(255, 69, 0, 0.8)); }}
    }}

    .somos-fuego-footer {{
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 4px;
        text-transform: uppercase;
        background: linear-gradient(270deg, #ff2a00, #ff7700, #ffaa00, #ff2a00);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: flame-effect 4s ease infinite;
        margin: 25px 0 15px 0;
    }}

    .glass-card {{
        background: rgba(12, 12, 12, 0.82);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(231, 76, 60, 0.25);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7);
    }}

    div[data-testid="stSelectbox"] > label,
    div[data-testid="stTextInput"] > label {{
        padding-top: 0 !important;
        margin-bottom: 2px !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
    }}

    input, textarea {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
        font-weight: 600 !important;
    }}

    div[data-baseweb="input"] button {{
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 32px !important;
        height: 32px !important;
    }}
    div[data-baseweb="input"] button svg {{
        fill: #E74C3C !important;
        width: 18px !important;
        height: 18px !important;
    }}

    .stButton>button, div[data-testid="stFormSubmitButton"]>button {{
        background: linear-gradient(135deg, #B01E10 0%, #7A0000 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        border-radius: 6px !important;
        border: 1px solid rgba(231, 76, 60, 0.4) !important;
        width: 100% !important;
        margin: 6px auto !important;
        padding: 8px 12px !important;
        box-shadow: 0 2px 8px rgba(176, 30, 16, 0.3) !important;
    }}

    .btn-logout-discreto button {{
        background: rgba(18, 18, 18, 0.8) !important;
        color: #E74C3C !important;
        border: 1px solid rgba(231, 76, 60, 0.4) !important;
        border-radius: 10px !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        padding: 5px 10px !important;
        width: auto !important;
        box-shadow: none !important;
    }}

    /* --- ESTILOS EXACTOS DE LAS ENCUESTAS EN HORIZONTAL --- */
    .safara-poll-row {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        justify-content: space-evenly !important;
        align-items: flex-start !important;
        width: 100% !important;
        margin: 15px 0 !important;
        box-sizing: border-box !important;
    }}
    .safara-poll-col {{
        flex: 0 0 48% !important;
        max-width: 48% !important;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
    }}
    .poll-img-btn {{
        width: 85px !important;
        height: 85px !important;
        object-fit: contain !important;
        cursor: pointer !important;
        display: block !important;
        margin: 0 auto !important;
        transition: transform 0.2s ease, filter 0.2s ease !important;
    }}
    .poll-img-green-norm {{
        filter: grayscale(1) sepia(1) saturate(5) hue-rotate(80deg) brightness(0.95) drop-shadow(0 0 6px #39ff14) !important;
        opacity: 0.8 !important;
    }}
    .poll-img-green-sel {{
        filter: grayscale(1) sepia(1) saturate(8) hue-rotate(80deg) brightness(1.25) drop-shadow(0 0 10px #39ff14) drop-shadow(0 0 22px #39ff14) !important;
        transform: scale(1.12) !important;
        opacity: 1 !important;
    }}
    .poll-img-red-norm {{
        filter: grayscale(1) sepia(1) saturate(8) hue-rotate(320deg) brightness(0.95) drop-shadow(0 0 6px #ff1744) !important;
        opacity: 0.8 !important;
    }}
    .poll-img-red-sel {{
        filter: grayscale(1) sepia(1) saturate(10) hue-rotate(320deg) brightness(1.25) drop-shadow(0 0 10px #ff1744) drop-shadow(0 0 22px #ff1744) !important;
        transform: scale(1.12) !important;
        opacity: 1 !important;
    }}
    .poll-label-green {{
        color: #39ff14 !important;
        text-align: center !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        margin-top: 6px !important;
    }}
    .poll-label-red {{
        color: #ff1744 !important;
        text-align: center !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        margin-top: 6px !important;
    }}

    .ticker-container {{
        width: 100%;
        background: linear-gradient(90deg, #900C3F 0%, #C0392B 50%, #E74C3C 100%);
        color: #FFFFFF;
        overflow: hidden;
        white-space: nowrap;
        box-sizing: border-box;
        border-radius: 10px;
        padding: 8px 0;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(192, 57, 43, 0.4);
    }}
    .ticker-text {{
        display: inline-block;
        padding-left: 100%;
        animation: ticker 18s linear infinite;
        font-weight: 800;
        font-size: 13px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    @keyframes ticker {{
        0% {{ transform: translate(0, 0); }}
        100% {{ transform: translate(-100%, 0); }}
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# --- ARCHIVOS DE DATOS Y DIRECTORIOS ---
RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"
SALDO_FILE = "saldo_caja.txt"
# Fichero nuevo y deliberadamente separado del registro heredado de credenciales.
# No se migra ni se carga el fichero anterior: las pruebas empiezan sin cuentas.
EXCEL_USUARIOS = "usuarios_safara_v2.xlsx"
EXCEL_INVITACIONES = "invitaciones_safara_v2.xlsx"
VOTOS_PERSIST_FILE = "votos_safara_historial.xlsx"
CONFESIONARIO_FILE = "confesionario_safara.xlsx"
ACTUACIONES_FILE = "actuaciones_safara.xlsx"
AUDITORIA_FILE = "auditoria_safara.log"

FECHA_FUNDACION = datetime.date(2023, 4, 23)

hoy_m = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
ciclo_actual = obtener_ciclo_semanal_actual()


def sincronizacion_google_habilitada():
  """Evita conexiones externas salvo autorización explícita en Secrets."""
  try:
    value = st.secrets.get("enable_google_sheets_sync", False)
  except Exception:
    return False
  return value is True or str(value).strip().lower() in {"true", "1", "si", "sí"}


_google_storage = None
_google_storage_error = ""
_supabase_storage = None
_supabase_storage_error = ""
_SUPABASE_BACKEND_VERSION = "2026-11-19-receipts-v2"


@st.cache_resource(show_spinner=False)
def crear_almacenamiento_supabase_compartido(database_url, backend_version):
  """Reutiliza un grupo pequeño de conexiones para todas las sesiones activas."""
  del backend_version  # Fuerza una instancia nueva y compatible tras cada despliegue relevante.
  return SupabaseSafaraStorage(SupabaseStorageConfig(database_url))


def obtener_almacenamiento_google():
  """Devuelve el almacén autorizado, priorizando Supabase para datos transaccionales."""
  global _google_storage, _google_storage_error, _supabase_storage, _supabase_storage_error
  if supabase_storage_enabled(st.secrets):
    if _supabase_storage is not None:
      return _supabase_storage
    if _supabase_storage_error:
      return None
    try:
      config = SupabaseStorageConfig.from_secrets(st.secrets)
      _supabase_storage = crear_almacenamiento_supabase_compartido(
          config.database_url, _SUPABASE_BACKEND_VERSION
      )
      return _supabase_storage
    except SupabaseStorageConfigurationError as error:
      _supabase_storage_error = str(error)
      return None
  return obtener_almacenamiento_drive()


def obtener_almacenamiento_drive():
  """Devuelve Google Drive únicamente para justificantes; nunca para datos críticos."""
  global _google_storage, _google_storage_error
  if not google_storage_enabled(st.secrets):
    return None
  if _google_storage is not None:
    return _google_storage
  if _google_storage_error:
    return None
  try:
    credenciales_drive = None
    try:
      oauth_config = GoogleDriveOAuthConfig.from_secrets(st.secrets)
    except GoogleDriveOAuthConfigurationError as error:
      if "safara_google_drive_oauth" in st.secrets:
        _google_storage_error = str(error)
        return None
    else:
      if not supabase_storage_enabled(st.secrets):
        _google_storage_error = (
            "La autorización de Drive necesita la base segura de pruebas activa."
        )
        return None
      database = obtener_almacenamiento_google()
      if not usar_almacenamiento_supabase(database):
        _google_storage_error = (
            "La autorización de Drive necesita la base segura de pruebas activa."
        )
        return None
      autorizacion_drive = database.obtener_autorizacion_google_drive()
      token_cifrado = autorizacion_drive.get("token_cifrado", "")
      carpeta_id = autorizacion_drive.get("carpeta_id", "")
      if not token_cifrado:
        _google_storage_error = (
            "Google Drive aún no ha sido autorizado por una persona administradora."
        )
        return None
      if not carpeta_id:
        _google_storage_error = (
            "La autorización de Google Drive debe completarse de nuevo para preparar la carpeta segura."
        )
        return None
      credenciales_drive = credentials_from_encrypted_token(oauth_config, token_cifrado)

    _google_storage = GoogleSafaraStorage(
        GoogleStorageConfig.from_secrets(st.secrets), drive_credentials=credenciales_drive,
        receipts_folder_id=carpeta_id if credenciales_drive else None,
    )
    # Las pestañas antiguas solo pertenecen al modo legado de Google como
    # almacenamiento. Con Supabase activo, Sheets recibe exclusivamente el
    # informe reducido y seguro definido por la integración de mantenimiento.
    if not supabase_storage_enabled(st.secrets):
      _google_storage.ensure_schema()
    return _google_storage
  except (StorageConfigurationError, GoogleDriveOAuthOperationError,
          SupabaseStorageOperationError) as error:
    _google_storage_error = str(error)
    return None


def reiniciar_almacenamiento_drive():
  """Fuerza a que el siguiente uso adopte una nueva autorización ya guardada."""
  global _google_storage, _google_storage_error
  _google_storage = None
  _google_storage_error = ""


def usar_almacenamiento_google():
  """Indica que hay persistencia remota autorizada y evita archivos efímeros."""
  return supabase_storage_enabled(st.secrets) or google_storage_enabled(st.secrets)


def usar_almacenamiento_supabase(storage=None):
  candidato = storage if storage is not None else obtener_almacenamiento_google()
  # Streamlit puede conservar recursos entre despliegues. El nombre estable
  # evita que una instancia válida de la versión anterior se confunda con
  # Google por cambiar la identidad interna de la clase Python.
  return getattr(candidato.__class__, "__name__", "") == "SupabaseSafaraStorage"


def diagnostico_supabase_para_administracion():
  """Devuelve un estado seguro y concreto, sin revelar ningún secreto."""
  if not supabase_storage_enabled(st.secrets):
    return None, (
        "Supabase no está activado en los secretos de esta aplicación de pruebas. "
        "No se iniciará Google Drive ni se usarán rutas antiguas."
    )
  almacenamiento = obtener_almacenamiento_google()
  if not usar_almacenamiento_supabase(almacenamiento):
    return None, _supabase_storage_error or (
        "La conexión privada de Supabase no se ha podido preparar."
    )
  try:
    almacenamiento.verificar_conexion_segura()
  except SupabaseStorageAuthenticationError:
    return None, "La contraseña privada de Supabase no coincide con la conexión guardada."
  except SupabaseStorageOperationError:
    return None, "No se puede contactar ahora con la base segura de Supabase."
  return almacenamiento, ""


def actualizar_informes_y_copias_en_segundo_plano():
  """Actualiza Google como copia de consulta sin poner en riesgo Supabase."""
  if not supabase_storage_enabled(st.secrets):
    return False
  try:
    database = obtener_almacenamiento_google()
    if not usar_almacenamiento_supabase(database):
      return False
    google = obtener_almacenamiento_drive()
    return run_google_maintenance(database, google)
  except Exception:
    # La operación principal ya se confirmó en Supabase. Google se reintenta
    # en la siguiente acción autorizada sin mostrar un error técnico al grupo.
    return False


def reintentar_justificantes_pendientes_sin_interrumpir(database):
  """Reintenta tickets ya protegidos sin afectar a la sesión ni al gasto."""
  if not usar_almacenamiento_supabase(database):
    return 0
  try:
    pendientes = database.listar_justificantes_pendientes()
    if not pendientes:
      return 0
    drive = obtener_almacenamiento_drive()
    if not drive:
      return 0
  except (StorageOperationError, SupabaseStorageOperationError):
    return 0

  completados = 0
  for pendiente in pendientes:
    try:
      archivo = database.obtener_justificante_pendiente(int(pendiente["gasto_id"]))
      if not archivo:
        continue
      drive_file_id, enlace = drive.upload_receipt(
          str(archivo["nombre_fichero"]), bytes(archivo["contenido"]),
          str(archivo.get("mime_type") or "application/octet-stream"),
      )
      database.confirmar_justificante_drive(
          int(pendiente["gasto_id"]), drive_file_id, enlace
      )
      completados += 1
    except (StorageOperationError, SupabaseStorageOperationError) as error:
      try:
        database.marcar_justificante_pendiente(int(pendiente["gasto_id"]), str(error))
      except SupabaseStorageOperationError:
        pass
  return completados


# Los informes se actualizan al terminar acciones que cambian datos. El bloqueo
# temporal de Supabase evita que varias personas lancen la misma copia a la vez.


def reiniciar_estado_si_cambia_backend():
  """Evita reutilizar en la sesión datos de un almacenamiento anterior."""
  if supabase_storage_enabled(st.secrets):
    backend_actual = "supabase"
  elif google_storage_enabled(st.secrets):
    backend_actual = "google"
  else:
    backend_actual = "local"

  if st.session_state.get("_safara_backend_persistencia") == backend_actual:
    return

  for clave in (
      "votos_historial",
      "actuaciones",
      "confesionario_mensajes",
      "gastos",
      "saldo_caja",
      "usuarios_registrados",
      "invitaciones",
      "usuario_autenticado",
      "ultimo_acceso",
      "fallos_acceso",
      "bloqueado_hasta",
      "mostrar_recuperacion",
  ):
    st.session_state.pop(clave, None)
  st.session_state["_safara_backend_persistencia"] = backend_actual


reiniciar_estado_si_cambia_backend()


def usuario_autenticado_en_sesion():
  """Evita cargar módulos de trabajo antes de que exista una sesión válida."""
  return bool(st.session_state.get("usuario_autenticado"))


def guardar_excel_atomico(dataframe, destino):
  """Evita dejar un Excel incompleto si la escritura se interrumpe."""
  temporal = f"{destino}.tmp.xlsx"
  try:
    dataframe.to_excel(temporal, index=False)
    os.replace(temporal, destino)
    return True
  except Exception:
    try:
      if os.path.exists(temporal):
        os.remove(temporal)
    except OSError:
      pass
    return False


def guardar_texto_atomico(texto, destino):
  temporal = f"{destino}.tmp"
  try:
    with open(temporal, "w", encoding="utf-8") as archivo:
      archivo.write(str(texto))
    os.replace(temporal, destino)
    return True
  except OSError:
    try:
      if os.path.exists(temporal):
        os.remove(temporal)
    except OSError:
      pass
    return False


def registrar_auditoria(evento, usuario="", detalle=""):
  """Registra solo eventos técnicos; nunca secretos, contraseñas ni códigos."""
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    marca_tiempo = datetime.datetime.now(ZoneInfo("Europe/Madrid")).isoformat()
    storage.append_audit(str(evento), str(usuario), str(detalle), marca_tiempo)
    return
  try:
    marca_tiempo = datetime.datetime.now(ZoneInfo("Europe/Madrid")).isoformat()
    linea = " | ".join(
        [marca_tiempo, str(evento), str(usuario), str(detalle).replace("\n", " ")]
    )
    with open(AUDITORIA_FILE, "a", encoding="utf-8") as archivo:
      archivo.write(linea + "\n")
  except OSError:
    pass

# --- INICIALIZACIÓN DE VOTOS ---
# Los datos de trabajo no son necesarios para identificar a una persona. Cargarlos
# antes del acceso multiplicaba consultas y mostraba fallos de infraestructura en
# la pantalla pública. Se inicializan en el primer rerun posterior al acceso.
if "votos_historial" not in st.session_state and usuario_autenticado_en_sesion():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    try:
      st.session_state.votos_historial = pd.DataFrame(
          storage.read_records("Votos"),
          columns=["encuesta_id", "ciclo_id", "usuario_id", "respuesta", "actualizado_en"],
      )
    except (StorageOperationError, SupabaseStorageOperationError):
      st.session_state.votos_historial = pd.DataFrame(
          columns=["encuesta_id", "ciclo_id", "usuario_id", "respuesta", "actualizado_en"]
      )
  elif os.path.exists(VOTOS_PERSIST_FILE) and not usar_almacenamiento_google():
    try:
      st.session_state.votos_historial = pd.read_excel(VOTOS_PERSIST_FILE)
    except:
      st.session_state.votos_historial = pd.DataFrame(
          columns=[
              "encuesta_id",
              "ciclo_id",
              "usuario_id",
              "respuesta",
              "actualizado_en",
          ]
      )
  else:
    st.session_state.votos_historial = pd.DataFrame(
        columns=[
            "encuesta_id",
            "ciclo_id",
            "usuario_id",
            "respuesta",
            "actualizado_en",
        ]
    )


def guardar_votos_persistentes():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    if usar_almacenamiento_supabase(storage):
      return True
    try:
      storage.replace_records("Votos", st.session_state.votos_historial.to_dict(orient="records"))
      return True
    except (StorageOperationError, SupabaseStorageOperationError):
      st.error("No se han podido guardar los votos. Inténtalo de nuevo.")
      registrar_auditoria("error_guardado_votos")
      return False
  if usar_almacenamiento_google():
    st.error("La conexión segura con Google aún no está lista. No se han guardado los votos.")
    return False
  if not guardar_excel_atomico(st.session_state.votos_historial, VOTOS_PERSIST_FILE):
    st.error("No se han podido guardar los votos. Inténtalo de nuevo.")
    registrar_auditoria("error_guardado_votos")
    return False
  return True


# --- FUNCIONES DE SINCRONIZACIÓN Y GESTIÓN CON GOOGLE SHEETS (NUBE) ---
def sincronizar_bolo_en_sheets(titulo, fecha_obj, hora_str, lugar_str, estado_str):
  if usar_almacenamiento_google():
    # Las actuaciones ya se guardan completas en la pestaña de pruebas propia.
    return 1 if obtener_almacenamiento_google() else None
  try:
    if sincronizacion_google_habilitada() and "gcp_service_account" in st.secrets:
      import gspread
      from google.oauth2.service_account import Credentials

      scopes = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ]
      credentials = Credentials.from_service_account_info(
          st.secrets["gcp_service_account"], scopes=scopes
      )
      client = gspread.authorize(credentials)
      sheet = client.open_by_key(
          "16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM"
      ).worksheet("ACTUACIONES 2026")

      # Determinar la siguiente columna libre al final (basado en la Fila 3 UBICACION)
      fila3 = sheet.row_values(3)
      next_col = len(fila3) + 1
      if next_col < 3:
        next_col = 3

      f_str = (
          fecha_obj.strftime("%d/%m/%Y")
          if isinstance(fecha_obj, datetime.date)
          else str(fecha_obj)
      )

      # Escribir los datos en la nueva columna al final
      sheet.update_cell(2, next_col, estado_str)
      sheet.update_cell(3, next_col, titulo)
      sheet.update_cell(4, next_col, f_str)
      sheet.update_cell(5, next_col, hora_str if hora_str else "19:00h")

      # Inicializar las celdas de los socios (filas 6 en adelante) con '?'
      col_b = sheet.col_values(2)
      for r_idx in range(6, len(col_b) + 1):
        try:
          sheet.update_cell(r_idx, next_col, "?")
        except:
          pass

      return next_col
    return None
  except Exception as e:
    st.error(f"Error al sincronizar con Google Sheets: {e}")
    return None


def cambiar_estado_bolo_en_sheets(sheet_col, nuevo_estado):
  if usar_almacenamiento_google():
    return
  try:
    if sincronizacion_google_habilitada() and "gcp_service_account" in st.secrets and sheet_col:
      import gspread
      from google.oauth2.service_account import Credentials

      scopes = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ]
      credentials = Credentials.from_service_account_info(
          st.secrets["gcp_service_account"], scopes=scopes
      )
      client = gspread.authorize(credentials)
      sheet = client.open_by_key(
          "16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM"
      ).worksheet("ACTUACIONES 2026")

      sheet.update_cell(2, sheet_col, nuevo_estado)
  except Exception as e:
    st.error(f"Error actualizando estado en Google Sheets: {e}")


def eliminar_bolo_en_sheets(sheet_col):
  if usar_almacenamiento_google():
    return
  try:
    if sincronizacion_google_habilitada() and "gcp_service_account" in st.secrets and sheet_col:
      import gspread
      from google.oauth2.service_account import Credentials

      scopes = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ]
      credentials = Credentials.from_service_account_info(
          st.secrets["gcp_service_account"], scopes=scopes
      )
      client = gspread.authorize(credentials)
      sheet = client.open_by_key(
          "16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM"
      ).worksheet("ACTUACIONES 2026")

      for r in range(2, 50):
        try:
          sheet.update_cell(r, sheet_col, "")
        except:
          pass
  except Exception as e:
    st.error(f"Error eliminando actuación en Google Sheets: {e}")


def registrar_voto_en_sheets_cloud(encuesta_id, usuario_id, respuesta):
  if usar_almacenamiento_google():
    return
  try:
    if sincronizacion_google_habilitada() and "gcp_service_account" in st.secrets and str(encuesta_id).startswith(
        "bolo_"
    ):
      import gspread
      from google.oauth2.service_account import Credentials

      scopes = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ]
      credentials = Credentials.from_service_account_info(
          st.secrets["gcp_service_account"], scopes=scopes
      )
      client = gspread.authorize(credentials)
      sheet = client.open_by_key(
          "16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM"
      ).worksheet("ACTUACIONES 2026")

      bolo_id = int(str(encuesta_id).split("_")[1])
      target_col = None
      for a in st.session_state.get("actuaciones", []):
        if a.get("id") == bolo_id:
          target_col = a.get("sheet_col")
          break

      if not target_col:
        target_col = bolo_id + 2

      col_b_values = sheet.col_values(2)
      user_row = None
      for idx, val in enumerate(col_b_values):
        if val.strip().lower() == str(usuario_id).strip().lower():
          user_row = idx + 1
          break

      if not user_row:
        next_row = len(col_b_values) + 1
        if next_row < 6:
          next_row = 6
        sheet.update_cell(next_row, 2, str(usuario_id))
        user_row = next_row

      sheet.update_cell(user_row, target_col, str(respuesta))
  except Exception as e:
    st.error(f"Error registrando voto en Google Sheets: {e}")


def registrar_voto_backend(encuesta_id, usuario_id, respuesta):
  global ciclo_actual
  if str(encuesta_id) == "ensayo_proximo":
    ensayo = informacion_ensayo()
    if not ensayo["votacion_abierta"]:
      st.warning("La encuesta de ensayo ya está cerrada. El resultado queda guardado en el historial.")
      return False
  ahora_str = datetime.datetime.now(ZoneInfo("Europe/Madrid")).strftime(
      "%Y-%m-%d %H:%M:%S"
  )
  df = st.session_state.votos_historial
  votos_anteriores = df.copy(deep=True)

  ciclo_target = (
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_")
      else informacion_ensayo()["ciclo_id"] if str(encuesta_id) == "ensayo_proximo"
      else ciclo_actual
  )

  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if usar_almacenamiento_supabase(storage):
    try:
      storage.guardar_voto(str(encuesta_id), str(ciclo_target), str(usuario_id), str(respuesta))
    except SupabaseStorageOperationError:
      st.error("No se ha podido guardar tu respuesta. Inténtalo de nuevo.")
      return False

  cond = (
      (df["encuesta_id"] == str(encuesta_id))
      & (df["ciclo_id"] == str(ciclo_target))
      & (df["usuario_id"] == str(usuario_id))
  )

  if df[cond].empty:
    nuevo_reg = {
        "encuesta_id": str(encuesta_id),
        "ciclo_id": str(ciclo_target),
        "usuario_id": str(usuario_id),
        "respuesta": str(respuesta),
        "actualizado_en": ahora_str,
    }
    st.session_state.votos_historial = pd.concat(
        [df, pd.DataFrame([nuevo_reg])], ignore_index=True
    )
  else:
    st.session_state.votos_historial.loc[cond, "respuesta"] = str(respuesta)
    st.session_state.votos_historial.loc[cond, "actualizado_en"] = ahora_str

  if not guardar_votos_persistentes():
    st.session_state.votos_historial = votos_anteriores
    return False
  registrar_voto_en_sheets_cloud(encuesta_id, usuario_id, respuesta)
  registrar_auditoria("voto_actualizado", usuario_id, encuesta_id)
  actualizar_informes_y_copias_en_segundo_plano()
  return True


def obtener_voto_usuario(encuesta_id, usuario_id):
  global ciclo_actual
  ciclo_target = (
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_")
      else informacion_ensayo()["ciclo_id"] if str(encuesta_id) == "ensayo_proximo"
      else ciclo_actual
  )
  df = st.session_state.get(
      "votos_historial",
      pd.DataFrame(columns=["encuesta_id", "ciclo_id", "usuario_id", "respuesta", "actualizado_en"]),
  )
  if df.empty:
    return None
  res = df[
      (df["encuesta_id"] == str(encuesta_id))
      & (df["ciclo_id"] == str(ciclo_target))
      & (df["usuario_id"] == str(usuario_id))
  ]
  if not res.empty:
    return res.iloc[0]["respuesta"]
  return None


def obtener_todos_votos_encuesta(encuesta_id):
  global ciclo_actual
  ciclo_target = (
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_")
      else informacion_ensayo()["ciclo_id"] if str(encuesta_id) == "ensayo_proximo"
      else ciclo_actual
  )
  # Un retorno externo (OAuth) puede reconstruir la sesión en un rerun. Este
  # acceso defensivo garantiza que una encuesta vacía nunca derribe el panel.
  df = st.session_state.get(
      "votos_historial",
      pd.DataFrame(columns=["encuesta_id", "ciclo_id", "usuario_id", "respuesta", "actualizado_en"]),
  )
  if df.empty:
    return pd.DataFrame()
  return df[
      (df["encuesta_id"] == str(encuesta_id))
      & (df["ciclo_id"] == str(ciclo_target))
  ]


def sincronizar_historial_ensayos():
  """Cierra por reloj los ensayos vencidos y devuelve el historial disponible."""
  ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
  ciclo = informacion_ensayo(ahora)["ciclo_id"]
  cache = st.session_state.get("_historial_ensayos_cache")
  if (
      cache
      and cache.get("ciclo") == ciclo
      and ahora - cache.get("consultado_en", ahora) < datetime.timedelta(seconds=60)
  ):
    return cache.get("historial", [])
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if not usar_almacenamiento_supabase(storage):
    return []
  try:
    for cierre in ciclos_que_deben_cerrarse():
      storage.cerrar_ensayo_semanal(
          cierre["ciclo_id"],
          cierre["fecha"],
          cierre["hora_cierre"],
          cierre["ubicacion"],
          QUORUM_ENSAYO_MINIMO,
      )
    historial = storage.obtener_historial_ensayos()
    st.session_state["_historial_ensayos_cache"] = {
        "ciclo": ciclo, "consultado_en": ahora, "historial": historial,
    }
    return historial
  except SupabaseStorageOperationError:
    return []


# --- PERSISTENCIA Y CARGA DE ACTUACIONES / BOLOS (CON GOOGLE SHEETS) ---
def guardar_actuaciones_excel():
  try:
    df_act = pd.DataFrame(st.session_state.actuaciones)
    if "fecha" in df_act.columns:
      df_act["fecha"] = df_act["fecha"].apply(
          lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x)
      )
    storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
    if storage:
      if usar_almacenamiento_supabase(storage):
        return True
      storage.replace_records("Actuaciones", df_act.to_dict(orient="records"))
      return True
    if usar_almacenamiento_google():
      return False
    if not guardar_excel_atomico(df_act, ACTUACIONES_FILE):
      st.error("No se han podido guardar las actuaciones.")
      return False
    return True
  except Exception:
    st.error("No se han podido preparar las actuaciones para guardarlas.")
    return False


def cargar_actuaciones_desde_fuentes():
  acts = []
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    try:
      acts = storage.read_records("Actuaciones")
      for actuacion in acts:
        try:
          actuacion["id"] = int(actuacion.get("id", 0))
        except (TypeError, ValueError):
          actuacion["id"] = 0
        try:
          actuacion["sheet_col"] = int(actuacion.get("sheet_col", 0))
        except (TypeError, ValueError):
          actuacion["sheet_col"] = actuacion["id"] + 2
        try:
          actuacion["fecha"] = datetime.date.fromisoformat(str(actuacion.get("fecha", "")))
        except ValueError:
          actuacion["fecha"] = hoy_m
      return [actuacion for actuacion in acts if actuacion.get("id")]
    except (StorageOperationError, SupabaseStorageOperationError):
      return []
  if usar_almacenamiento_google():
    return []
  try:
    if sincronizacion_google_habilitada() and "gcp_service_account" in st.secrets:
      import gspread
      from google.oauth2.service_account import Credentials

      scopes = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive",
      ]
      credentials = Credentials.from_service_account_info(
          st.secrets["gcp_service_account"], scopes=scopes
      )
      client = gspread.authorize(credentials)
      sheet = client.open_by_key(
          "16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM"
      ).worksheet("ACTUACIONES 2026")
      data = sheet.get_all_values()
      if len(data) >= 3:
        estado_row = data[0] if len(data) > 0 else []
        headers_row = data[1] if len(data) > 1 else data[0]
        fecha_row = data[2] if len(data) > 2 else []
        hora_row = data[3] if len(data) > 3 else []

        for col_idx in range(2, len(headers_row)):
          titulo_bolo = headers_row[col_idx].strip()
          if not titulo_bolo:
            continue
          f_str = fecha_row[col_idx].strip() if col_idx < len(fecha_row) else ""
          h_str = hora_row[col_idx].strip() if col_idx < len(hora_row) else ""
          e_str = (
              estado_row[col_idx].strip().upper()
              if col_idx < len(estado_row)
              else "CONFIRMADA"
          )

          match_f = re.search(r"\d{2}/\d{2}/\d{4}", f_str)
          fecha_obj = hoy_m
          if match_f:
            try:
              fecha_obj = datetime.datetime.strptime(
                  match_f.group(0), "%d/%m/%Y"
              ).date()
            except:
              pass

          acts.append({
              "id": col_idx - 1,
              "titulo": titulo_bolo,
              "fecha": fecha_obj,
              "hora": h_str if h_str else "19:00h",
              "lugar": "Pamplona / Navarra",
              "estado": e_str if e_str else "CONFIRMADA",
              "sheet_col": col_idx + 1,
          })
  except Exception:
    pass

  if not acts:
    if os.path.exists(ACTUACIONES_FILE):
      try:
        df_act = pd.read_excel(ACTUACIONES_FILE)
        list_acts = df_act.to_dict(orient="records")
        for a in list_acts:
          if isinstance(a.get("fecha"), str):
            try:
              a["fecha"] = datetime.date.fromisoformat(a["fecha"])
            except:
              pass
          if "sheet_col" not in a:
            a["sheet_col"] = a.get("id", 1) + 2
        acts = list_acts
      except:
        acts = []
    if not acts:
      acts = [
          {
              "id": 1,
              "titulo": "Halloween Ocasiones Especiales",
              "fecha": datetime.date(2026, 10, 31),
              "hora": "19:00h",
              "lugar": "Pamplona",
              "estado": "CONFIRMADA",
              "sheet_col": 3,
          },
          {
              "id": 2,
              "titulo": "Boda Amaia (Iruña Park)",
              "fecha": datetime.date(2026, 11, 7),
              "hora": "19:00h - 20:00h",
              "lugar": "Iruña Park, Pamplona",
              "estado": "CONFIRMADA",
              "sheet_col": 4,
          },
      ]
  return acts


if "actuaciones" not in st.session_state and usuario_autenticado_en_sesion():
  st.session_state.actuaciones = cargar_actuaciones_desde_fuentes()

# --- CONFESIONARIO PERSISTENTE ---
if "confesionario_mensajes" not in st.session_state and usuario_autenticado_en_sesion():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    try:
      st.session_state.confesionario_mensajes = storage.read_records("Confesionario")
    except (StorageOperationError, SupabaseStorageOperationError):
      st.session_state.confesionario_mensajes = []
  elif os.path.exists(CONFESIONARIO_FILE) and not usar_almacenamiento_google():
    try:
      df_conf = pd.read_excel(CONFESIONARIO_FILE)
      st.session_state.confesionario_mensajes = df_conf.to_dict(
          orient="records"
      )
    except:
      st.session_state.confesionario_mensajes = []
  else:
    st.session_state.confesionario_mensajes = []


def guardar_confesionario_excel():
  try:
    df_conf = pd.DataFrame(st.session_state.confesionario_mensajes)
    storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
    if storage:
      storage.replace_records("Confesionario", df_conf.to_dict(orient="records"))
      return True
    if usar_almacenamiento_google():
      return False
    if not guardar_excel_atomico(df_conf, CONFESIONARIO_FILE):
      st.error("No se ha podido guardar el mensaje.")
      return False
    return True
  except Exception:
    st.error("No se ha podido preparar el mensaje para guardarlo.")
    return False


if "gastos" not in st.session_state and usuario_autenticado_en_sesion():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    try:
      st.session_state.gastos = pd.DataFrame(storage.read_records("Gastos"))
      if st.session_state.gastos.empty:
        st.session_state.gastos = pd.DataFrame(
            columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado", "Enlace Ticket", "Drive File ID", "MIME Type"]
        )
      else:
        st.session_state.gastos["ID"] = pd.to_numeric(st.session_state.gastos["ID"], errors="coerce").fillna(0).astype(int)
        st.session_state.gastos["Importe"] = pd.to_numeric(st.session_state.gastos["Importe"], errors="coerce").fillna(0.0)
      if "Reembolsado" not in st.session_state.gastos.columns:
        st.session_state.gastos["Reembolsado"] = "PENDIENTE ABONO"
    except (StorageOperationError, SupabaseStorageOperationError):
      st.session_state.gastos = pd.DataFrame()
  elif os.path.exists(EXCEL_FILE) and not usar_almacenamiento_google():
    try:
      st.session_state.gastos = pd.read_excel(EXCEL_FILE)
      if "Reembolsado" not in st.session_state.gastos.columns:
        st.session_state.gastos["Reembolsado"] = "PENDIENTE ABONO"
    except:
      st.session_state.gastos = pd.DataFrame(
          columns=[
              "ID",
              "Fecha",
              "Usuario",
              "Concepto",
              "Importe",
              "Fichero",
              "Reembolsado",
              "Enlace Ticket",
          ]
      )
  else:
    st.session_state.gastos = pd.DataFrame(
        columns=[
            "ID",
            "Fecha",
            "Usuario",
            "Concepto",
            "Importe",
            "Fichero",
            "Reembolsado",
            "Enlace Ticket",
        ]
    )

if "saldo_caja" not in st.session_state and usuario_autenticado_en_sesion():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    try:
      caja = {item.get("clave"): item.get("valor") for item in storage.read_records("Caja")}
      st.session_state.saldo_caja = float(caja.get("saldo_caja", 0.0))
    except (StorageOperationError, SupabaseStorageOperationError, TypeError, ValueError):
      st.session_state.saldo_caja = 0.0
  elif os.path.exists(SALDO_FILE) and not usar_almacenamiento_google():
    try:
      with open(SALDO_FILE, "r") as f:
        st.session_state.saldo_caja = float(f.read().strip())
    except:
      st.session_state.saldo_caja = 1250.50
  else:
    st.session_state.saldo_caja = 1250.50


def guardar_gastos_persistentes():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    if usar_almacenamiento_supabase(storage):
      return True
    if not hasattr(storage, "replace_records"):
      return False
    try:
      storage.replace_records("Gastos", st.session_state.gastos.to_dict(orient="records"))
      return True
    except (StorageOperationError, SupabaseStorageOperationError):
      return False
  if usar_almacenamiento_google():
    return False
  return guardar_excel_atomico(st.session_state.gastos, EXCEL_FILE)


def guardar_saldo_persistente(usuario):
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if storage:
    if usar_almacenamiento_supabase(storage):
      try:
        return storage.actualizar_saldo(float(st.session_state.saldo_caja), usuario)
      except SupabaseStorageOperationError:
        return False
    try:
      storage.replace_records("Caja", [{"clave": "saldo_caja", "valor": st.session_state.saldo_caja}])
      return True
    except (StorageOperationError, SupabaseStorageOperationError):
      return False
  if usar_almacenamiento_google():
    return False
  return guardar_texto_atomico(st.session_state.saldo_caja, SALDO_FILE)

USER_REQUIRED_COLUMNS = {
    "Nombre",
    "rol",
    "password_salt",
    "password_hash",
    "email",
    "tel",
    "fnac",
    "instrumento",
    "rgpd",
}


def cargar_usuarios_seguro():
  """Carga solo el registro v2 con contraseñas hasheadas y roles explícitos."""
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if usar_almacenamiento_google() and not storage:
    return {}
  if storage:
    try:
      df_u = pd.DataFrame(storage.read_records("Usuarios"))
      df_u.rename(columns={"telefono": "tel", "fecha_nacimiento": "fnac"}, inplace=True)
      if "activo" in df_u.columns:
        df_u = df_u[df_u["activo"].astype(str).str.lower() != "false"]
    except (StorageOperationError, SupabaseStorageOperationError):
      return {}
  elif not os.path.exists(EXCEL_USUARIOS):
    return {}
  else:
    try:
      df_u = pd.read_excel(EXCEL_USUARIOS)
    except Exception:
      return {}
  try:
    if not USER_REQUIRED_COLUMNS.issubset(df_u.columns):
      return {}
    usuarios = {}
    for record in df_u.to_dict(orient="records"):
      nombre = normalize_display_name(record.get("Nombre"))
      if (
          not nombre
          or normalized_name_key(nombre)
          in {normalized_name_key(item) for item in usuarios}
          or str(record.get("rol")) not in {"admin", "usuario"}
          or not str(record.get("password_salt") or "")
          or not str(record.get("password_hash") or "")
      ):
        continue
      usuarios[nombre] = {
          "rol": str(record["rol"]),
          "password_salt": str(record["password_salt"]),
          "password_hash": str(record["password_hash"]),
          "email": str(record["email"]),
          "tel": str(record["tel"]),
          "fnac": str(record["fnac"]),
          "instrumento": str(record["instrumento"]),
          "rgpd": bool(record["rgpd"]),
        }
    return usuarios
  except Exception:
    return {}


def guardar_usuarios_excel():
  """Persiste el registro de usuarios de forma atómica y sin contraseñas."""
  try:
    df_u = pd.DataFrame.from_dict(
        st.session_state.usuarios_registrados, orient="index"
    ).reset_index()
    df_u.rename(columns={"index": "Nombre"}, inplace=True)
    df_u = df_u[
        [
            "Nombre",
            "rol",
            "password_salt",
            "password_hash",
            "email",
            "tel",
            "fnac",
            "instrumento",
            "rgpd",
        ]
    ]
    storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
    if storage:
      records = df_u.to_dict(orient="records")
      for record in records:
        record["activo"] = "true"
      storage.replace_records("Usuarios", records)
      return True
    if usar_almacenamiento_google():
      return False
    temporal = f"{EXCEL_USUARIOS}.tmp.xlsx"
    df_u.to_excel(temporal, index=False)
    os.replace(temporal, EXCEL_USUARIOS)
    return True
  except Exception:
    return False


INVITATION_COLUMNS = [
    "codigo_hash",
    "emitido_por",
    "creado_en",
    "caduca_en",
    "usado_por",
    "usado_en",
]


def cargar_invitaciones_seguras():
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if usar_almacenamiento_google() and not storage:
    return []
  if storage:
    try:
      df = pd.DataFrame(storage.read_records("Invitaciones"))
    except (StorageOperationError, SupabaseStorageOperationError):
      return []
  elif not os.path.exists(EXCEL_INVITACIONES):
    return []
  else:
    try:
      df = pd.read_excel(EXCEL_INVITACIONES)
    except Exception:
      return []
  try:
    if not set(INVITATION_COLUMNS).issubset(df.columns):
      return []
    invitaciones = []
    for record in df[INVITATION_COLUMNS].to_dict(orient="records"):
      def valor_celda(key):
        value = record.get(key)
        return "" if pd.isna(value) else str(value)

      code_hash = valor_celda("codigo_hash")
      if re.fullmatch(r"[0-9a-f]{64}", code_hash):
        invitaciones.append({key: valor_celda(key) for key in INVITATION_COLUMNS})
    return invitaciones
  except Exception:
    return []


def guardar_invitaciones_excel():
  try:
    df = pd.DataFrame(st.session_state.invitaciones, columns=INVITATION_COLUMNS)
    storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
    if storage:
      storage.replace_records("Invitaciones", df.to_dict(orient="records"))
      return True
    if usar_almacenamiento_google():
      return False
    temporal = f"{EXCEL_INVITACIONES}.tmp.xlsx"
    df.to_excel(temporal, index=False)
    os.replace(temporal, EXCEL_INVITACIONES)
    return True
  except Exception:
    return False


def crear_invitacion(usuario_admin, dias_validez):
  codigo = generate_invitation_code()
  ahora = datetime.datetime.now(datetime.timezone.utc)
  registro = {
      "codigo_hash": hash_invitation_code(codigo),
      "emitido_por": str(usuario_admin),
      "creado_en": ahora.isoformat(),
      "caduca_en": (ahora + datetime.timedelta(days=dias_validez)).isoformat(),
      "usado_por": "",
      "usado_en": "",
  }
  storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
  if usar_almacenamiento_supabase(storage):
    try:
      storage.crear_invitacion(registro["codigo_hash"], usuario_admin, registro["caduca_en"])
      st.session_state.invitaciones.append(registro)
      return codigo
    except SupabaseStorageOperationError:
      return None
  st.session_state.invitaciones.append(registro)
  if guardar_invitaciones_excel():
    return codigo
  st.session_state.invitaciones.pop()
  return None


def invitacion_valida(codigo):
  ahora = datetime.datetime.now(datetime.timezone.utc)
  for registro in st.session_state.invitaciones:
    if registro.get("usado_por"):
      continue
    try:
      caduca_en = datetime.datetime.fromisoformat(registro["caduca_en"])
    except (TypeError, ValueError):
      continue
    if caduca_en < ahora:
      continue
    if verify_invitation_code(codigo, registro.get("codigo_hash")):
      return registro
  return None


def consumir_invitacion(codigo, usuario):
  registro = invitacion_valida(codigo)
  if not registro:
    return False
  registro["usado_por"] = str(usuario)
  registro["usado_en"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
  if guardar_invitaciones_excel():
    return True
  registro["usado_por"] = ""
  registro["usado_en"] = ""
  return False


def obtener_token_bootstrap():
  try:
    return str(st.secrets.get("bootstrap_admin_token", ""))
  except Exception:
    return ""


def es_administrador(nombre):
  return bool(
      nombre
      and st.session_state.usuarios_registrados.get(nombre, {}).get("rol")
      == "admin"
  )


if "usuarios_registrados" not in st.session_state:
  st.session_state.usuarios_registrados = cargar_usuarios_seguro()

if "invitaciones" not in st.session_state:
  st.session_state.invitaciones = cargar_invitaciones_seguras()

if "usuario_autenticado" not in st.session_state:
  st.session_state.usuario_autenticado = None

if "ultimo_acceso" not in st.session_state:
  st.session_state.ultimo_acceso = datetime.datetime.now()

if "fallos_acceso" not in st.session_state:
  st.session_state.fallos_acceso = 0

if "bloqueado_hasta" not in st.session_state:
  st.session_state.bloqueado_hasta = None

if "mostrar_recuperacion" not in st.session_state:
  st.session_state.mostrar_recuperacion = False

# El retorno de Google abre una pestaña independiente. Recuperamos la sesión
# únicamente si vuelve un código de OAuth con un estado cifrado y firmado que
# esta misma aplicación emitió hace menos de quince minutos.
if not st.session_state.usuario_autenticado:
  codigo_oauth_retorno = str(st.query_params.get("code", "")).strip()
  estado_oauth_retorno = str(st.query_params.get("state", "")).strip()
  if codigo_oauth_retorno and estado_oauth_retorno:
    try:
      config_retorno = GoogleDriveOAuthConfig.from_secrets(st.secrets)
      usuario_retorno = returning_user_from_state(
          config_retorno, estado_oauth_retorno
      )
    except GoogleDriveOAuthConfigurationError:
      usuario_retorno = None
    if usuario_retorno and es_administrador(usuario_retorno):
      st.session_state.usuario_autenticado = usuario_retorno
      st.session_state.ultimo_acceso = datetime.datetime.now()
      # El primer pase se inició antes de recuperar la sesión: se reinicia para
      # cargar los datos de trabajo en el orden normal y sin destellos ni fallos.
      st.rerun()

if st.session_state.usuario_autenticado:
  ahora = datetime.datetime.now()
  tiempo_inactivo = ahora - st.session_state.ultimo_acceso
  if tiempo_inactivo > datetime.timedelta(minutes=30):
    st.session_state.usuario_autenticado = None
  else:
    st.session_state.ultimo_acceso = ahora

# ==============================================================================
# --- PANTALLA DE ACCESO Y REGISTRO --------------------------------------------
# ==============================================================================
if not st.session_state.usuario_autenticado:

  if logo_fuego_file:
    html_logo = render_logo_png(logo_fuego_file, width=210)
    if html_logo:
      st.markdown(html_logo, unsafe_allow_html=True)

  frase_actual = random.choice(FRASES_SAFARA)
  st.markdown(
      f'<div class="frase-chapa-badge">"{frase_actual}"</div>',
      unsafe_allow_html=True,
  )

  tab_login, tab_registro = st.tabs(["ACCESO SAFARERS", "UNIRSE AL GRUPO"])

  with tab_login:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    nombres_disponibles = ["Selecciona tu usuario..."] + sorted(
        st.session_state.usuarios_registrados.keys(), key=normalized_name_key
    )
    nombre_login = st.selectbox("Safarer", nombres_disponibles)
    password_login = st.text_input(
        "Contraseña de Acceso",
        type="password",
        placeholder="Introduce tu contraseña",
    )

    if st.button("¡VAAAMONOSSS!"):
      bloqueado_hasta = st.session_state.bloqueado_hasta
      if bloqueado_hasta and datetime.datetime.now() < bloqueado_hasta:
        segundos = int((bloqueado_hasta - datetime.datetime.now()).total_seconds()) + 1
        st.error(f"Espera {segundos} segundos antes de intentarlo de nuevo.")
      elif nombre_login == "Selecciona tu usuario...":
        st.error("Por favor, selecciona tu nombre.")
      elif not password_login:
        st.error("Por favor, introduce tu contraseña.")
      else:
        user_info = st.session_state.usuarios_registrados.get(nombre_login)
        if user_info and verify_password(
            password_login,
            user_info.get("password_salt"),
            user_info.get("password_hash"),
        ):
          st.session_state.usuario_autenticado = nombre_login
          st.session_state.ultimo_acceso = datetime.datetime.now()
          st.session_state.fallos_acceso = 0
          st.session_state.bloqueado_hasta = None
          registrar_auditoria("inicio_sesion", nombre_login)
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        else:
          st.session_state.fallos_acceso += 1
          if st.session_state.fallos_acceso >= 5:
            st.session_state.bloqueado_hasta = datetime.datetime.now() + datetime.timedelta(
                minutes=1
            )
            st.session_state.fallos_acceso = 0
            st.error("Demasiados intentos. El acceso queda bloqueado durante un minuto.")
          else:
            st.error("Contraseña incorrecta.")

    if not st.session_state.mostrar_recuperacion:
      if st.button(
          "¿Has olvidado la contraseña?",
          key="btn_recuperar_toggle",
      ):
        st.session_state.mostrar_recuperacion = True
        st.rerun()

    if st.session_state.mostrar_recuperacion:
      st.markdown(
          "<p style='color:#E74C3C; font-size:0.8rem; font-weight:700;"
          " margin-top:10px; text-align:center;'>Por seguridad, la"
          " contraseña no se envía ni se muestra. Contacta con una persona"
          " administradora para restablecerla.</p>",
          unsafe_allow_html=True,
      )
      if st.button("Cerrar"):
        st.session_state.mostrar_recuperacion = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

  with tab_registro:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    primer_usuario = not st.session_state.usuarios_registrados
    with st.form("form_registro_completo", clear_on_submit=True):
      reg_nombre = st.text_input("Nombre y Apellidos *")
      reg_email = st.text_input("Correo Electrónico *")
      reg_tel = st.text_input("Teléfono Móvil de contacto *")
      reg_password = st.text_input(
          "Contraseña de Acceso *",
          type="password",
          help="Mínimo 12 caracteres, con letras y números.",
      )
      reg_password_confirm = st.text_input(
          "Repite la contraseña *", type="password"
      )

      token_bootstrap = ""
      codigo_invitacion = ""
      if primer_usuario:
        st.info(
            "Primera alta: se creará la persona administradora inicial."
        )
        token_bootstrap = st.text_input(
            "Secreto de configuración inicial *",
            type="password",
            help="Solo está en Streamlit Secrets; no se guarda en la aplicación.",
        )
      else:
        st.info(
            "Para proteger al grupo, las nuevas altas requieren un código de invitación de un solo uso."
        )
        codigo_invitacion = st.text_input(
            "Código de invitación *", type="password"
        )

      st.markdown("**Fecha de Nacimiento (Día / Mes / Año):**")
      col_d, col_m, col_a = st.columns(3)
      with col_d:
        reg_dia = st.number_input("Día", 1, 31, 15)
      with col_m:
        reg_mes = st.number_input("Mes", 1, 12, 6)
      with col_a:
        reg_anio = st.number_input("Año", 1950, 2018, 1998)

      reg_instrumento = st.selectbox(
          "Instrumento Principal",
          ["Repenike", "Caja", "Surdo", "Surdo de contra", "Ganza (bailarinas)"],
      )

      st.markdown("---")
      st.markdown(
          """
                <div style="background: rgba(18, 18, 18, 0.7); border: 1px solid rgba(231, 76, 60, 0.3); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
                    <p style="color: #E74C3C; font-size: 0.75rem; font-weight: 700; margin: 0 0 4px 0;">Protección de Datos y Derechos de Imagen (RGPD)</p>
                    <p style="color: #AAAAAA; font-size: 0.7rem; margin: 0;">De conformidad con el RGPD (UE 2016/679) y LOPDGDD 3/2018, los datos recabados por SAFARA PERCUSSION serán utilizados para la gestión interna del grupo y autorización de imagen en redes oficiales.</p>
                </div>
                """,
          unsafe_allow_html=True,
      )

      reg_acepta_rgpd = st.checkbox(
          "Acepto la política de privacidad y autorizo derechos de imagen *"
      )

      btn_reg_submit = st.form_submit_button("SOLICITAR ALTA")

      if btn_reg_submit:
        nombre_limpio = normalize_display_name(reg_nombre)
        email_limpio = validate_email(reg_email)
        telefono_limpio = validate_phone(reg_tel)
        error_nombre = validate_display_name(nombre_limpio)
        error_password = validate_password(reg_password)
        ya_registrado = any(
            normalized_name_key(nombre_limpio) == normalized_name_key(nombre)
            for nombre in st.session_state.usuarios_registrados
        )
        if not (reg_nombre and reg_email and reg_tel and reg_password):
          st.error("Por favor, completa todos los campos obligatorios.")
        elif error_nombre:
          st.error(error_nombre)
        elif not email_limpio:
          st.error("Introduce un correo electrónico válido.")
        elif not telefono_limpio:
          st.error("Introduce un teléfono móvil válido.")
        elif error_password:
          st.error(error_password)
        elif reg_password != reg_password_confirm:
          st.error("Las contraseñas no coinciden.")
        elif not reg_acepta_rgpd:
          st.warning(
              "Debes aceptar la casilla de Protección de Datos e Imagen."
          )
        elif ya_registrado:
          st.error("Este nombre ya está registrado en el sistema.")
        elif primer_usuario and not verify_bootstrap_token(
            token_bootstrap, obtener_token_bootstrap()
        ):
          st.error(
              "No se ha podido verificar la configuración inicial. Revisa el secreto de Streamlit."
          )
        elif not primer_usuario and not usar_almacenamiento_supabase() and not invitacion_valida(codigo_invitacion):
          st.error("El código de invitación no es válido, ya se ha usado o ha caducado.")
        else:
          fecha_nac_str = f"{reg_dia:02d}/{reg_mes:02d}/{reg_anio}"
          password_salt, password_hash = hash_password(reg_password)
          nuevo_usuario = {
              "rol": "admin" if primer_usuario else "usuario",
              "password_salt": password_salt,
              "password_hash": password_hash,
              "email": email_limpio,
              "tel": telefono_limpio,
              "fnac": fecha_nac_str,
              "instrumento": reg_instrumento,
              "rgpd": True,
          }
          storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
          if usar_almacenamiento_supabase(storage):
            try:
              alta_guardada = storage.registrar_usuario(
                  nombre_limpio, nuevo_usuario, codigo_invitacion
              )
            except SupabaseStorageAuthenticationError:
              alta_guardada = None
              mensaje_error_conexion = (
                  "La contraseña privada de Supabase no coincide. No se ha creado "
                  "el alta; actualiza la conexión en Streamlit Secrets."
              )
            except SupabaseStorageOperationError:
              alta_guardada = None
              mensaje_error_conexion = (
                  "No se ha podido conectar con la base segura. No se ha creado "
                  "el alta; revisa la conexión privada."
              )
            if alta_guardada is None:
              st.error(mensaje_error_conexion)
            elif not alta_guardada:
              st.error("El código de invitación no es válido, ya se ha usado o ha caducado.")
            else:
              st.session_state.usuarios_registrados[nombre_limpio] = nuevo_usuario
              registrar_auditoria("alta_usuario", nombre_limpio, nuevo_usuario["rol"])
              actualizar_informes_y_copias_en_segundo_plano()
              st.success("¡Alta creada! Ya puedes acceder con tu contraseña.")
          else:
            st.session_state.usuarios_registrados[nombre_limpio] = nuevo_usuario
            if not guardar_usuarios_excel():
              del st.session_state.usuarios_registrados[nombre_limpio]
              st.error("No se ha podido guardar el alta. Inténtalo de nuevo.")
            elif not primer_usuario and not consumir_invitacion(
                codigo_invitacion, nombre_limpio
            ):
              del st.session_state.usuarios_registrados[nombre_limpio]
              guardar_usuarios_excel()
              st.error("No se ha podido confirmar el código. Inténtalo de nuevo.")
            else:
              registrar_auditoria("alta_usuario", nombre_limpio, nuevo_usuario["rol"])
              st.success("¡Alta creada! Ya puedes acceder con tu contraseña.")
    st.markdown("</div>", unsafe_allow_html=True)

  st.stop()

# ==============================================================================
# --- APLICACIÓN PRINCIPAL (POST-LOGIN) ----------------------------------------
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado
hoy_act = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()

primer_bolo_conf = None
if "actuaciones" in st.session_state and isinstance(
    st.session_state.actuaciones, list
):
  for a in st.session_state.actuaciones:
    f_act = a.get("fecha")
    if isinstance(f_act, str):
      try:
        f_act = datetime.date.fromisoformat(f_act)
      except:
        f_act = hoy_act

    votos_bolo = obtener_todos_votos_encuesta(f"bolo_{a['id']}")
    conf_cnt = (
        len(votos_bolo[votos_bolo["respuesta"] == "SI"])
        if not votos_bolo.empty
        else 0
    )

    if (
        a.get("estado") == "CONFIRMADA" or conf_cnt >= QUORUM_BOLO_MINIMO
    ) and f_act >= hoy_act:
      primer_bolo_conf = a
      break

if primer_bolo_conf:
  txt_ticker = f"🚨 ATENCIÓN SAFARA • Próximo Bolo: {primer_bolo_conf['titulo']} ({primer_bolo_conf['lugar']}) • ¡Confirma tu asistencia en la Agenda! 🔥"
else:
  txt_ticker = (
      "🚨 ATENCIÓN SAFARA • Próximos ensayos y eventos disponibles en la"
      " agenda. ¡Somos Fuego! 🔥"
  )

st.markdown(
    f"""
    <div class="ticker-container">
        <div class="ticker-text">{escapar_html(txt_ticker)}</div>
    </div>
""",
    unsafe_allow_html=True,
)

col_head_left, col_head_right = st.columns([3, 1])
with col_head_right:
  st.markdown('<div class="btn-logout-discreto">', unsafe_allow_html=True)
  if st.button("⏻ ¡Me pirooooo!", key="btn_logout_piro"):
    st.session_state.usuario_autenticado = None
    st.session_state.mostrar_recuperacion = False
    st.rerun()
  st.markdown("</div>", unsafe_allow_html=True)

src_avatar = (
    render_logo_inline_b64(logo_fuego_file) if logo_fuego_file else None
)
fecha_hoy_str = obtener_fecha_espanol()

with col_head_left:
  img_html = (
      f'<img src="{src_avatar}" />'
      if src_avatar
      else '<span style="font-size:20px; color:#E74C3C; font-weight:800;">S</span>'
  )
  st.markdown(
      f"""
        <div style="display: flex; align-items: center; gap: 15px; padding: 5px 0;">
            <div style="width: 50px; height: 50px; border-radius: 50%; background: #0D0D0D; border: 2px solid #E74C3C; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                {img_html}
            </div>
            <div>
                <h3 style="margin: 0; font-size: 18px; color: #FFFFFF;">¡Hola, {escapar_html(usuario_actual)}!</h3>
                <p style="margin: 0; font-size: 12px; color: #AAAAAA;">{fecha_hoy_str}</p>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown(
    f'<div class="frase-chapa-badge">"{random.choice(FRASES_SAFARA)}"</div>',
    unsafe_allow_html=True,
)

tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(
    ["Nuestras Movidas", "Agenda & Bolos", "Caja & Finanzas", "Administración"]
)

# --- PESTAÑA 1: NUESTRAS MOVIDAS ---
with tab_movidas:
  cumpleaneros_hoy = []
  for nombre_u, u_data in st.session_state.usuarios_registrados.items():
    fnac = u_data.get("fnac")
    if fnac and isinstance(fnac, str) and "/" in fnac:
      try:
        p_dia, p_mes, _ = fnac.split("/")
        if int(p_dia) == hoy_m.day and int(p_mes) == hoy_m.month:
          cumpleaneros_hoy.append(nombre_u)
      except:
        pass

  if cumpleaneros_hoy:
    for c_nombre in cumpleaneros_hoy:
      st.markdown(
          f"""
                <div style="background: linear-gradient(135deg, #E74C3C 0%, #900C3F 100%); border-radius: 14px; padding: 14px; text-align: center; margin-bottom: 15px; color: #FFF; box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);">
                    <strong style="font-size: 16px; color: #FFF;">¡HOY ES EL CUMPLEAÑOS DE {c_nombre.upper()}!</strong><br>
                    <span style="font-size: 13px; font-style: italic; font-weight: 600; color: #DDD;">"{random.choice(FRASES_CUMPLE)}"</span>
                </div>
            """,
          unsafe_allow_html=True,
      )

  ensayo_info = informacion_ensayo()
  ensayo_info["url_maps"] = UBICACIONES_ENSAYO[ensayo_info["ubicacion_nombre"]]
  historial_ensayos = sincronizar_historial_ensayos()
  fecha_ens_str = (
      ensayo_info["fecha"].strftime("%d/%m/%Y")
      if isinstance(ensayo_info["fecha"], datetime.date)
      else str(ensayo_info["fecha"])
  )

  df_votos_ensayo = obtener_todos_votos_encuesta("ensayo_proximo")
  confirmados_list = (
      df_votos_ensayo[df_votos_ensayo["respuesta"] == "SI"][
          "usuario_id"
      ].tolist()
      if not df_votos_ensayo.empty
      else []
  )
  num_confirmados = len(confirmados_list)

  counts = {
      "Repenike": 0,
      "Caja": 0,
      "Surdo": 0,
      "Surdo de contra": 0,
      "Ganza (bailarinas)": 0,
  }
  for c_user in confirmados_list:
    u_inst = st.session_state.usuarios_registrados.get(c_user, {}).get(
        "instrumento", "Repenike"
    )
    if u_inst in counts:
      counts[u_inst] += 1

  ensayo_confirmado = (
      num_confirmados >= QUORUM_ENSAYO_MINIMO
      and counts["Repenike"] >= 1
      and counts["Caja"] >= 1
  )
  badge_estado_ens = (
      "🟢 CONFIRMADO" if ensayo_confirmado else "🟡 PENDIENTE DE QUÓRUM"
  )
  color_badge_ens = "#2ECC71" if ensayo_confirmado else "#E74C3C"

  st.markdown(
      f"""
        <div style="background: linear-gradient(145deg, #180E00 0%, #0D0D0D 100%); border: 2px solid #E74C3C; border-radius: 18px; padding: 18px; text-align: center; margin-bottom: 15px;">
            <span style="background: {color_badge_ens}; color: #000; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 800;">{badge_estado_ens}</span>
            <h3 style="color: #FFFFFF; margin: 10px 0 4px 0; font-size: 18px;">PRÓXIMO ENSAYO</h3>
            <p style="font-size: 15px; margin: 4px 0;"><b>Fecha:</b> {fecha_ens_str} ({ensayo_info['hora']})</p>
            <p style="font-size: 14px; margin: 4px 0;"><b>Ubicación:</b> {ensayo_info['ubicacion_nombre']}</p>
            <div style="margin-top: 10px;">
                <a href="{ensayo_info['url_maps']}" target="_blank" style="background: #E74C3C; color: #FFF; padding: 8px 16px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block;">
                    Ver Ubicación en Google Maps 📍
                </a>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      """
        <div style="text-align: center; margin: 15px 0 10px 0;">
            <h4 style="color: #FFFFFF; font-size: 16px; margin-bottom: 2px;">¿Le damos caña este viernes?</h4>
            <p style="font-size: 11px; color: #AAA; margin-top: 0;">Pulsa el logo correspondiente para responder:</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  if ensayo_info["votacion_abierta"]:
    voto_ens_actual = obtener_voto_usuario("ensayo_proximo", usuario_actual)
    img_si_cls = (
        "poll-img-green-sel"
        if voto_ens_actual == "SI"
        else "poll-img-green-norm"
    )
    img_no_cls = (
        "poll-img-red-sel" if voto_ens_actual == "NO" else "poll-img-red-norm"
    )

    st.markdown(
        f"""
          <div class="safara-poll-row">
              <div class="safara-poll-col">
                  <img src="{logo_b64_inline}" class="poll-img-btn {img_si_cls}" />
                  <div class="poll-label-green">A tope, se le da</div>
              </div>
              <div class="safara-poll-col">
                  <img src="{logo_b64_inline}" class="poll-img-btn {img_no_cls}" />
                  <div class="poll-label-red">No puedo, tengo lío</div>
              </div>
          </div>
      """,
        unsafe_allow_html=True,
    )

    voto_ens_si, voto_ens_no = st.columns(2)
    with voto_ens_si:
      if st.button("A tope, se le da", key="btn_ens_si"):
        if registrar_voto_backend("ensayo_proximo", usuario_actual, "SI"):
          st.rerun()
    with voto_ens_no:
      if st.button("No puedo, tengo lío", key="btn_ens_no"):
        if registrar_voto_backend("ensayo_proximo", usuario_actual, "NO"):
          st.rerun()
  else:
    st.info("La encuesta semanal está cerrada. El resultado queda guardado en el historial y la siguiente se abrirá el lunes a las 08:00.")

  st.markdown(
      f"<p style='text-align: center; font-size: 14px; font-weight: 800;"
      f" color: #E74C3C; margin-top: 12px;'>{num_confirmados} Safarers han"
      " confirmado para este viernes</p>",
      unsafe_allow_html=True,
  )

  if confirmados_list:
    st.caption(
        f"Repenikes: {counts['Repenike']} | Cajas: {counts['Caja']} |"
        f" Surdos: {counts['Surdo']} | Surdos de contra:"
        f" {counts['Surdo de contra']} | Bailarinas:"
        f" {counts['Ganza (bailarinas)']}"
    )

  if historial_ensayos:
    ensayos_confirmados = sum(
        1 for ensayo in historial_ensayos if ensayo.get("estado") == "CONFIRMADO"
    )
    st.caption(
        f"Historial técnico: {ensayos_confirmados} ensayos confirmados de "
        f"{len(historial_ensayos)} semanas cerradas."
    )

  st.markdown("---")

  st.markdown(
      """
        <div style="background: linear-gradient(145deg, #12141a 0%, #1a0f00 100%); border: 1px solid #E74C3C; border-radius: 16px; padding: 16px; text-align: center; margin-bottom: 12px;">
            <h4 style="color: #FFFFFF; margin: 0; font-size: 15px;">CENICA POST-ENSAYO</h4>
            <p style="font-size: 13px; color: #FFD700; font-style: italic; font-weight: 600; margin-top: 4px; margin-bottom: 0;">¡Aquí se viene a lo que se viene!</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  voto_cena_actual = obtener_voto_usuario("cena_proxima", usuario_actual)
  c_img_si_cls = (
      "poll-img-green-sel"
      if voto_cena_actual == "SI"
      else "poll-img-green-norm"
  )
  c_img_no_cls = (
      "poll-img-red-sel" if voto_cena_actual == "NO" else "poll-img-red-norm"
  )

  st.markdown(
      f"""
        <div class="safara-poll-row">
            <div class="safara-poll-col">
                <img src="{logo_b64_inline}" class="poll-img-btn {c_img_si_cls}" />
                <div class="poll-label-green">A tope, se le da</div>
            </div>
            <div class="safara-poll-col">
                <img src="{logo_b64_inline}" class="poll-img-btn {c_img_no_cls}" />
                <div class="poll-label-red">No puedo, tengo lío</div>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  voto_cena_si, voto_cena_no = st.columns(2)
  with voto_cena_si:
    if st.button("A tope, se le da", key="btn_cena_si"):
      if registrar_voto_backend("cena_proxima", usuario_actual, "SI"):
        st.rerun()
  with voto_cena_no:
    if st.button("No puedo, tengo lío", key="btn_cena_no"):
      if registrar_voto_backend("cena_proxima", usuario_actual, "NO"):
        st.rerun()

  df_votos_cena = obtener_todos_votos_encuesta("cena_proxima")
  num_cenan = (
      len(df_votos_cena[df_votos_cena["respuesta"] == "SI"])
      if not df_votos_cena.empty
      else 0
  )
  st.markdown(
      f"<p style='text-align: center; font-size: 13px; font-weight: 800;"
      f" color: #2ECC71; margin-top: 8px;'>🟢 {num_cenan} Safarers confirmados"
      " para cena</p>",
      unsafe_allow_html=True,
  )

  st.markdown("---")

  st.markdown(
      "<h4 style='color: #E74C3C;'>Evolución de Actuaciones Safara</h4>",
      unsafe_allow_html=True,
  )

  m_col1, m_col2, m_col3 = st.columns(3)
  with m_col1:
    st.metric("2024", "5 bolos")
  with m_col2:
    st.metric("2025", "21 bolos")
  with m_col3:
    st.metric("2026", "14 bolos")

  st.caption("CRECIMIENTO: ¡Más de 40 bolos acumuladas! ¡Esto está que arde!")

  st.markdown("---")

  st.markdown(
      "<h4 style='color: #E74C3C;'>Safara en Redes Sociales</h4>",
      unsafe_allow_html=True,
  )

  r_col1, r_col2 = st.columns(2)
  with r_col1:
    st.markdown(
        """
            <div style="background: #12141a; border: 1px solid #E74C3C; border-radius: 12px; padding: 12px; text-align: center;">
                <b style="color: #FFFFFF;">Instagram Oficial</b><br><br>
                <a href="https://www.instagram.com/safarapercussion?srtk=Ym9jYTB0eWF2cjQz" target="_blank" style="background: #E1306C; color: #FFF; padding: 6px 12px; border-radius: 8px; font-weight: 800; text-decoration: none; display: inline-block; font-size: 0.75rem;">
                    Ver Instagram
                </a>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with r_col2:
    st.markdown(
        """
            <div style="background: #12141a; border: 1px solid #E74C3C; border-radius: 12px; padding: 12px; text-align: center;">
                <b style="color: #FFFFFF;">TikTok Oficial</b><br><br>
                <a href="https://www.tiktok.com/@safarapercussion?_r=1&_t=ZN-9ASh8h0A2Le" target="_blank" style="background: #000; color: #FFF; border: 1px solid #FFF; padding: 6px 12px; border-radius: 8px; font-weight: 800; text-decoration: none; display: inline-block; font-size: 0.75rem;">
                    Ver TikTok
                </a>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("---")

  st.markdown(
      "<h4 style='color: #E74C3C;'>El Confesionario</h4>",
      unsafe_allow_html=True,
  )
  with st.form("form_confesionario_directo", clear_on_submit=True):
    confesion_txt = st.text_area(
        "Tu mensaje confidencial para el grupo",
        placeholder="Escribe tu idea o propuesta aquí...",
        key="confesion_input_txt",
    )
    btn_enviar_conf = st.form_submit_button("ENVIAR AL CONFESIONARIO")

    if btn_enviar_conf:
      if confesion_txt and confesion_txt.strip():
        fecha_actual_str = datetime.datetime.now(
            ZoneInfo("Europe/Madrid")
        ).strftime("%d/%m/%Y %H:%M")
        nuevo_msg = {
            "fecha": fecha_actual_str,
            "usuario": usuario_actual,
            "mensaje": confesion_txt.strip(),
        }
        storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
        if usar_almacenamiento_supabase(storage):
          try:
            storage.guardar_confesion(usuario_actual, confesion_txt.strip())
            confesion_guardada = True
          except SupabaseStorageOperationError:
            confesion_guardada = False
        else:
          st.session_state.confesionario_mensajes.append(nuevo_msg)
          confesion_guardada = guardar_confesionario_excel()
        if confesion_guardada:
          if usar_almacenamiento_supabase(storage):
            st.session_state.confesionario_mensajes.append(nuevo_msg)
          registrar_auditoria("mensaje_confesionario", usuario_actual)
          st.success("¡Mensaje guardado con éxito en el confesionario!")
        else:
          if not usar_almacenamiento_supabase(storage):
            st.session_state.confesionario_mensajes.pop()
          st.error("No se ha podido guardar tu mensaje. Inténtalo de nuevo.")
      else:
        st.error("Por favor, escribe un mensaje antes de enviar.")

# ==============================================================================
# --- PESTAÑA 2: AGENDA & BOLOS (ENCUESTAS HORIZONTALES SIN REDIRECCIÓN) ------
# ==============================================================================
with tab_eventos:
  st.markdown(
      "<h3 style='color: #E74C3C;'>Agenda de Actuaciones y Encuestas</h3>",
      unsafe_allow_html=True,
  )

  actuaciones_list = st.session_state.actuaciones

  if not actuaciones_list:
    st.info("No hay actuaciones o bolos registrados por ahora.")
  else:
    for ev in actuaciones_list:
      bolo_id = ev["id"]
      encuesta_key = f"bolo_{bolo_id}"

      votos_bolo_df = obtener_todos_votos_encuesta(encuesta_key)
      confirmados_bolo = (
          votos_bolo_df[votos_bolo_df["respuesta"] == "SI"]["usuario_id"].tolist()
          if not votos_bolo_df.empty
          else []
      )
      num_conf = len(confirmados_bolo)

      quorum_alcanzado = num_conf >= QUORUM_BOLO_MINIMO
      estado_ev_raw = str(ev.get("estado", "")).upper()
      es_anulada = estado_ev_raw == "ANULADA"
      es_confirmada_oficial = estado_ev_raw == "CONFIRMADA"
      es_bolo_confirmado = (
          es_confirmada_oficial or quorum_alcanzado
      ) and not es_anulada

      if es_anulada:
        estado_badge = "🔴 ACTUACIÓN ANULADA"
        color_badge = "#E74C3C"
        border_card = "1px solid #E74C3C"
      elif es_bolo_confirmado:
        estado_badge = (
            "🟢 CONFIRMADA (¡OFICIAL / QUÓRUM ALCANZADO!)"
            if es_confirmada_oficial
            else "🟢 CONFIRMADA (¡QUÓRUM ALCANZADO!)"
        )
        color_badge = "#2ECC71"
        border_card = "2px solid #2ECC71"
      else:
        estado_badge = (
            f"🟡 EN EVALUACIÓN ({num_conf}/{QUORUM_BOLO_MINIMO} VOTOS)"
        )
        color_badge = "#E74C3C"
        border_card = "1px solid #E74C3C"

      f_ev_str = (
          ev["fecha"].strftime("%d/%m/%Y")
          if isinstance(ev["fecha"], datetime.date)
          else str(ev["fecha"])
      )
      titulo_ev_html = escapar_html(ev.get("titulo"))
      hora_ev_html = escapar_html(ev.get("hora"))
      lugar_ev_html = escapar_html(ev.get("lugar"))

      st.markdown(
          f"""
            <div style="background: #12141a; border: {border_card}; border-radius: 16px; padding: 18px; margin-bottom: 12px;">
                <span style="background: {color_badge}; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800;">{estado_badge}</span>
                <h3 style="color: #FFFFFF; margin: 8px 0 4px 0; font-size: 18px;">{titulo_ev_html}</h3>
                <p style="font-size: 14px; margin: 4px 0; color: #DDD;">📅 <b>Fecha:</b> {escapar_html(f_ev_str)} ({hora_ev_html})</p>
                <p style="font-size: 14px; margin: 4px 0; color: #DDD;">📍 <b>Lugar:</b> {lugar_ev_html}</p>
            </div>
        """,
          unsafe_allow_html=True,
      )

      voto_bolo_actual = obtener_voto_usuario(encuesta_key, usuario_actual)

      if es_anulada:
        st.markdown(
            """
                <div style="background: rgba(231, 76, 60, 0.15); border: 1px solid #E74C3C; border-radius: 10px; padding: 10px; text-align: center; margin: 10px 0;">
                    <p style="color: #E74C3C; font-weight: 800; font-size: 13px; margin: 0;">🚫 Esta actuación ha sido anulada. Votaciones cerradas.</p>
                </div>
            """,
            unsafe_allow_html=True,
        )
      elif es_bolo_confirmado and voto_bolo_actual:
        txt_res = (
            "ASISTIRÉ A ESTE BOLO 🔥"
            if voto_bolo_actual == "SI"
            else "NO PUEDO ASISTIR ❌"
        )
        st.markdown(
            f"""
                <div style="background: rgba(46, 204, 113, 0.15); border: 1px solid #2ECC71; border-radius: 10px; padding: 10px; text-align: center; margin: 10px 0;">
                    <p style="color: #2ECC71; font-weight: 800; font-size: 13px; margin: 0;">✅ Tu respuesta registrada: {txt_res}</p>
                </div>
            """,
            unsafe_allow_html=True,
        )
      else:
        cls_b_si = (
            "poll-img-green-sel"
            if voto_bolo_actual == "SI"
            else "poll-img-green-norm"
        )
        cls_b_no = (
            "poll-img-red-sel"
            if voto_bolo_actual == "NO"
            else "poll-img-red-norm"
        )

        b_col_si, b_col_no = st.columns(2)
        with b_col_si:
          st.markdown(
              f"""
                    <div style="text-align: center;">
                        <img src="{logo_b64_inline}" class="poll-img-btn {cls_b_si}" />
                    </div>
                """,
              unsafe_allow_html=True,
          )
          if st.button("A tope, se le da", key=f"btn_v_si_{bolo_id}"):
            if registrar_voto_backend(encuesta_key, usuario_actual, "SI"):
              st.rerun()

        with b_col_no:
          st.markdown(
              f"""
                    <div style="text-align: center;">
                        <img src="{logo_b64_inline}" class="poll-img-btn {cls_b_no}" />
                    </div>
                """,
              unsafe_allow_html=True,
          )
          if st.button("No puedo, tengo lío", key=f"btn_v_no_{bolo_id}"):
            if registrar_voto_backend(encuesta_key, usuario_actual, "NO"):
              st.rerun()

      if not es_anulada:
        st.markdown(
            f"<p style='text-align: center; font-size: 13px; font-weight: 800;"
            f" color: #2ECC71; margin-top: 4px;'>🟢 {num_conf} Safarers"
            " confirmados para este bolo</p>",
            unsafe_allow_html=True,
        )

        if confirmados_bolo:
          counts_b = {
              "Repenike": 0,
              "Caja": 0,
              "Surdo": 0,
              "Surdo de contra": 0,
              "Ganza (bailarinas)": 0,
          }
          for c_user in confirmados_bolo:
            u_inst = st.session_state.usuarios_registrados.get(c_user, {}).get(
                "instrumento", "Repenike"
            )
            if u_inst in counts_b:
              counts_b[u_inst] += 1
            else:
              counts_b["Repenike"] += 1

          st.caption(
              f"Repenikes: {counts_b['Repenike']} | Cajas: {counts_b['Caja']} |"
              f" Surdos: {counts_b['Surdo']} | Surdos de contra:"
              f" {counts_b['Surdo de contra']} | Bailarinas:"
              f" {counts_b['Ganza (bailarinas)']}"
          )

      st.markdown("---")

# --- PESTAÑA 3: CAJA & FINANZAS ---
with tab_gastos_app:
  gastos_abonados_total = (
      st.session_state.gastos[
          st.session_state.gastos["Reembolsado"] == "ABONADO"
      ]["Importe"].sum()
      if not st.session_state.gastos.empty
      else 0.0
  )
  saldo_dinamico_actual = st.session_state.saldo_caja - gastos_abonados_total
  saldo_formateado_es = formato_espanol(saldo_dinamico_actual)

  st.markdown(
      f"""
        <div style="background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%); border: 2px solid #E74C3C; border-radius: 20px; padding: 24px 18px; text-align: center; box-shadow: 0 15px 40px rgba(231, 76, 60, 0.3); margin-bottom: 20px;">
            <h2 style="color: #E74C3C !important; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px;">Caja Rural de Navarra • Fondo Común</h2>
            <div style="font-size: 38px; font-weight: 800; color: #FFFFFF; margin: 6px 0;">{saldo_formateado_es} €</div>
            <p style="font-size: 12px; color: #888888;">Recaudación y gestión de fondos para ensayos, eventos y material.</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  total_gastos_registrados = (
      st.session_state.gastos["Importe"].sum()
      if not st.session_state.gastos.empty
      else 0.0
  )
  pend = (
      st.session_state.gastos[
          st.session_state.gastos["Reembolsado"] == "PENDIENTE ABONO"
      ]["Importe"].sum()
      if not st.session_state.gastos.empty
      else 0.0
  )

  m1, m2 = st.columns(2)
  with m1:
    st.metric(
        "Gastos Totales", f"{formato_espanol(total_gastos_registrados)} €"
    )
  with m2:
    st.metric("Pendiente Reembolso", f"{formato_espanol(pend)} €")

  st.write("")

  tab_sub_reg, tab_sub_hist = st.tabs(["Registrar Gasto", "Historial de Gastos"])

  with tab_sub_reg:
    categorias_safara = [
        "Parking",
        "Instrumentos (parches, mazas, repuestos)",
        "Bebidas",
        "Accesorios (Luces, complementos)",
        "Equipamiento (Ropa)",
        "Tasa Administración",
        "Restaurantes / Dietas",
        "Gasolina",
        "Otros",
    ]

    categoria_seleccionada = st.selectbox(
        "Categoría de Gasto *", categorias_safara
    )
    detalle_concepto = st.text_input(
        "Detalle adicional / Comercio",
        placeholder="Ej. Tam Tam, Bar Río, Parking Plaza Castillo...",
    )
    fichero = st.file_uploader(
        "Adjuntar Ticket (Imagen o PDF) *", type=["png", "jpg", "jpeg", "pdf"]
    )
    importe = st.number_input(
        "Importe (€) *", min_value=0.0, value=0.0, step=0.50, format="%.2f"
    )
    fecha = st.date_input(
        "Fecha del gasto *",
        datetime.date.today(),
        min_value=datetime.date(2023, 1, 1),
        max_value=datetime.date.today() + datetime.timedelta(days=1),
        format="DD/MM/YYYY",
    )

    if st.button("Guardar y Enviar Gasto"):
      if fichero is None:
        st.error(
            "❌ ES OBLIGATORIO ADJUNTAR EL TICKET O FOTO PARA REGISTRAR EL"
            " GASTO."
        )
      elif importe <= 0:
        st.error("Por favor, introduce un importe válido mayor a 0.")
      else:
        tamano_fichero = getattr(fichero, "size", 0)
        contenido_fichero = (
            fichero.getvalue()
            if isinstance(tamano_fichero, int) and tamano_fichero <= 10 * 1024 * 1024
            else b""
        )
        ext, error_fichero = validate_receipt_upload(
            fichero.name, tamano_fichero, contenido_fichero
        )
        if error_fichero:
          st.error(error_fichero)
        else:
          id_nuevo = (
              int(st.session_state.gastos["ID"].max() + 1)
              if not st.session_state.gastos.empty
              else 1
          )

          identificador_ticket = uuid.uuid4().hex[:16]
          nombre_fichero = (
              f"Gasto_{fecha}_{identificador_ticket}.{ext}"
          )
          mime_type = {
              "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "pdf": "application/pdf",
          }[ext]
          storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
          concepto_final = f"{categoria_seleccionada}" + (
              f" - {detalle_concepto}" if detalle_concepto else ""
          )
          nuevo_reg = {
              "ID": id_nuevo,
              "Fecha": str(fecha),
              "Usuario": usuario_actual,
              "Concepto": concepto_final,
              "Importe": float(importe),
              "Fichero": nombre_fichero,
              "Reembolsado": "PENDIENTE ABONO",
              "Enlace Ticket": "",
              "Drive File ID": "",
              "MIME Type": mime_type,
          }
          if usar_almacenamiento_supabase(storage):
            try:
              # La base segura confirma gasto y ticket antes de hablar con Drive.
              # Si Google falla, administración podrá reintentarlo sin pedir el archivo otra vez.
              nuevo_reg = storage.crear_gasto_con_justificante_pendiente(
                  nuevo_reg, contenido_fichero
              )
              gasto_guardado = True
            except SupabaseStorageOperationError:
              gasto_guardado = False
          else:
            # En pruebas, un gasto nunca puede caer en el guardado histórico.
            # Si la base segura no está lista, no se registra ni se pierde un
            # archivo local que pudiera dar una falsa sensación de éxito.
            st.error(
                "No se ha registrado el gasto: la base segura de Supabase no está disponible. "
                "La administración debe revisar el diagnóstico de conexión."
            )
            st.stop()
          if gasto_guardado:
            if usar_almacenamiento_supabase(storage):
              almacenamiento_drive = (
                  obtener_almacenamiento_drive() if google_storage_enabled(st.secrets) else None
              )
              try:
                if not almacenamiento_drive:
                  raise StorageOperationError(
                      _google_storage_error or "Google Drive está pendiente de autorización."
                  )
                drive_file_id, enlace_excel = almacenamiento_drive.upload_receipt(
                    nombre_fichero, contenido_fichero, mime_type
                )
                storage.confirmar_justificante_drive(
                    int(nuevo_reg["ID"]), drive_file_id, enlace_excel
                )
                nuevo_reg["Drive File ID"] = drive_file_id
                nuevo_reg["Enlace Ticket"] = enlace_excel
                nuevo_reg["Estado Justificante"] = "GUARDADO"
                aviso_justificante = "Justificante guardado de forma segura en Drive."
              except (StorageOperationError, SupabaseStorageOperationError) as error:
                detalle_drive = str(error).strip() or "Drive no está disponible temporalmente."
                try:
                  storage.marcar_justificante_pendiente(int(nuevo_reg["ID"]), detalle_drive)
                except SupabaseStorageOperationError:
                  pass
                nuevo_reg["Estado Justificante"] = "PENDIENTE_DRIVE"
                aviso_justificante = (
                    "El gasto y el justificante ya están protegidos en la base segura. "
                    "Drive se reintentará desde Administración cuando la autorización esté lista."
                )
              st.session_state.gastos = pd.concat(
                  [st.session_state.gastos, pd.DataFrame([nuevo_reg])], ignore_index=True,
              )
            else:
              aviso_justificante = "El gasto queda pendiente de revisión en el panel de administración."
            st.success("¡Gasto registrado con éxito!")
            registrar_auditoria(
                "gasto_registrado", usuario_actual, str(nuevo_reg.get("ID", id_nuevo))
            )
            # Supabase ya confirmó el gasto y, si procede, el ticket. Ahora se
            # actualiza Sheets como vista de consulta; un fallo externo nunca
            # revierte el gasto ni interrumpe a la persona que lo registró.
            actualizar_informes_y_copias_en_segundo_plano()
            st.info(aviso_justificante)
          else:
            st.error("No se ha podido guardar el gasto. Inténtalo de nuevo.")

  with tab_sub_hist:
    st.markdown(
        "<p style='color: #E74C3C; font-size: 14px; font-weight:"
        " 800;'>REGISTRO HISTÓRICO DE GASTOS</p>",
        unsafe_allow_html=True,
    )

    try:
      if (
          not st.session_state.gastos.empty
          and len(st.session_state.gastos) > 0
      ):
        filtro_estado = st.selectbox(
            "Filtrar Estado", ["Todos", "Pendientes Abono", "Abonados"]
        )
        df_view = st.session_state.gastos.copy()
        if filtro_estado == "Pendientes Abono":
          df_view = df_view[df_view["Reembolsado"] == "PENDIENTE ABONO"]
        elif filtro_estado == "Abonados":
          df_view = df_view[df_view["Reembolsado"] == "ABONADO"]

        for _, row in df_view.iterrows():
          estado_txt = str(row["Reembolsado"])
          color_badge = "#2ECC71" if estado_txt == "ABONADO" else "#E74C3C"
          try:
            fecha_visual = datetime.date.fromisoformat(
                str(row["Fecha"])
            ).strftime("%d/%m/%Y")
          except:
            fecha_visual = str(row["Fecha"])

          st.markdown(
              f"""
                        <div style="background: #121212; border-left: 5px solid #E74C3C; border: 1px solid #2A2A2A; padding: 14px; border-radius: 12px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: #FFFFFF; font-size: 14px;">{escapar_html(row['Concepto'])}</strong>
                                <span style="background: {color_badge}; color: #000; padding: 2px 7px; border-radius: 6px; font-size: 9px; font-weight: 800;">{estado_txt}</span>
                            </div>
                            <div style="margin-top: 6px; font-size: 12px; color: #FFFFFF;">
                                <span>Colaborador:</span> <b>{escapar_html(row['Usuario'])}</b> | <span>Fecha:</span> {escapar_html(fecha_visual)} | <span style="color: #E74C3C; font-weight: 800;">{formato_espanol(row['Importe'])} €</span>
                            </div>
                        </div>
                    """,
              unsafe_allow_html=True,
          )

          fich = row.get("Fichero")
          if fich and isinstance(fich, str) and str(fich) != "nan":
            enlace_drive = str(row.get("Enlace Ticket", ""))
            if enlace_drive.startswith("https://"):
              st.link_button(f"Abrir Ticket (Gasto #{row['ID']})", enlace_drive)
              continue
            path_fich = os.path.join(RECEIPTS_DIR, fich)
            if os.path.exists(path_fich):
              with st.expander(f"Previsualizar Ticket (Gasto #{row['ID']})"):
                ext = fich.lower().split(".")[-1]
                if ext in ["png", "jpg", "jpeg"]:
                  st.image(path_fich, use_container_width=True)
                elif ext == "pdf":
                  st.write(f"📄 Archivo PDF adjunto: `{fich}`")
                else:
                  st.write(f"📁 Archivo adjunto: `{fich}`")
      else:
        st.info("No hay gastos registrados todavía.")
    except Exception as e:
      st.warning("Cargando historial de gastos...")

# --- PESTAÑA 4: PANEL DE ADMINISTRACIÓN ---
with tab_admin_app:
  if not es_administrador(usuario_actual):
    st.info("Esta sección está disponible solo para personas administradoras.")
  else:
    st.success("Acceso de Administración Autorizado")
    # Al abrir Administración se recupera también cualquier actualización que
    # hubiera quedado pendiente (por ejemplo, un gasto registrado justo antes
    # de publicar esta mejora), sin exigir otro registro de prueba.
    actualizar_informes_y_copias_en_segundo_plano()

    # Estado breve y seguro: ayuda a comprobar el circuito completo sin
    # mostrar URLs privadas, tokens ni mensajes técnicos del proveedor.
    try:
      estado_seguro, _ = diagnostico_supabase_para_administracion()
      estado_google = (
          estado_seguro.estado_mantenimiento_google() if estado_seguro else {}
      )
    except SupabaseStorageOperationError:
      estado_google = {}
    if estado_google:
      informes_pendientes = (
          int(estado_google.get("sheets_revision", 0))
          != int(estado_google.get("sheets_synced_revision", 0))
      )
      columnas_estado = st.columns(3)
      columnas_estado[0].metric("Base segura", "ACTIVA")
      columnas_estado[1].metric(
          "Informes Google", "PENDIENTES" if informes_pendientes else "ACTUALIZADOS"
      )
      columnas_estado[2].metric(
          "Copia Drive", "PENDIENTE" if estado_google.get("ultimo_error") else "AL DÍA"
      )

    st.markdown("#### Autorizar justificantes en Google Drive")
    st.caption(
        "Conecta una sola vez el Drive de SAFARA para que los tickets se guarden "
        "con su propio espacio, sin usar la cuota de la cuenta técnica."
    )
    try:
      configuracion_drive_oauth = GoogleDriveOAuthConfig.from_secrets(st.secrets)
    except GoogleDriveOAuthConfigurationError:
      st.info("La autorización de Drive se está preparando. No es necesaria ninguna acción todavía.")
    else:
      almacenamiento_seguro, error_supabase = diagnostico_supabase_para_administracion()
      if not almacenamiento_seguro:
        st.error(error_supabase)
      else:
        codigo_google = str(st.query_params.get("code", "")).strip()
        estado_google = str(st.query_params.get("state", "")).strip()
        error_google = str(st.query_params.get("error", "")).strip()
        detalle_google = str(st.query_params.get("error_description", "")).strip()
        if error_google:
          # Google devuelve esta información en la URL de retorno. Se muestra
          # sin credenciales y se limpia para que no rompa sesiones posteriores.
          st.error(
              "Google no completó la autorización. "
              + (detalle_google[:300] if detalle_google else "Vuelve a iniciarla desde este panel.")
          )
          st.query_params.clear()
        if codigo_google or estado_google:
          if not (codigo_google and estado_google):
            st.error("Google no ha devuelto una autorización completa. Iníciala de nuevo.")
          else:
            try:
              permiso_cifrado = exchange_code_for_encrypted_token(
                  configuracion_drive_oauth, codigo_google, estado_google
              )
              credenciales_drive = credentials_from_encrypted_token(
                  configuracion_drive_oauth, permiso_cifrado
              )
              # Antes de guardar el permiso se comprueba Drive y se crea la
              # carpeta propia de SAFARA. Un permiso incompleto nunca queda activo.
              preparacion_drive = GoogleSafaraStorage(
                  GoogleStorageConfig.from_secrets(st.secrets),
                  drive_credentials=credenciales_drive,
              )
              carpeta_id = preparacion_drive.crear_carpeta_justificantes_propietaria()
              almacenamiento_seguro.guardar_autorizacion_google_drive(
                  permiso_cifrado, carpeta_id, usuario_actual
              )
              reiniciar_almacenamiento_drive()
              st.query_params.clear()
              registrar_auditoria("google_drive_autorizado", usuario_actual)
              actualizar_informes_y_copias_en_segundo_plano()
              st.success("Google Drive ha quedado autorizado para guardar justificantes.")
            except (GoogleDriveOAuthOperationError, SupabaseStorageOperationError) as error:
              st.error(str(error))

        try:
          autorizacion_guardada = almacenamiento_seguro.obtener_autorizacion_google_drive()
          drive_autorizado = bool(
              autorizacion_guardada.get("token_cifrado")
              and autorizacion_guardada.get("carpeta_id")
          )
        except SupabaseStorageOperationError:
          drive_autorizado = False
        if drive_autorizado:
          st.success("Drive está autorizado y listo para guardar justificantes.")
        else:
          url_autorizacion = google_drive_authorization_url(
              configuracion_drive_oauth, usuario_actual
          )
          st.markdown(
              f'<a href="{escapar_html(url_autorizacion)}" target="_blank" rel="noopener noreferrer" '
              'style="display:inline-block;background:#c62828;color:#ffffff;padding:10px 16px;'
              'border-radius:8px;font-weight:700;text-decoration:none;">AUTORIZAR GOOGLE DRIVE</a>',
              unsafe_allow_html=True,
          )
          st.caption(
              "Se abrirá una pestaña segura: elige la cuenta propietaria de la carpeta de SAFARA. "
              "Tu sesión de esta pestaña se conservará aunque la autorización falle o se cancele."
          )

        if drive_autorizado:
          reenviados_automaticamente = reintentar_justificantes_pendientes_sin_interrumpir(
              almacenamiento_seguro
          )
          if reenviados_automaticamente:
            actualizar_informes_y_copias_en_segundo_plano()
            st.info(
                f"Se han enviado automáticamente {reenviados_automaticamente} justificante(s) pendiente(s)."
            )
          try:
            justificantes_pendientes = almacenamiento_seguro.listar_justificantes_pendientes()
          except SupabaseStorageOperationError:
            justificantes_pendientes = []
          if justificantes_pendientes:
            st.warning(
                f"Hay {len(justificantes_pendientes)} justificante(s) protegidos pendientes de Drive."
            )
            if st.button("REINTENTAR JUSTIFICANTES PENDIENTES"):
              completados = reintentar_justificantes_pendientes_sin_interrumpir(
                  almacenamiento_seguro
              )
              if completados:
                actualizar_informes_y_copias_en_segundo_plano()
              st.success(f"Justificantes enviados a Drive: {completados}.")
              st.rerun()

    st.markdown("#### Crear código de alta")
    st.caption(
        "Cada código permite una sola alta y no se guarda en texto visible."
    )
    with st.form("form_crear_invitacion", clear_on_submit=True):
      dias_invitacion = st.selectbox(
          "Validez del código", [1, 7, 30], format_func=lambda days: f"{days} día(s)"
      )
      crear_codigo = st.form_submit_button("GENERAR CÓDIGO DE ALTA")
      if crear_codigo:
        codigo_nuevo = crear_invitacion(usuario_actual, dias_invitacion)
        if codigo_nuevo:
          st.session_state.ultimo_codigo_invitacion = codigo_nuevo
          registrar_auditoria("invitacion_creada", usuario_actual, f"{dias_invitacion}d")
        else:
          st.error("No se ha podido guardar el código de alta.")

    codigo_mostrado = st.session_state.get("ultimo_codigo_invitacion")
    if codigo_mostrado:
      st.success("Código creado. Cópialo y compártelo de forma privada.")
      st.code(codigo_mostrado, language=None)
      if st.button("Ocultar código", key="ocultar_codigo_invitacion"):
        st.session_state.ultimo_codigo_invitacion = None
        st.rerun()

    st.markdown("---")
    st.markdown("#### Gestionar personas administradoras")
    personas_normales = [
        nombre for nombre, datos in st.session_state.usuarios_registrados.items()
        if datos.get("rol") == "usuario"
    ]
    if personas_normales:
      with st.form("form_conceder_administracion"):
        futuro_admin = st.selectbox(
            "Persona a autorizar como administradora", personas_normales
        )
        confirmar_permiso = st.checkbox(
            "Confirmo que esta persona debe acceder a Administración."
        )
        conceder_permiso = st.form_submit_button("AUTORIZAR ADMINISTRACIÓN")
        if conceder_permiso:
          if not confirmar_permiso:
            st.warning("Confirma la autorización antes de continuar.")
          else:
            storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
            try:
              actualizado = (
                  storage.actualizar_rol_usuario(futuro_admin, "admin", usuario_actual)
                  if usar_almacenamiento_supabase(storage) else False
              )
            except SupabaseStorageOperationError:
              actualizado = False
            if actualizado:
              st.session_state.usuarios_registrados[futuro_admin]["rol"] = "admin"
              st.success("Permiso concedido. Esa persona debe cerrar sesión y volver a entrar.")
              st.rerun()
            else:
              st.error("No se ha podido conceder el permiso de administración.")
    else:
      st.info("No hay personas usuarias pendientes de autorización.")

    otros_admins = [
        nombre for nombre, datos in st.session_state.usuarios_registrados.items()
        if datos.get("rol") == "admin" and nombre != usuario_actual
    ]
    if otros_admins:
      with st.form("form_retirar_administracion"):
        admin_a_retirar = st.selectbox(
            "Persona a devolver a usuario normal", otros_admins
        )
        confirmar_retirada = st.checkbox(
            "Confirmo la retirada del acceso de Administración."
        )
        retirar_permiso = st.form_submit_button("RETIRAR ADMINISTRACIÓN")
        if retirar_permiso:
          if not confirmar_retirada:
            st.warning("Confirma la retirada antes de continuar.")
          else:
            storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
            try:
              actualizado = (
                  storage.actualizar_rol_usuario(admin_a_retirar, "usuario", usuario_actual)
                  if usar_almacenamiento_supabase(storage) else False
              )
            except SupabaseStorageOperationError:
              actualizado = False
            if actualizado:
              st.session_state.usuarios_registrados[admin_a_retirar]["rol"] = "usuario"
              st.success("Acceso de Administración retirado.")
              st.rerun()
            else:
              st.error("No se ha podido retirar el permiso de administración.")

    st.markdown("---")
    st.markdown("#### Sincronizar informes y copias")
    st.caption("Actualiza la vista de consulta de Google sin ralentizar la entrada del grupo.")
    if st.button("ACTUALIZAR INFORMES AHORA", key="sincronizar_informes_admin"):
      if actualizar_informes_y_copias_en_segundo_plano():
        st.success("Informes y copias actualizados.")
      else:
        st.info("No había cambios pendientes o Google no está disponible ahora mismo.")

    st.markdown("---")
    st.markdown("#### Lanzar Nueva Encuesta de Bolo")
    with st.form("form_crear_bolo_admin"):
      b_tit = st.text_input("Título de la Actuación")
      b_fec = st.date_input("Fecha del Evento", datetime.date.today())
      b_hor = st.text_input("Hora", value="19:00h")
      b_lug = st.text_input("Lugar / Municipio")
      b_est = st.selectbox(
          "Estado Inicial", ["CONFIRMADA", "EVALUACION", "STANDBY"]
      )
      btn_guardar_act = st.form_submit_button("GUARDAR ACTUACIÓN")

      if btn_guardar_act:
        if not (b_tit and b_lug):
          st.error(
              "Por favor, completa el título y el lugar antes de guardar."
          )
        else:
          # Validación de duplicados para evitar múltiples columnas idénticas
          duplicado = any(
              a.get("titulo", "").strip().lower() == b_tit.strip().lower()
              and str(a.get("fecha")) == str(b_fec)
              for a in st.session_state.actuaciones
          )
          if duplicado:
            st.warning("Ya existe una actuación registrada con este mismo título y fecha.")
          else:
            storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
            if usar_almacenamiento_supabase(storage):
              try:
                nueva_actuacion = storage.crear_actuacion({
                    "titulo": b_tit, "fecha": b_fec, "hora": b_hor,
                    "lugar": b_lug, "estado": b_est,
                }, usuario_actual)
              except SupabaseStorageOperationError:
                nueva_actuacion = None
              if nueva_actuacion is None:
                st.error("No se ha podido guardar la actuación.")
              else:
                st.session_state.actuaciones.append(nueva_actuacion)
                st.success("🎉 ¡Bolo creado y guardado con seguridad!")
                registrar_auditoria("actuacion_creada", usuario_actual, b_tit)
                st.rerun()
            else:
              sincronizacion_activa = sincronizacion_google_habilitada()
              sheet_col_asignado = (
                  sincronizar_bolo_en_sheets(b_tit, b_fec, b_hor, b_lug, b_est)
                  if sincronizacion_activa else None
              )
              nuevo_id_act = max([a["id"] for a in st.session_state.actuaciones], default=0) + 1
              if not sincronizacion_activa:
                sheet_col_asignado = nuevo_id_act + 2
              if sheet_col_asignado is not None:
                st.session_state.actuaciones.append({
                    "id": nuevo_id_act, "titulo": b_tit, "fecha": b_fec, "hora": b_hor,
                    "lugar": b_lug, "estado": b_est, "sheet_col": sheet_col_asignado,
                })
                if guardar_actuaciones_excel():
                  mensaje = (
                      "🎉 ¡Bolo procesado y creado con éxito (sincronizado en Google Sheets)!"
                      if sincronizacion_activa
                      else "🎉 ¡Bolo creado y guardado localmente!"
                  )
                  st.success(mensaje)
                  registrar_auditoria("actuacion_creada", usuario_actual, b_tit)
                  st.rerun()
                else:
                  st.error("No se ha podido guardar la actuación.")
              else:
                st.error("No se pudo sincronizar con Google Sheets. Comprueba la conexión y credenciales.")

    st.markdown("---")

    # GESTIÓN Y OPCIÓN DUAL: ANULAR O ELIMINAR ACTUACIONES
    st.markdown("#### Gestionar / Anular / Eliminar Actuaciones")
    if st.session_state.actuaciones:
      opciones_bolos = {
          f"#{a['id']} - {a['titulo']} ({a['fecha']}) [{a.get('estado', 'CONFIRMADA')}]": (
              a["id"]
          )
          for a in st.session_state.actuaciones
      }
      bolo_sel_key = st.selectbox(
          "Selecciona la actuación sobre la que deseas actuar:",
          list(opciones_bolos.keys()),
      )
      id_sel = opciones_bolos[bolo_sel_key]

      col_a1, col_a2 = st.columns(2)
      with col_a1:
        if st.button("🚫 Marcar como ANULADA"):
          storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
          if usar_almacenamiento_supabase(storage):
            try:
              actualizado = storage.cambiar_estado_actuacion(id_sel, "ANULADA")
            except SupabaseStorageOperationError:
              actualizado = False
            if not actualizado:
              st.error("No se ha podido actualizar la actuación.")
              st.stop()
          sheet_col_target = None
          for a in st.session_state.actuaciones:
            if a["id"] == id_sel:
              a["estado"] = "ANULADA"
              sheet_col_target = a.get("sheet_col")
              break
          guardar_actuaciones_excel()
          cambiar_estado_bolo_en_sheets(sheet_col_target, "ANULADA")
          st.success(
              "Actuación marcada como ANULADA (registrada en Drive sin"
              " borrar)."
          )
          st.rerun()

      with col_a2:
        if st.button("🗑️ Eliminar Definitivamente"):
          storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
          if usar_almacenamiento_supabase(storage):
            try:
              eliminado = storage.eliminar_actuacion(id_sel)
            except SupabaseStorageOperationError:
              eliminado = False
            if not eliminado:
              st.error("No se ha podido eliminar la actuación.")
              st.stop()
          sheet_col_target = None
          for a in st.session_state.actuaciones:
            if a["id"] == id_sel:
              sheet_col_target = a.get("sheet_col")
              break
          st.session_state.actuaciones = [
              a for a in st.session_state.actuaciones if a["id"] != id_sel
          ]
          guardar_actuaciones_excel()
          eliminar_bolo_en_sheets(sheet_col_target)
          st.success("Actuación eliminada totalmente del sistema y de Drive.")
          st.rerun()
    else:
      st.info("No hay actuaciones actualmente registradas.")

    st.markdown("---")

    # --- GESTIÓN DE SALDO DE CAJA & FINANZAS ---
    st.markdown("#### Ajustar Saldo de Caja & Finanzas")
    with st.form("form_ajuste_saldo"):
      nuevo_saldo_input = st.number_input(
          "Nuevo Saldo Total en Caja (€)",
          min_value=0.0,
          value=float(st.session_state.saldo_caja),
          step=10.0,
          format="%.2f",
      )
      btn_actualizar_saldo = st.form_submit_button("ACTUALIZAR SALDO")
      if btn_actualizar_saldo:
        saldo_anterior = st.session_state.saldo_caja
        st.session_state.saldo_caja = float(nuevo_saldo_input)
        if guardar_saldo_persistente(usuario_actual):
          registrar_auditoria("saldo_actualizado", usuario_actual)
          st.success("¡Importe actualizado con éxito!")
          st.rerun()
        else:
          st.session_state.saldo_caja = saldo_anterior
          st.error("No se ha podido guardar el saldo.")

    st.markdown("---")

    # --- SUGERENCIAS SAFARERS ---
    st.markdown("#### Sugerencias Safarers desde el Confesionario")
    if st.session_state.confesionario_mensajes:
      for idx, m_conf in enumerate(
          reversed(st.session_state.confesionario_mensajes), 1
      ):
        st.markdown(
            f"""
                <div style="background: #12141a; border-left: 4px solid #E74C3C; border: 1px solid #2a2a2a; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #E74C3C; font-weight: 700; margin-bottom: 4px;">
                        <span>👤 {escapar_html(m_conf.get('usuario', 'Anónimo'))}</span>
                        <span>📅 {escapar_html(m_conf.get('fecha', ''))}</span>
                    </div>
                    <div style="color: #FFFFFF; font-size: 13px; line-height: 1.4;">
                        "{escapar_html(m_conf.get('mensaje', ''))}"
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
    else:
      st.info("No hay sugerencias registradas en el confesionario por ahora.")

    st.markdown("---")

    st.markdown("#### Listado Oficial de Socios Registrados")
    if st.session_state.usuarios_registrados:
      df_regs = pd.DataFrame.from_dict(
          st.session_state.usuarios_registrados, orient="index"
      ).drop(columns=["password_salt", "password_hash"], errors="ignore")
      st.dataframe(df_regs, use_container_width=True)

      csv_u = df_regs.reset_index().to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Descargar Registro de Socios (CSV)",
          data=csv_u,
          file_name=f"SAFARA_SOCIOS_{datetime.date.today()}.csv",
          mime="text/csv",
      )

      st.markdown("---")
      st.markdown("#### Depurar / Eliminar Usuarios Duplicados")
      socios_lista = list(st.session_state.usuarios_registrados.keys())
      socio_a_borrar = st.selectbox(
          "Selecciona el usuario que quieras eliminar:", socios_lista
      )

      if st.button("Eliminar Socio Seleccionado"):
        es_ultimo_admin = (
            st.session_state.usuarios_registrados[socio_a_borrar].get("rol")
            == "admin"
            and sum(
                user.get("rol") == "admin"
                for user in st.session_state.usuarios_registrados.values()
            ) == 1
        )
        if es_ultimo_admin:
          st.error("No se puede eliminar a la última persona administradora.")
        else:
          usuario_eliminado = st.session_state.usuarios_registrados.pop(
              socio_a_borrar
          )
          storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
          if usar_almacenamiento_supabase(storage):
            try:
              usuario_guardado = storage.desactivar_usuario(socio_a_borrar)
            except SupabaseStorageOperationError:
              usuario_guardado = False
          else:
            usuario_guardado = guardar_usuarios_excel()
          if usuario_guardado:
            st.success(f"Usuario '{socio_a_borrar}' eliminado correctamente.")
            st.rerun()
          else:
            st.session_state.usuarios_registrados[socio_a_borrar] = usuario_eliminado
            st.error("No se ha podido guardar el cambio.")
    else:
      st.info("No hay socios registrados en el sistema.")

    st.markdown("---")
    st.markdown("#### Confirmar Reembolso a Colaboradores")
    pendientes_df = (
        st.session_state.gastos[
            st.session_state.gastos["Reembolsado"] == "PENDIENTE ABONO"
        ]
        if not st.session_state.gastos.empty
        else pd.DataFrame()
    )

    if pendientes_df.empty:
      st.info("No hay gastos pendientes de abono.")
    else:
      for idx, prow in pendientes_df.iterrows():
        col_ab1, col_ab2 = st.columns([3, 1])
        with col_ab1:
          st.write(
              f"**#{prow['ID']} - {prow['Usuario']}**:"
              f" {formato_espanol(prow['Importe'])} € ({prow['Concepto']})"
          )
        with col_ab2:
          if st.button("Marcar ABONADO", key=f"abonar_{prow['ID']}"):
            estado_anterior = st.session_state.gastos.loc[
                st.session_state.gastos["ID"] == prow["ID"], "Reembolsado"
            ].copy()
            st.session_state.gastos.loc[
                st.session_state.gastos["ID"] == prow["ID"], "Reembolsado"
            ] = "ABONADO"
            storage = obtener_almacenamiento_google() if usar_almacenamiento_google() else None
            if usar_almacenamiento_supabase(storage):
              try:
                gasto_guardado = storage.marcar_gasto_abonado(int(prow["ID"]), usuario_actual)
              except SupabaseStorageOperationError:
                gasto_guardado = False
            else:
              gasto_guardado = guardar_gastos_persistentes()
            if gasto_guardado:
              registrar_auditoria("gasto_abonado", usuario_actual, str(prow["ID"]))
              actualizar_informes_y_copias_en_segundo_plano()
              st.success(f"Gasto #{prow['ID']} marcado como ABONADO")
              st.rerun()
            else:
              st.session_state.gastos.loc[
                  st.session_state.gastos["ID"] == prow["ID"], "Reembolsado"
              ] = estado_anterior
              st.error("No se ha podido actualizar el reembolso.")

    st.divider()

    with st.expander(
        "Generar Paquete de Auditoría (ZIP + Excel)", expanded=False
    ):
      if st.button("Generar Paquete ZIP"):
        if st.session_state.gastos.empty:
          st.warning("No hay datos para exportar.")
        else:
          zip_buffer = io.BytesIO()
          with zipfile.ZipFile(
              zip_buffer, "w", zipfile.ZIP_DEFLATED
          ) as zip_file:
            excel_buffer = io.BytesIO()
            st.session_state.gastos.to_excel(excel_buffer, index=False)
            zip_file.writestr(
                "Libro_Registro_Safara_Percussion.xlsx",
                excel_buffer.getvalue(),
            )

            for _, row in st.session_state.gastos.iterrows():
              fich = row.get("Fichero")
              if fich and isinstance(fich, str) and str(fich) != "nan":
                path_fich = os.path.join(RECEIPTS_DIR, fich)
                if os.path.exists(path_fich):
                  clean_concept = re.sub(r"[^a-zA-Z0-9]", "_", row["Concepto"])[
                      :30
                  ]
                  ext = fich.split(".")[-1]
                  zip_name = (
                      f"Justificantes/ID_{row['ID']}_{row['Fecha']}_{clean_concept}_{row['Importe']}EUR.{ext}"
                  )
                  zip_file.write(path_fich, zip_name)

          zip_buffer.seek(0)
          st.success("Paquete generado con éxito")
          st.download_button(
              label="Descargar ZIP Certificado",
              data=zip_buffer.getvalue(),
              file_name=f"Auditoria_Safara_Percussion_{datetime.date.today()}.zip",
              mime="application/zip",
          )

st.divider()

logo_delante_file = buscar_logo_delante()
if logo_delante_file:
  html_pie = render_logo_png(logo_delante_file, width=170)
  if html_pie:
    st.markdown(html_pie, unsafe_allow_html=True)

st.markdown(
    '<div class="somos-fuego-footer">SOMOS FUEGO</div>', unsafe_allow_html=True
)

