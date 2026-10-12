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
    page_title="Safara Percussion",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- FRASES DE CHAPAS SAFARA PARA LA CABECERA (SIN EMOJIS) ---
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

def cargar_imagen_b64(ruta_fichero):
    if os.path.exists(ruta_fichero):
        try:
            with open(ruta_fichero, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            return None
    return None

def buscar_logo_fuego():
    for f in os.listdir("."):
        f_lower = f.lower()
        if "detra" in f_lower and f_lower.endswith((".png", ".jpg", ".jpeg")):
            return f
    return "Logo detrás PNG.png"

# --- APLICACIÓN DE ESTILOS CSS ELEGANTE (SPARTA & ROJO RED SAFARA) ---
bg_b64 = cargar_imagen_b64("IMG_0753.jpeg")
logo_fuego_file = buscar_logo_fuego()
logo_b64 = cargar_imagen_b64(logo_fuego_file) if logo_fuego_file else None

bg_css_login = f"background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.88)), url('data:image/jpeg;base64,{bg_b64}'); background-size: cover; background-position: center; background-attachment: fixed;" if bg_b64 else "background-color: #050505;"

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

    /* INSIGNIA CENTRAL TRANSPARENTE SPARTA-STYLE */
    .sparta-logo-container {{
        text-align: center;
        margin-top: 1.2rem;
        margin-bottom: 1.2rem;
    }}
    
    .sparta-circle-logo {{
        width: 175px;
        height: 175px;
        border-radius: 50%;
        border: 2px solid rgba(231, 76, 60, 0.85);
        box-shadow: 0 0 30px rgba(231, 76, 60, 0.5);
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
        filter: drop-shadow(0px 0px 10px rgba(231, 76, 60, 0.8));
    }}

    .frase-chapa-badge {{
        text-align: center;
        font-size: 13px;
        color: #E74C3C;
        font-weight: 700;
        font-style: italic;
        margin-bottom: 25px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    /* TARJETAS CRISTAL TRASLÚCIDO CON BORDE ROJO SAFARA */
    .glass-card {{
        background: rgba(12, 12, 12, 0.82);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(231, 76, 60, 0.25);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7);
    }}

    /* BOTONES UNIFICADOS EN ROJO SAFARA */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {{
        background: linear-gradient(135deg, #C0392B 0%, #900C3F 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        padding: 12px 18px !important;
        box-shadow: 0 4px 18px rgba(192, 57, 43, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
    }}
    .stButton>button:hover {{
        box-shadow: 0 6px 22px rgba(231, 76, 60, 0.6) !important;
        transform: translateY(-1px);
    }}

    /* CAMPOS DE TEXTO E INPUTS SOBRIOS */
    input, textarea {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
        font-weight: 600 !important;
    }}

    /* OCULTAR EL RESIDUO DE TEXTO / BOTÓN DE VISIBILIDAD EN INPUT PASSWORD */
    div[data-baseweb="input"] button, 
    div[data-baseweb="input"] span[title*="Show"],
    div[data-baseweb="input"] span[title*="Hide"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: #888888 !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        font-size: 0.85rem !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: #E74C3C !important;
        border-bottom-color: #E74C3C !important;
    }}

    /* MARQUESINA EN ROJO SAFARA */
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

# CÁLCULO DE ROTACIÓN SEMANAL DE ENSAYO
hoy_m = datetime.date.today()
semana_num = hoy_m.isocalendar()[1]
ubicacion_rotativa = "Baragazte (Barañain)" if semana_num % 2 == 0 else "Gaztetxe de Zizur"

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
    st.session_state.saldo_caja = 1250.50

if "admins" not in st.session_state:
    st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if "usuarios_registrados" not in st.session_state:
    st.session_state.usuarios_registrados = {
        "Diego": {
            "pin": "1234",
            "email": "85diegoalvarez@gmail.com",
            "tel": "650184254",
            "fnac": "15/06/1998",
            "instrumento": "Surdo",
            "rgpd": True,
        }
    }

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = None

if "recientemente_registrado" not in st.session_state:
    st.session_state.recientemente_registrado = None

# ==============================================================================
# --- PANTALLA DE ACCESO Y REGISTRO (SPARTA & DEEP RED ACCENT) ------------------
# ==============================================================================
if not st.session_state.usuario_autenticado:

    # Logo con contenedor totalmente transparente
    if logo_b64:
        st.markdown(
            f"""
            <div class="sparta-logo-container">
                <div class="sparta-circle-logo">
                    <img src="data:image/png;base64,{logo_b64}" alt="Safara Logo">
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sparta-logo-container">
                <div class="sparta-circle-logo">
                    <span style="color:#E74C3C; font-weight:900; font-size:1.1rem;">SAFARA</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Frase aleatoria del grupo justo debajo del logo principal
    frase_actual = random.choice(FRASES_SAFARA)
    st.markdown(f'<div class="frase-chapa-badge">"{frase_actual}"</div>', unsafe_allow_html=True)

    tab_login, tab_registro = st.tabs(["ACCESO SAFARERS", "UNIRSE AL GRUPO"])

    with tab_login:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        nombres_disponibles = ["Selecciona tu usuario..."] + list(st.session_state.usuarios_registrados.keys())
        nombre_login = st.selectbox("Safarer", nombres_disponibles)
        pin_login = st.text_input("PIN de Acceso", type="password", placeholder="Introduce tu PIN")

        if st.button("ENTRAR EN SAFARA"):
            if nombre_login == "Selecciona tu usuario...":
                st.error("Selecciona tu nombre para continuar.")
            elif not pin_login:
                st.error("Introduce tu PIN de acceso.")
            else:
                user_info = st.session_state.usuarios_registrados.get(nombre_login)
                if user_info and str(user_info.get("pin")).strip() == pin_login.strip():
                    st.session_state.usuario_autenticado = nombre_login
                    st.rerun()
                elif nombre_login in st.session_state.admins and pin_login.strip() in ["1234", "2026"]:
                    st.session_state.usuario_autenticado = nombre_login
                    st.rerun()
                else:
                    st.error("PIN incorrecto. Revisa e inténtalo de nuevo.")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recuperación integrada vía WhatsApp
        with st.expander("¡Vaya memoria Safarer! ¿Has olvidado la contraseña?"):
            st.caption("Introduce tu teléfono de contacto para enviarte el recordatorio de PIN:")
            tel_recup = st.text_input("Teléfono Móvil Registrado", placeholder="600000000")
            if st.button("ENVIAR RECORDATORIO POR WHATSAPP"):
                if nombre_login == "Selecciona tu usuario...":
                    st.warning("Selecciona primero tu usuario en el desplegable superior.")
                elif not tel_recup:
                    st.warning("Escribe tu número de teléfono.")
                else:
                    user_info = st.session_state.usuarios_registrados.get(nombre_login, {})
                    pin_rec = user_info.get("pin", "1234")
                    msg_wa = f"Hola {nombre_login}, tu PIN de acceso para Safara Percussion es: {pin_rec}."
                    url_wa = f"https://wa.me/34{tel_recup.strip()}?text={urllib.parse.quote(msg_wa)}"
                    st.markdown(
                        f"""
                        <div style="margin-top: 10px; text-align: center;">
                            <a href="{url_wa}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 10px 16px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block;">
                                Abrir WhatsApp y Recibir PIN
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown('</div>', unsafe_allow_html=True)

    with tab_registro:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("form_registro_completo"):
            reg_nombre = st.text_input("Nombre y Apellidos *")
            reg_email = st.text_input("Correo Electrónico *")
            reg_tel = st.text_input("Teléfono Móvil *")

            reg_instrumento = st.selectbox("Instrumento Principal", ["Surdo", "Repenike", "Caja", "Surdo de contra", "Ganza (bailarinas)"])

            reg_acepta_rgpd = st.checkbox("Acepto la política de privacidad y autorizo el uso de imagen para difusión del grupo *")
            btn_reg_submit = st.form_submit_button("SOLICITAR ALTA Y GENERAR PIN")

            if btn_reg_submit:
                if not (reg_nombre and reg_email and reg_tel):
                    st.error("Completa los campos obligatorios.")
                elif not reg_acepta_rgpd:
                    st.warning("Debes aceptar la casilla de protección de datos.")
                else:
                    pin_gen = f"{random.randint(1000, 9999)}"
                    st.session_state.usuarios_registrados[reg_nombre] = {
                        "pin": pin_gen,
                        "email": reg_email,
                        "tel": reg_tel,
                        "instrumento": reg_instrumento,
                        "rgpd": True
                    }
                    st.success(f"¡Alta tramitada! Tu PIN es: *{pin_gen}*")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ==============================================================================
# --- VISTA INTERIOR (POST-LOGIN) -----------------------------------------------
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; margin-bottom: 20px;">
        <div>
            <h3 style="margin: 0; color: #FFFFFF;">¡Hola, {usuario_actual}!</h3>
            <span style="font-size: 12px; color: #888888;">{obtener_fecha_espanol()}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("Salir"):
    st.session_state.usuario_autenticado = None
    st.rerun()

tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(
    ["Nuestras Movidas", "Agenda & Bolos", "Caja & Finanzas", "Administración"]
)

with tab_movidas:
    st.markdown("### PRÓXIMO ENSAYO")
    st.info("Pestaña activa y funcional.")

with tab_eventos:
    st.markdown("### AGENDA")
    st.info("Pestaña de eventos en preparación.")

with tab_gastos_app:
    st.markdown("### CAJA & FINANZAS")
    st.info("Módulo de caja común.")

with tab_admin_app:
    st.markdown("### ADMINISTRACIÓN")
    st.info("Área privada de la junta.")
