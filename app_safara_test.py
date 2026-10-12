import base64
import datetime
import io
import os
import random
import re
import urllib.parse
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Safara Percussion - App Oficial (Test)",
    layout="centered",
    initial_sidebar_state="collapsed"
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


# --- FUNCIONES DE APOYO Y FORMATO ---
def obtener_fecha_espanol():
    hoy = datetime.date.today()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
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


# --- ESTILOS CSS SPARTA & RED SAFARA UNIFICADO ---
logo_fuego_file = buscar_logo_fuego()
logo_delante_file = buscar_logo_delante()
logo_b64_inline = render_logo_inline_b64(logo_fuego_file) or ""

bg_b64 = ""
if os.path.exists("IMG_0753.jpeg"):
    with open("IMG_0753.jpeg", "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode()

bg_css_login = (
    f"background: linear-gradient(rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.88)), url('data:image/jpeg;base64,{bg_b64}'); background-size: cover; background-position: center; background-attachment: fixed;"
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

    /* INSIGNIA CENTRAL TRANSPARENTE SPARTA STYLE */
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

    input, textarea {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
        font-weight: 600 !important;
    }}

    /* BOTONES GENERALES DE LA APP */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {{
        background: linear-gradient(135deg, #B01E10 0%, #7A0000 100%);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.7rem;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        border-radius: 6px;
        border: 1px solid rgba(231, 76, 60, 0.4);
        width: 100%;
        min-width: 0px;
        margin: 4px auto;
        padding: 6px 10px;
        box-shadow: 0 2px 8px rgba(176, 30, 16, 0.3);
    }}

    /* --- ESTILOS EXCLUSIVOS PARA LOS BOTONES DE ENCUESTA (LOGO PURO) --- */
    .btn-logo-poll > button {{
        background-color: transparent !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
        border: none !important;
        box-shadow: none !important;
        width: 100px !important;
        height: 100px !important;
        min-height: 100px !important;
        margin: 0 auto !important;
        display: block !important;
        color: transparent !important;
        cursor: pointer !important;
        transition: transform 0.2s ease, filter 0.2s ease !important;
    }}

    .btn-logo-poll > button:hover {{
        transform: scale(1.1) !important;
    }}

    /* VARIACIONES DE COLOR Y RESPLANDOR (SÍ / NO / SELECCIONADO) */
    .btn-green-normal > button {{
        background-image: url('{logo_b64_inline}') !important;
        filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(118deg) brightness(119%) contrast(119%) drop-shadow(0 0 6px rgba(46, 204, 113, 0.6)) !important;
        opacity: 0.85 !important;
    }}

    .btn-green-selected > button {{
        background-image: url('{logo_b64_inline}') !important;
        filter: brightness(0) saturate(100%) invert(48%) sepia(79%) saturate(2476%) hue-rotate(118deg) brightness(119%) contrast(119%) drop-shadow(0 0 18px #2ECC71) drop-shadow(0 0 30px #2ECC71) !important;
        transform: scale(1.12) !important;
        opacity: 1 !important;
    }}

    .btn-red-normal > button {{
        background-image: url('{logo_b64_inline}') !important;
        filter: drop-shadow(0 0 6px rgba(231, 76, 60, 0.6)) brightness(1.1) !important;
        opacity: 0.85 !important;
    }}

    .btn-red-selected > button {{
        background-image: url('{logo_b64_inline}') !important;
        filter: drop-shadow(0 0 18px #E74C3C) drop-shadow(0 0 30px #E74C3C) brightness(1.3) !important;
        transform: scale(1.12) !important;
        opacity: 1 !important;
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

# --- DIRECTORIOS Y ARCHIVOS DE DATOS ---
RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"
SALDO_FILE = "saldo_caja.txt"
EXCEL_USUARIOS = "usuarios_safara.xlsx"

hoy_m = datetime.date.today()
semana_num = hoy_m.isocalendar()[1]
ubicacion_rotativa = (
    "Baragazte (Barañain)" if semana_num % 2 == 0 else "Gaztetxe de Zizur"
)

# --- INICIALIZACIÓN DE ESTADOS ---
if "proximo_ensayo" not in st.session_state:
    st.session_state.proximo_ensayo = {
        "fecha": hoy_m + datetime.timedelta(days=(4 - hoy_m.weekday()) % 7),
        "hora": "19:00h - 19:30h",
        "ubicacion_nombre": ubicacion_rotativa,
        "url_maps": UBICACIONES_ENSAYO[ubicacion_rotativa],
        "asistencia": {},
        "votos_cena": {},
    }

if "confesionario_mensajes" not in st.session_state:
    st.session_state.confesionario_mensajes = []

if "actuaciones" not in st.session_state:
    st.session_state.actuaciones = [
        {
            "id": 1,
            "titulo": "Halloween Ocasiones Especiales",
            "fecha": datetime.date(2026, 10, 31),
            "hora": "19:00h",
            "lugar": "Pamplona",
            "estado": "CONFIRMADA",
            "limite_votacion": None,
            "votos": {},
        },
        {
            "id": 2,
            "titulo": "Boda Amaia (Iruña Park)",
            "fecha": datetime.date(2026, 11, 7),
            "hora": "19:00h - 20:00h",
            "lugar": "Iruña Park, Pamplona",
            "estado": "CONFIRMADA",
            "limite_votacion": None,
            "votos": {},
        },
    ]

if "gastos" not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        try:
            st.session_state.gastos = pd.read_excel(EXCEL_FILE)
            if "Reembolsado" not in st.session_state.gastos.columns:
                st.session_state.gastos["Reembolsado"] = "PENDIENTE ABONO"
        except:
            st.session_state.gastos = pd.DataFrame(columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado", "Enlace Ticket"])
    else:
        st.session_state.gastos = pd.DataFrame(columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado", "Enlace Ticket"])

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
            st.session_state.usuarios_registrados = df_u.set_index("Nombre").to_dict(orient="index")
        except:
            st.session_state.usuarios_registrados = {
                "Admin": {"pin": "1234", "email": "admin@safarapercussion.com", "tel": "600000000", "fnac": "01/01/1990", "instrumento": "Surdo", "rgpd": True},
                "Diego": {"pin": "1234", "email": "85diegoalvarez@gmail.com", "tel": "650184254", "fnac": "15/06/1998", "instrumento": "Surdo de contra", "rgpd": True}
            }
    else:
        st.session_state.usuarios_registrados = {
            "Admin": {"pin": "1234", "email": "admin@safarapercussion.com", "tel": "600000000", "fnac": "01/01/1990", "instrumento": "Surdo", "rgpd": True},
            "Diego": {"pin": "1234", "email": "85diegoalvarez@gmail.com", "tel": "650184254", "fnac": "15/06/1998", "instrumento": "Surdo de contra", "rgpd": True}
        }


def guardar_usuarios_excel():
    df_u = pd.DataFrame.from_dict(st.session_state.usuarios_registrados, orient="index").reset_index()
    df_u.rename(columns={"index": "Nombre"}, inplace=True)
    df_u.to_excel(EXCEL_USUARIOS, index=False)


# ==============================================================================
# --- GESTIÓN DE SESIÓN PERSISTENTE ---
# ==============================================================================
params = st.query_params
user_param = params.get("user")

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if "ultimo_acceso" not in st.session_state:
    st.session_state.ultimo_acceso = datetime.datetime.now()

if user_param and user_param in st.session_state.usuarios_registrados:
    if not st.session_state.usuario_autenticado:
        st.session_state.usuario_autenticado = user_param

if st.session_state.usuario_autenticado:
    ahora = datetime.datetime.now()
    if (ahora - st.session_state.ultimo_acceso) > datetime.timedelta(minutes=30):
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
# --- LOGIN Y REGISTRO ---
# ==============================================================================
if not st.session_state.usuario_autenticado:
    if logo_fuego_file:
        html_logo = render_logo_png(logo_fuego_file, width=210)
        if html_logo:
            st.markdown(html_logo, unsafe_allow_html=True)

    frase_actual = random.choice(FRASES_SAFARA)
    st.markdown(f'<div class="frase-chapa-badge">"{frase_actual}"</div>', unsafe_allow_html=True)

    tab_login, tab_registro = st.tabs(["ACCESO SAFARERS", "UNIRSE AL GRUPO"])

    with tab_login:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        nombres_disponibles = ["Selecciona tu usuario..."] + list(st.session_state.usuarios_registrados.keys())
        nombre_login = st.selectbox("Safarer", nombres_disponibles)
        pin_login = st.text_input("PIN de Acceso", type="password", placeholder="Introduce tu PIN")

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
                    st.rerun()
                elif nombre_login in st.session_state.admins and pin_login.strip() in ["1234", "2026"]:
                    st.session_state.usuario_autenticado = nombre_login
                    st.session_state.ultimo_acceso = datetime.datetime.now()
                    st.query_params["user"] = nombre_login
                    st.rerun()
                else:
                    st.error("PIN incorrecto.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

# ==============================================================================
# --- APLICACIÓN PRINCIPAL ---
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado
hoy_act = datetime.date.today()

primer_bolo_conf = None
if "actuaciones" in st.session_state:
    for a in st.session_state.actuaciones:
        f_act = a.get("fecha")
        if isinstance(f_act, str):
            try: f_act = datetime.date.fromisoformat(f_act)
            except: f_act = hoy_act
        if a.get("estado") == "CONFIRMADA" and f_act >= hoy_act:
            primer_bolo_conf = a
            break

txt_ticker = f"🚨 ATENCIÓN SAFARA • Próximo Bolo: {primer_bolo_conf['titulo']} ({primer_bolo_conf['lugar']}) • ¡Confirma tu asistencia! 🔥" if primer_bolo_conf else "🚨 ATENCIÓN SAFARA • ¡Próximos ensayos y eventos disponibles! 🔥"

st.markdown(f'<div class="ticker-container"><div class="ticker-text">{txt_ticker}</div></div>', unsafe_allow_html=True)

col_head_left, col_head_right = st.columns([3, 1])
with col_head_right:
    if st.button("Cerrar Sesión"):
        st.session_state.usuario_autenticado = None
        st.query_params.clear()
        st.rerun()

src_avatar = render_logo_inline_b64(logo_fuego_file) if logo_fuego_file else None
with col_head_left:
    img_html = f'<img src="{src_avatar}" />' if src_avatar else '<span style="font-size:20px; color:#E74C3C;">S</span>'
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; padding: 5px 0;">
            <div style="width: 50px; height: 50px; border-radius: 50%; background: #0D0D0D; border: 2px solid #E74C3C; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                {img_html}
            </div>
            <div>
                <h3 style="margin: 0; font-size: 18px; color: #FFFFFF;">¡Hola, {usuario_actual}!</h3>
                <p style="margin: 0; font-size: 12px; color: #AAAAAA;">{obtener_fecha_espanol()}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown(f'<div class="frase-chapa-badge">"{random.choice(FRASES_SAFARA)}"</div>', unsafe_allow_html=True)

tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(["Nuestras Movidas", "Agenda & Bolos", "Caja & Finanzas", "Administración"])

# --- PESTAÑA 1: NUESTRAS MOVIDAS ---
with tab_movidas:
    ensayo_info = st.session_state.proximo_ensayo
    fecha_ens_str = ensayo_info["fecha"].strftime("%d/%m/%Y") if isinstance(ensayo_info["fecha"], datetime.date) else str(ensayo_info["fecha"])

    confirmados_list = [u for u, v in ensayo_info["asistencia"].items() if "SI" == str(v)]
    num_confirmados = len(confirmados_list)
    ensayo_confirmado = num_confirmados >= 6
    badge_estado_ens = "🟢 CONFIRMADO" if ensayo_confirmado else "🟡 PENDIENTE DE QUORUM"
    color_badge_ens = "#2ECC71" if ensayo_confirmado else "#E74C3C"

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="text-align: center; margin: 15px 0 10px 0;">
            <h4 style="color: #FFFFFF; font-size: 16px; margin-bottom: 2px;">¿Le damos caña este viernes?</h4>
            <p style="font-size: 11px; color: #AAA; margin-top: 0;">Pulsa el logo correspondiente para responder:</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SELECTOR DE ENSAYO: LOGO PURO SIN RECARGAS NI FORMULARIOS ---
    voto_ens_actual = ensayo_info["asistencia"].get(usuario_actual, None)
    
    col_ens_si, col_ens_no = st.columns(2)

    with col_ens_si:
        cls_si = "btn-green-selected" if voto_ens_actual == "SI" else "btn-green-normal"
        st.markdown(f'<div class="btn-logo-poll {cls_si}">', unsafe_allow_html=True)
        if st.button(" ", key="poll_ens_si", help="A tope, se le da"):
            ensayo_info["asistencia"][usuario_actual] = "SI"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:700; color:#2ECC71; margin-top:4px;'>A tope, se le da</p>", unsafe_allow_html=True)

    with col_ens_no:
        cls_no = "btn-red-selected" if voto_ens_actual == "NO" else "btn-red-normal"
        st.markdown(f'<div class="btn-logo-poll {cls_no}">', unsafe_allow_html=True)
        if st.button(" ", key="poll_ens_no", help="No puedo, tengo lío"):
            ensayo_info["asistencia"][usuario_actual] = "NO"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:700; color:#E74C3C; margin-top:4px;'>No puedo, tengo lío</p>", unsafe_allow_html=True)

    st.markdown(f"<p style='text-align: center; font-size: 14px; font-weight: 800; color: #E74C3C; margin-top: 12px;'>{num_confirmados} Safarers han confirmado para este viernes</p>", unsafe_allow_html=True)

    st.markdown("---")

    # --- SELECTOR DE CENA: LOGO PURO SIN RECARGAS ---
    st.markdown("""
        <div style="background: linear-gradient(145deg, #12141a 0%, #1a0f00 100%); border: 1px solid #E74C3C; border-radius: 16px; padding: 16px; text-align: center; margin-bottom: 12px;">
            <h4 style="color: #FFFFFF; margin: 0; font-size: 15px;">CENICA POST-ENSAYO</h4>
            <p style="font-size: 13px; color: #FFD700; font-style: italic; font-weight: 600; margin-top: 4px; margin-bottom: 0;">¡Aquí se viene a lo que se viene!</p>
        </div>
    """, unsafe_allow_html=True)

    voto_cena_actual = ensayo_info["votos_cena"].get(usuario_actual, None)

    col_cena_si, col_cena_no = st.columns(2)

    with col_cena_si:
        cls_c_si = "btn-green-selected" if voto_cena_actual == "SI" else "btn-green-normal"
        st.markdown(f'<div class="btn-logo-poll {cls_c_si}">', unsafe_allow_html=True)
        if st.button(" ", key="poll_cena_si", help="De una, a cenar"):
            ensayo_info["votos_cena"][usuario_actual] = "SI"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:700; color:#2ECC71; margin-top:4px;'>De una, a cenar</p>", unsafe_allow_html=True)

    with col_cena_no:
        cls_c_no = "btn-red-selected" if voto_cena_actual == "NO" else "btn-red-normal"
        st.markdown(f'<div class="btn-logo-poll {cls_c_no}">', unsafe_allow_html=True)
        if st.button(" ", key="poll_cena_no", help="Me recojo pronto"):
            ensayo_info["votos_cena"][usuario_actual] = "NO"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:12px; font-weight:700; color:#E74C3C; margin-top:4px;'>Me recojo pronto</p>", unsafe_allow_html=True)

    num_cenan = len([u for u, v in ensayo_info["votos_cena"].items() if v == "SI"])
    st.markdown(f"<p style='text-align: center; font-size: 13px; font-weight: 800; color: #2ECC71; margin-top: 8px;'>🟢 {num_cenan} Safarers confirmados para cena</p>", unsafe_allow_html=True)

# --- PESTAÑA 2: AGENDA & BOLOS ---
with tab_eventos:
    st.markdown("<h3 style='color: #E74C3C;'>Agenda de Actuaciones</h3>", unsafe_allow_html=True)
    if primer_bolo_conf:
        st.markdown(f"""
            <div style="background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%); border: 2px solid #E74C3C; border-radius: 18px; padding: 18px; margin-bottom: 20px;">
                <span style="background: #2ECC71; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800;">PRÓXIMO BOLO CONFIRMADO</span>
                <h3 style="color: #FFFFFF; margin: 8px 0 4px 0;">{primer_bolo_conf['titulo']}</h3>
                <p style="margin: 4px 0; font-size: 14px;">Lugar: <b>{primer_bolo_conf['lugar']}</b></p>
            </div>
        """, unsafe_allow_html=True)

# --- PESTAÑA 3: CAJA & FINANZAS ---
with tab_gastos_app:
    saldo_formateado_es = formato_espanol(st.session_state.saldo_caja)
    st.markdown(f"""
        <div style="background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%); border: 2px solid #E74C3C; border-radius: 20px; padding: 24px 18px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: #E74C3C !important; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px;">Caja Rural de Navarra • Fondo Común</h2>
            <div style="font-size: 38px; font-weight: 800; color: #FFFFFF; margin: 6px 0;">{saldo_formateado_es} €</div>
        </div>
    """, unsafe_allow_html=True)

# --- PESTAÑA 4: ADMINISTRACIÓN ---
with tab_admin_app:
    pin_ing = st.text_input("Clave de Administración", type="password")
    if pin_ing == "safara2026":
        st.success("Acceso Autorizado")
        if st.session_state.usuarios_registrados:
            st.dataframe(pd.DataFrame.from_dict(st.session_state.usuarios_registrados, orient="index"), use_container_width=True)

st.divider()
if logo_delante_file:
    html_pie = render_logo_png(logo_delante_file, width=170)
    if html_pie:
        st.markdown(html_pie, unsafe_allow_html=True)

st.markdown('<div class="somos-fuego-footer">SOMOS FUEGO</div>', unsafe_allow_html=True)
