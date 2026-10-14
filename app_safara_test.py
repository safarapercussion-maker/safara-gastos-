import base64
import datetime
import io
import os
import random
import re
import urllib.parse
import zipfile

try:
  from zoneinfo import ZoneInfo
except ImportError:
  from backports.zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

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
    "Baragazte (Barañain)": "https://maps.app.goo.gl/LyDLFNRPgj9WhfQk7?g_st=ic",
    "Gaztetxe de Zizur": "https://maps.app.goo.gl/PxZBzzqGTVf3qR5f6?g_st=ic",
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


def render_logo_png(filename, width=210):
  if filename and os.path.exists(filename):
    try:
      with open(filename, "rb") as f:
        data = f.read()
      encoded = base64.b64encode(data).decode()
      ext = filename.split(".")[-1].lower()
      mime = "image/png" if ext == "png" else "image/jpeg"
      return f"""
                <div class="sparta-logo-container">
                    <div class="sparta-circle-logo">
                        <img src="data:{mime};base64,{encoded}" width="{width}" />
                    </div>
                </div>
            """
    except:
      return None
  return None


def render_logo_inline_b64(filename):
  if filename and os.path.exists(filename):
    try:
      with open(filename, "rb") as f:
        data = f.read()
      encoded = base64.b64encode(data).decode()
      ext = filename.split(".")[-1].lower()
      mime = "image/png" if ext == "png" else "image/jpeg"
      return f"data:{mime};base64,{encoded}"
    except:
      return None
  return None


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

bg_b64 = ""
if os.path.exists("IMG_0753.jpeg"):
  with open("IMG_0753.jpeg", "rb") as f:
    bg_b64 = base64.b64encode(f.read()).decode()

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
EXCEL_USUARIOS = "usuarios_safara.xlsx"
VOTOS_PERSIST_FILE = "votos_safara_historial.xlsx"
CONFESIONARIO_FILE = "confesionario_safara.xlsx"
ACTUACIONES_FILE = "actuaciones_safara.xlsx"

FECHA_FUNDACION = datetime.date(2023, 4, 23)

hoy_m = datetime.datetime.now(ZoneInfo("Europe/Madrid")).date()
semana_num = hoy_m.isocalendar()[1]
ubicacion_rotativa = (
    "Baragazte (Barañain)" if semana_num % 2 == 0 else "Gaztetxe de Zizur"
)

ciclo_actual = obtener_ciclo_semanal_actual()

# --- INICIALIZACIÓN DE VOTOS ---
if "votos_historial" not in st.session_state:
  if os.path.exists(VOTOS_PERSIST_FILE):
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
  try:
    st.session_state.votos_historial.to_excel(VOTOS_PERSIST_FILE, index=False)
  except Exception:
    pass


def registrar_voto_backend(encuesta_id, usuario_id, respuesta):
  global ciclo_actual
  ahora_str = datetime.datetime.now(ZoneInfo("Europe/Madrid")).strftime(
      "%Y-%m-%d %H:%M:%S"
  )
  df = st.session_state.votos_historial

  ciclo_target = (
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_") else ciclo_actual
  )

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

  guardar_votos_persistentes()


def obtener_voto_usuario(encuesta_id, usuario_id):
  global ciclo_actual
  ciclo_target = (
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_") else ciclo_actual
  )
  df = st.session_state.votos_historial
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
      "BOLO_PERMANENTE" if str(encuesta_id).startswith("bolo_") else ciclo_actual
  )
  df = st.session_state.votos_historial
  if df.empty:
    return pd.DataFrame()
  return df[
      (df["encuesta_id"] == str(encuesta_id))
      & (df["ciclo_id"] == str(ciclo_target))
  ]


# --- PERSISTENCIA DE ACTUACIONES / BOLOS ---
def guardar_actuaciones_excel():
  try:
    df_act = pd.DataFrame(st.session_state.actuaciones)
    if "fecha" in df_act.columns:
      df_act["fecha"] = df_act["fecha"].apply(
          lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x)
      )
    df_act.to_excel(ACTUACIONES_FILE, index=False)
  except Exception:
    pass


if "actuaciones" not in st.session_state:
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
      st.session_state.actuaciones = list_acts
    except:
      st.session_state.actuaciones = []
  else:
    # Carga automática desde tu Google Sheet de Actuaciones
        try:
            ACTUATIONS_GSHEET_URL = "https://docs.google.com/spreadsheets/d/16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM/export?format=csv&gid=2025182751"
            df_act = pd.read_csv(ACTUATIONS_GSHEET_URL)
            list_acts = []
            for index, row in df_act.iterrows():
                f_val = row.get("fecha", datetime.date.today())
                if isinstance(f_val, str):
                    try:
                        f_val = datetime.date.fromisoformat(f_val.strip())
                    except:
                        f_val = datetime.date.today()
                
                list_acts.append({
                    "id": int(row.get("id", index + 1)),
                    "titulo": str(row.get("titulo", "Actuación Safara")),
                    "fecha": f_val,
                    "hora": str(row.get("hora", "19:00h")),
                    "lugar": str(row.get("lugar", "Pamplona")),
                    "estado": str(row.get("estado", "CONFIRMADA"))
                })
            st.session_state.actuaciones = list_acts
        except Exception:
            st.session_state.actuaciones = []

# --- CONFESIONARIO PERSISTENTE ---
if "confesionario_mensajes" not in st.session_state:
  if os.path.exists(CONFESIONARIO_FILE):
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
    df_conf.to_excel(CONFESIONARIO_FILE, index=False)
  except Exception:
    pass


if "proximo_ensayo" not in st.session_state:
  st.session_state.proximo_ensayo = {
      "id": "ensayo_proximo",
      "fecha": hoy_m + datetime.timedelta(days=(4 - hoy_m.weekday()) % 7),
      "hora": "19:00h - 19:30h",
      "ubicacion_nombre": ubicacion_rotativa,
      "url_maps": UBICACIONES_ENSAYO[ubicacion_rotativa],
  }

if "gastos" not in st.session_state:
  if os.path.exists(EXCEL_FILE):
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

if "saldo_caja" not in st.session_state:
  if os.path.exists(SALDO_FILE):
    try:
      with open(SALDO_FILE, "r") as f:
        st.session_state.saldo_caja = float(f.read().strip())
    except:
      st.session_state.saldo_caja = 1250.50
  else:
    st.session_state.saldo_caja = 1250.50

if "admins" not in st.session_state:
  st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego", "Admin"]

if "usuarios_registrados" not in st.session_state:
  if os.path.exists(EXCEL_USUARIOS):
    try:
      df_u = pd.read_excel(EXCEL_USUARIOS)
      st.session_state.usuarios_registrados = df_u.set_index(
          "Nombre"
      ).to_dict(orient="index")
    except:
      st.session_state.usuarios_registrados = {
          "Admin": {
              "pin": "1234",
              "email": "admin@safarapercussion.com",
              "tel": "600000000",
              "fnac": "01/01/1990",
              "instrumento": "Surdo",
              "rgpd": True,
          },
          "Diego": {
              "pin": "1234",
              "email": "85diegoalvarez@gmail.com",
              "tel": "650184254",
              "fnac": "15/06/1998",
              "instrumento": "Surdo de contra",
              "rgpd": True,
          },
      }
  else:
    st.session_state.usuarios_registrados = {
        "Admin": {
            "pin": "1234",
            "email": "admin@safarapercussion.com",
            "tel": "600000000",
            "fnac": "01/01/1990",
            "instrumento": "Surdo",
            "rgpd": True,
        },
        "Diego": {
            "pin": "1234",
            "email": "85diegoalvarez@gmail.com",
            "tel": "650184254",
            "fnac": "15/06/1998",
            "instrumento": "Surdo de contra",
            "rgpd": True,
        },
    }


def guardar_usuarios_excel():
  df_u = pd.DataFrame.from_dict(
      st.session_state.usuarios_registrados, orient="index"
  ).reset_index()
  df_u.rename(columns={"index": "Nombre"}, inplace=True)
  df_u.to_excel(EXCEL_USUARIOS, index=False)


# ==============================================================================
# --- ACCIONES DE VOTO VÍA URL (CLIC DIRECTO EN LOGOS) -------------------------
# ==============================================================================
params = st.query_params
user_param = params.get("user")

if "action" in params:
  act = params.get("action")
  u_voter = params.get("voter")
  if act and u_voter:
    if act == "v_ens_si":
      registrar_voto_backend("ensayo_proximo", u_voter, "SI")
    elif act == "v_ens_no":
      registrar_voto_backend("ensayo_proximo", u_voter, "NO")
    elif act == "v_cena_si":
      registrar_voto_backend("cena_proxima", u_voter, "SI")
    elif act == "v_cena_no":
      registrar_voto_backend("cena_proxima", u_voter, "NO")
    elif act.startswith("v_bolo_si_"):
      b_id = act.replace("v_bolo_si_", "")
      registrar_voto_backend(f"bolo_{b_id}", u_voter, "SI")
    elif act.startswith("v_bolo_no_"):
      b_id = act.replace("v_bolo_no_", "")
      registrar_voto_backend(f"bolo_{b_id}", u_voter, "NO")

  st.query_params.clear()
  if user_param:
    st.query_params["user"] = user_param

if "usuario_autenticado" not in st.session_state:
  st.session_state.usuario_autenticado = None

if "ultimo_acceso" not in st.session_state:
  st.session_state.ultimo_acceso = datetime.datetime.now()

if user_param and user_param in st.session_state.usuarios_registrados:
  if not st.session_state.usuario_autenticado:
    st.session_state.usuario_autenticado = user_param

if st.session_state.usuario_autenticado:
  ahora = datetime.datetime.now()
  tiempo_inactivo = ahora - st.session_state.ultimo_acceso
  if tiempo_inactivo > datetime.timedelta(minutes=30):
    st.session_state.usuario_autenticado = None
    st.query_params.clear()
  else:
    st.session_state.ultimo_acceso = ahora
    st.query_params["user"] = st.session_state.usuario_autenticado

if "ultimo_whatsapp_url" not in st.session_state:
  st.session_state.ultimo_whatsapp_url = None

if "mostrar_recuperacion" not in st.session_state:
  st.session_state.mostrar_recuperacion = False

if "admin_autenticado" not in st.session_state:
  st.session_state.admin_autenticado = False

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

    nombres_disponibles = ["Selecciona tu usuario..."] + list(
        st.session_state.usuarios_registrados.keys()
    )
    nombre_login = st.selectbox("Safarer", nombres_disponibles)
    pin_login = st.text_input(
        "PIN de Acceso", type="password", placeholder="Introduce tu PIN"
    )

    if st.button("¡VAAAMONOSSS!"):
      if nombre_login == "Selecciona tu usuario...":
        st.error("Por favor, selecciona tu nombre.")
      elif not pin_login:
        st.error("Por favor, introduce tu PIN.")
      else:
        user_info = st.session_state.usuarios_registrados.get(nombre_login)
        if user_info and str(user_info.get("pin")).strip() == pin_login.strip():
          st.session_state.usuario_autenticado = nombre_login
          st.session_state.ultimo_acceso = datetime.datetime.now()
          st.query_params["user"] = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        elif nombre_login in st.session_state.admins and pin_login.strip() in [
            "1234",
            "2026",
        ]:
          st.session_state.usuario_autenticado = nombre_login
          st.session_state.ultimo_acceso = datetime.datetime.now()
          st.query_params["user"] = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        else:
          st.error("PIN incorrecto.")

    if not st.session_state.mostrar_recuperacion:
      if st.button(
          "¡Vaya memoria la tuya! ¿Has olvidado la contraseña?",
          key="btn_recuperar_toggle",
      ):
        st.session_state.mostrar_recuperacion = True
        st.rerun()

    if st.session_state.mostrar_recuperacion:
      st.markdown(
          "<p style='color:#E74C3C; font-size:0.8rem; font-weight:700;"
          " margin-top:10px; text-align:center;'>Recuperación de PIN vía"
          " WhatsApp:</p>",
          unsafe_allow_html=True,
      )
      tel_recup = st.text_input(
          "Teléfono móvil registrado", placeholder="600000000"
      )
      col_r1, col_r2 = st.columns(2)
      with col_r1:
        if st.button("Enviar WhatsApp"):
          if nombre_login == "Selecciona tu usuario...":
            st.warning("Selecciona tu usuario arriba.")
          elif not tel_recup:
            st.warning("Introduce tu teléfono.")
          else:
            u_data = st.session_state.usuarios_registrados.get(
                nombre_login, {"pin": "1234"}
            )
            pin_rec = u_data.get("pin", "1234")
            msg_wa = f"Hola {nombre_login}, tu PIN de acceso para Safara Percussion es: {pin_rec}."
            url_wa = f"https://wa.me/34{tel_recup.strip()}?text={urllib.parse.quote(msg_wa)}"
            st.markdown(
                f"""
                                <div style="margin-top: 5px; text-align: center;">
                                    <a href="{url_wa}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 6px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 800; text-decoration: none; display: inline-block;">
                                        Abrir WhatsApp 📱
                                    </a>
                                </div>
                            """,
                unsafe_allow_html=True,
            )
      with col_r2:
        if st.button("Cerrar"):
          st.session_state.mostrar_recuperacion = False
          st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

  with tab_registro:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("form_registro_completo"):
      reg_nombre = st.text_input("Nombre y Apellidos *")
      reg_email = st.text_input("Correo Electrónico *")
      reg_tel = st.text_input("Teléfono Móvil (para recibir PIN) *")

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

      btn_reg_submit = st.form_submit_button("SOLICITAR ALTA Y GENERAR PIN")

      if btn_reg_submit:
        if not (reg_nombre and reg_email and reg_tel):
          st.error("Por favor, completa todos los campos obligatorios.")
        elif not reg_acepta_rgpd:
          st.warning(
              "Debes aceptar la casilla de Protección de Datos e Imagen."
          )
        elif reg_nombre in st.session_state.usuarios_registrados:
          st.error("Este nombre ya está registrado en el sistema.")
        else:
          pin_generado = f"{random.randint(1000, 9999)}"
          fecha_nac_str = f"{reg_dia:02d}/{reg_mes:02d}/{reg_anio}"

          st.session_state.usuarios_registrados[reg_nombre] = {
              "pin": pin_generado,
              "email": reg_email,
              "tel": reg_tel,
              "fnac": fecha_nac_str,
              "instrumento": reg_instrumento,
              "rgpd": True,
          }
          guardar_usuarios_excel()

          st.success(
              f"¡Alta tramitada! Tu PIN personal es: **{pin_generado}**"
          )

          texto_w_pin = f"Hola {reg_nombre}, tu PIN de acceso para la app de Safara Percussion es: {pin_generado}."
          url_wa_pin = f"https://wa.me/34{reg_tel}?text={urllib.parse.quote(texto_w_pin)}"

          st.markdown(
              f"""
                        <div style="margin-top: 15px; text-align: center;">
                            <a href="{url_wa_pin}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 10px 18px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block;">
                                Enviar PIN por WhatsApp 📱
                            </a>
                        </div>
                    """,
              unsafe_allow_html=True,
          )
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
        <div class="ticker-text">{txt_ticker}</div>
    </div>
""",
    unsafe_allow_html=True,
)

col_head_left, col_head_right = st.columns([3, 1])
with col_head_right:
  st.markdown('<div class="btn-logout-discreto">', unsafe_allow_html=True)
  if st.button("⏻ ¡Me pirooooo!", key="btn_logout_piro"):
    st.session_state.usuario_autenticado = None
    st.session_state.ultimo_whatsapp_url = None
    st.session_state.mostrar_recuperacion = False
    st.query_params.clear()
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
                <h3 style="margin: 0; font-size: 18px; color: #FFFFFF;">¡Hola, {usuario_actual}!</h3>
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

  ensayo_info = st.session_state.proximo_ensayo
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

  ensayo_confirmado = num_confirmados >= 6
  badge_estado_ens = (
      "🟢 CONFIRMADO" if ensayo_confirmado else "🟡 PENDIENTE DE QUORUM"
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

  voto_ens_actual = obtener_voto_usuario("ensayo_proximo", usuario_actual)
  img_si_cls = (
      "poll-img-green-sel"
      if voto_ens_actual == "SI"
      else "poll-img-green-norm"
  )
  img_no_cls = (
      "poll-img-red-sel" if voto_ens_actual == "NO" else "poll-img-red-norm"
  )

  url_voto_si = f"?user={usuario_actual}&action=v_ens_si&voter={usuario_actual}"
  url_voto_no = f"?user={usuario_actual}&action=v_ens_no&voter={usuario_actual}"

  st.markdown(
      f"""
        <div class="safara-poll-row">
            <div class="safara-poll-col">
                <a href="{url_voto_si}" target="_self" style="text-decoration:none;">
                    <img src="{logo_b64_inline}" class="poll-img-btn {img_si_cls}" />
                </a>
                <div class="poll-label-green">A tope, se le da</div>
            </div>
            <div class="safara-poll-col">
                <a href="{url_voto_no}" target="_self" style="text-decoration:none;">
                    <img src="{logo_b64_inline}" class="poll-img-btn {img_no_cls}" />
                </a>
                <div class="poll-label-red">No puedo, tengo lío</div>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      f"<p style='text-align: center; font-size: 14px; font-weight: 800;"
      f" color: #E74C3C; margin-top: 12px;'>{num_confirmados} Safarers han"
      " confirmado para este viernes</p>",
      unsafe_allow_html=True,
  )

  if confirmados_list:
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
      else:
        counts["Repenike"] += 1

    st.caption(
        f"Repenikes: {counts['Repenike']} | Cajas: {counts['Caja']} |"
        f" Surdos: {counts['Surdo']} | Surdos de contra:"
        f" {counts['Surdo de contra']} | Bailarinas:"
        f" {counts['Ganza (bailarinas)']}"
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

  url_c_si = f"?user={usuario_actual}&action=v_cena_si&voter={usuario_actual}"
  url_c_no = f"?user={usuario_actual}&action=v_cena_no&voter={usuario_actual}"

  st.markdown(
      f"""
        <div class="safara-poll-row">
            <div class="safara-poll-col">
                <a href="{url_c_si}" target="_self" style="text-decoration:none;">
                    <img src="{logo_b64_inline}" class="poll-img-btn {c_img_si_cls}" />
                </a>
                <div class="poll-label-green">A tope, se le da</div>
            </div>
            <div class="safara-poll-col">
                <a href="{url_c_no}" target="_self" style="text-decoration:none;">
                    <img src="{logo_b64_inline}" class="poll-img-btn {c_img_no_cls}" />
                </a>
                <div class="poll-label-red">No puedo, tengo lío</div>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

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
        st.session_state.confesionario_mensajes.append(nuevo_msg)
        guardar_confesionario_excel()
        st.success("¡Mensaje guardado con éxito en el confesionario!")
      else:
        st.error("Por favor, escribe un mensaje antes de enviar.")

# ==============================================================================
# --- PESTAÑA 2: AGENDA & BOLOS (SISTEMA INTEGRADO DE ENCUESTAS + QUÓRUM) -----
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
      if ev.get("estado") == "CONFIRMADA" or quorum_alcanzado:
        estado_badge = "🟢 CONFIRMADA (¡QUÓRUM ALCANZADO!)"
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

      st.markdown(
          f"""
            <div style="background: #12141a; border: {border_card}; border-radius: 16px; padding: 18px; margin-bottom: 12px;">
                <span style="background: {color_badge}; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800;">{estado_badge}</span>
                <h3 style="color: #FFFFFF; margin: 8px 0 4px 0; font-size: 18px;">{ev['titulo']}</h3>
                <p style="font-size: 14px; margin: 4px 0; color: #DDD;">📅 <b>Fecha:</b> {f_ev_str} ({ev['hora']})</p>
                <p style="font-size: 14px; margin: 4px 0; color: #DDD;">📍 <b>Lugar:</b> {ev['lugar']}</p>
            </div>
        """,
          unsafe_allow_html=True,
      )

      voto_bolo_actual = obtener_voto_usuario(encuesta_key, usuario_actual)
      cls_b_si = (
          "poll-img-green-sel"
          if voto_bolo_actual == "SI"
          else "poll-img-green-norm"
      )
      cls_b_no = (
          "poll-img-red-sel" if voto_bolo_actual == "NO" else "poll-img-red-norm"
      )

      url_b_si = f"?user={usuario_actual}&action=v_bolo_si_{bolo_id}&voter={usuario_actual}"
      url_b_no = f"?user={usuario_actual}&action=v_bolo_no_{bolo_id}&voter={usuario_actual}"

      st.markdown(
          f"""
            <div class="safara-poll-row">
                <div class="safara-poll-col">
                    <a href="{url_b_si}" target="_self" style="text-decoration:none;">
                        <img src="{logo_b64_inline}" class="poll-img-btn {cls_b_si}" />
                    </a>
                    <div class="poll-label-green">A tope, se le da</div>
                </div>
                <div class="safara-poll-col">
                    <a href="{url_b_no}" target="_self" style="text-decoration:none;">
                        <img src="{logo_b64_inline}" class="poll-img-btn {cls_b_no}" />
                    </a>
                    <div class="poll-label-red">No puedo, tengo lío</div>
                </div>
            </div>
        """,
          unsafe_allow_html=True,
      )

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
        ext = fichero.name.split(".")[-1].lower()
        id_nuevo = (
            int(st.session_state.gastos["ID"].max() + 1)
            if not st.session_state.gastos.empty
            else 1
        )

        nombre_fichero = (
            f"Gasto_{id_nuevo}_{fecha}_{usuario_actual}_{importe}EUR.{ext}"
        )
        path_destino = os.path.join(RECEIPTS_DIR, nombre_fichero)

        with open(path_destino, "wb") as f:
          f.write(fichero.getbuffer())

        concepto_final = f"{categoria_seleccionada}" + (
            f" - {detalle_concepto}" if detalle_concepto else ""
        )
        enlace_excel = f'=HIPERVINCULO("{path_destino}"; "Ver Ticket")'

        nuevo_reg = {
            "ID": id_nuevo,
            "Fecha": str(fecha),
            "Usuario": usuario_actual,
            "Concepto": concepto_final,
            "Importe": float(importe),
            "Fichero": nombre_fichero,
            "Reembolsado": "PENDIENTE ABONO",
            "Enlace Ticket": enlace_excel,
        }
        st.session_state.gastos = pd.concat(
            [st.session_state.gastos, pd.DataFrame([nuevo_reg])],
            ignore_index=True,
        )
        st.session_state.gastos.to_excel(EXCEL_FILE, index=False)

        st.success("¡Gasto registrado con éxito!")

        texto_w = f"¡Aupa! Hay nuevo gasto registrado en la app: {formato_espanol(importe)} € por {concepto_final}. Ticket adjuntado y listo para revisión y abono."
        st.session_state.ultimo_whatsapp_url = (
            f"https://wa.me/34650184254?text={urllib.parse.quote(texto_w)}"
        )

    if st.session_state.ultimo_whatsapp_url:
      st.markdown(
          f"""
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{st.session_state.ultimo_whatsapp_url}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 12px 20px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                        Avisar por WhatsApp al Tesorero 📱
                    </a>
                </div>
            """,
          unsafe_allow_html=True,
      )
      if st.button("✔ Confirmar Aviso Enviado"):
        st.session_state.ultimo_whatsapp_url = None
        st.rerun()

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
                                <strong style="color: #FFFFFF; font-size: 14px;">{row['Concepto']}</strong>
                                <span style="background: {color_badge}; color: #000; padding: 2px 7px; border-radius: 6px; font-size: 9px; font-weight: 800;">{estado_txt}</span>
                            </div>
                            <div style="margin-top: 6px; font-size: 12px; color: #FFFFFF;">
                                <span>Colaborador:</span> <b>{row['Usuario']}</b> | <span>Fecha:</span> {fecha_visual} | <span style="color: #E74C3C; font-weight: 800;">{formato_espanol(row['Importe'])} €</span>
                            </div>
                        </div>
                    """,
              unsafe_allow_html=True,
          )

          fich = row.get("Fichero")
          if fich and isinstance(fich, str) and str(fich) != "nan":
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
  pin_ingresado = st.text_input(
      "Clave de Administración",
      type="password",
      placeholder="Introduce la contraseña...",
  )
  PIN_SECRETO = "safara2026"

  if pin_ingresado == PIN_SECRETO:
    st.session_state.admin_autenticado = True
  elif pin_ingresado != "":
    st.session_state.admin_autenticado = False
    st.error("Contraseña incorrecta.")

  if st.session_state.admin_autenticado:
    st.success("Acceso de Administración Autorizado")

    st.markdown("#### Lanzar Nueva Encuesta de Bolo")
    with st.form("form_crear_bolo_admin"):
      b_tit = st.text_input("Título de la Actuación")
      b_fec = st.date_input("Fecha del Evento", datetime.date.today())
      b_hor = st.text_input("Hora", value="Tarde")
      b_lug = st.text_input("Lugar / Municipio")
      b_est = st.selectbox(
          "Estado Inicial", ["EVALUACION", "CONFIRMADA", "STANDBY"]
      )
      btn_guardar_act = st.form_submit_button("GUARDAR ACTUACIÓN")

      if btn_guardar_act:
        if not (b_tit and b_lug):
          st.error(
              "Por favor, completa el título y el lugar antes de guardar."
          )
        else:
          nuevo_id_act = (
              max([a["id"] for a in st.session_state.actuaciones], default=0) + 1
          )
          st.session_state.actuaciones.append({
              "id": nuevo_id_act,
              "titulo": b_tit,
              "fecha": b_fec,
              "hora": b_hor,
              "lugar": b_lug,
              "estado": b_est,
          })
          guardar_actuaciones_excel()
          st.success(
              "¡Bolo registrado correctamente! Ya está disponible en la pestaña"
              " Agenda & Bolos para su votación."
          )
          st.rerun()

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
                        <span>👤 {m_conf.get('usuario', 'Anónimo')}</span>
                        <span>📅 {m_conf.get('fecha', '')}</span>
                    </div>
                    <div style="color: #FFFFFF; font-size: 13px; line-height: 1.4;">
                        "{m_conf.get('mensaje', '')}"
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
    else:
      st.info("No hay sugerencias registradas en el confesionario por ahora.")

    st.markdown("---")

    st.markdown("#### Listado Oficial de Socios Registrados y PINs")
    if st.session_state.usuarios_registrados:
      df_regs = pd.DataFrame.from_dict(
          st.session_state.usuarios_registrados, orient="index"
      )
      st.dataframe(df_regs, use_container_width=True)

      csv_u = df_regs.reset_index().to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Descargar Registro de Socios y PINs (Excel/CSV)",
          data=csv_u,
          file_name=f"SAFARA_SOCIOS_PINS_{datetime.date.today()}.csv",
          mime="text/csv",
      )

      st.markdown("---")
      st.markdown("#### Depurar / Eliminar Usuarios Duplicados")
      socios_lista = list(st.session_state.usuarios_registrados.keys())
      socio_a_borrar = st.selectbox(
          "Selecciona el usuario que quieras eliminar:", socios_lista
      )

      if st.button("Eliminar Socio Seleccionado"):
        del st.session_state.usuarios_registrados[socio_a_borrar]
        guardar_usuarios_excel()
        st.success(f"Usuario '{socio_a_borrar}' eliminado correctamente.")
        st.rerun()
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
            st.session_state.gastos.loc[
                st.session_state.gastos["ID"] == prow["ID"], "Reembolsado"
            ] = "ABONADO"
            st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
            st.success(f"Gasto #{prow['ID']} marcado como ABONADO")
            st.rerun()

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
              data=zip_buffer,
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
