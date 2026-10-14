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


# ==============================================================================
# --- CARGA DE ACTUACIONES DESDE GOOGLE SHEETS EN TIEMPO REAL ------------------
# ==============================================================================
ACTUATIONS_GSHEET_URL = "https://docs.google.com/spreadsheets/d/16uviY0tWNPcMKgtnPHA5N5AneW8nquD5A-6Nst-egRM/export?format=csv&gid=2025182751"

if "actuaciones" not in st.session_state:
    try:
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
        st.session_state.actuaciones = [
            {
                "id": 1,
                "titulo": "Halloween Ocasiones Especiales",
                "fecha": datetime.date(2026, 10, 31),
                "hora": "19:00h",
                "lugar": "Pamplona",
                "estado": "CONFIRMADA",
            }
        ]

def guardar_actuaciones_excel():
    # Las actuaciones se actualizan y leen directamente desde Google Sheets
    pass


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
