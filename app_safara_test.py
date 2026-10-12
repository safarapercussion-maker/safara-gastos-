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
    page_title="Safara Percussion - App Oficial", layout="centered"
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
    "¡Hoy el surdo retumba por ti! ¡Feliz cumpleaños!",
    "Un año más en el DNI pero sigues dándole duro al palo. ¡Felicidades!",
    "Hoy no hay excusa: te toca pagar las cervezas post-ensayo. ¡Feliz cumple!",
    "¡Que el ritmo no pare! Disfruta de tu día con toda la energía de Safara.",
    "¡Cumpleaños On Fire! A celebrarlo como se merece.",
]

# --- UBICACIONES HABITUALES DE ENSAYO ---
UBICACIONES_ENSAYO = {
    "Baragazte (Barañain)": "https://maps.app.goo.gl/LyDLFNRPgj9WhfQk7?g_st=ic",
    "Gaztetxe de Zizur": "https://maps.app.goo.gl/PxZBzzqGTVf3qR5f6?g_st=ic",
}


# --- FUNCIONES DE APOYO Y FORMATO ---
def obtener_fecha_espanol():
  hoy = datetime.date.today()
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


# --- ESTILOS CSS SPARTA & RED SAFARA UNIFICADO ---
logo_fuego_file = buscar_logo_fuego()
bg_b64 = (
    base64.b64encode(open("IMG_0753.jpeg", "rb").read()).decode()
    if os.path.exists("IMG_0753.jpeg")
    else ""
)
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
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');
    
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
        margin-top: 1rem;
        margin-bottom: 0.5rem;
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
        margin-bottom: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    /* TARJETAS CRISTAL TRASLÚCIDO */
    .glass-card {{
        background: rgba(12, 12, 12, 0.82);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(231, 76, 60, 0.25);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7);
    }}

    /* ELIMINACIÓN DE BARRAS GRISES / CONTENEDORES NO DESEADOS EN SELECTBOX */
    div[data-testid="stSelectbox"] {{
        background: transparent !important;
        border: none !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
    }}

    /* OCULTAR TEXTO RESIDUO DE VISIBILIDAD DE CONTRASEÑA */
    div[data-baseweb="input"] button, 
    div[data-baseweb="input"] span[title*="Show"],
    div[data-baseweb="input"] span[title*="Hide"],
    div[data-baseweb="input"] div[role="button"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    input, textarea {{
        background-color: #121212 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
        font-weight: 600 !important;
    }}

    /* BOTÓN PRINCIPAL ELEGANTE ROJO SAFARA */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {{
        background: linear-gradient(135deg, #A91B0D 0%, #7B0000 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        border-radius: 12px !important;
        border: 1px solid rgba(231, 76, 60, 0.6) !important;
        width: 100% !important;
        padding: 14px 20px !important;
        box-shadow: 0 4px 20px rgba(169, 27, 13, 0.5) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton>button:hover {{
        background: linear-gradient(135deg, #C0392B 0%, #900C3F 100%) !important;
        box-shadow: 0 6px 28px rgba(231, 76, 60, 0.8) !important;
        border-color: #E74C3C !important;
    }}

    /* WEGOW TICKER */
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

FECHA_FUNDACION = datetime.date(2023, 4, 23)

hoy_m = datetime.date.today()
semana_num = hoy_m.isocalendar()[1]
ubicacion_rotativa = (
    "Baragazte (Barañain)" if semana_num % 2 == 0 else "Gaztetxe de Zizur"
)

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
  st.session_state.saldo_caja = 1250.50

if "admins" not in st.session_state:
  st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego", "Admin"]

if "usuarios_registrados" not in st.session_state:
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
          "instrumento": "Surdo",
          "rgpd": True,
      },
  }

if "usuario_autenticado" not in st.session_state:
  st.session_state.usuario_autenticado = None

if "mostrar_recuperacion" not in st.session_state:
  st.session_state.mostrar_recuperacion = False

logo_fuego_file = buscar_logo_fuego()

# ==============================================================================
# --- PANTALLA DE ACCESO Y SEGURIDAD (LOGIN & REGISTRO) ------------------------
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

    if st.button("ENTRAR EN SAFARA"):
      if nombre_login == "Selecciona tu usuario...":
        st.error("Por favor, selecciona tu nombre.")
      elif not pin_login:
        st.error("Por favor, introduce tu PIN.")
      else:
        user_info = st.session_state.usuarios_registrados.get(nombre_login)
        if user_info and str(user_info.get("pin")).strip() == pin_login.strip():
          st.session_state.usuario_autenticado = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        elif (
            nombre_login in st.session_state.admins
            and pin_login.strip() in ["1234", "2026"]
        ):
          st.session_state.usuario_autenticado = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        else:
          st.error("PIN incorrecto.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ENLACE DE RECUPERACIÓN DISCRETO Y PEQUEÑO
    if not st.session_state.mostrar_recuperacion:
      if st.button(
          "¿Vaya memoria Safarer? ¿Has olvidado la contraseña?",
          key="btn_recuperar_toggle",
      ):
        st.session_state.mostrar_recuperacion = True
        st.rerun()
    else:
      st.markdown(
          "<p style='color:#E74C3C; font-size:0.8rem; font-weight:700;"
          " margin-top:8px;'>Recuperación de PIN vía WhatsApp:</p>",
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
      reg_tel = st.text_input("Teléfono Móvil *")
      reg_instrumento = st.selectbox(
          "Instrumento Principal",
          ["Surdo", "Repenike", "Caja", "Surdo de contra", "Ganza (bailarinas)"],
      )
      reg_acepta_rgpd = st.checkbox(
          "Acepto la política de privacidad y autorizo derechos de imagen *"
      )
      btn_reg_submit = st.form_submit_button("SOLICITAR ALTA Y GENERAR PIN")

      if btn_reg_submit:
        if not (reg_nombre and reg_email and reg_tel):
          st.error("Completa los campos obligatorios.")
        elif not reg_acepta_rgpd:
          st.warning("Debes aceptar la política de privacidad.")
        else:
          pin_gen = f"{random.randint(1000, 9999)}"
          st.session_state.usuarios_registrados[reg_nombre] = {
              "pin": pin_gen,
              "email": reg_email,
              "tel": reg_tel,
              "instrumento": reg_instrumento,
              "rgpd": True,
          }
          st.success(f"¡Alta tramitada! Tu PIN personal es: **{pin_gen}**")
    st.markdown("</div>", unsafe_allow_html=True)

  st.stop()

# ==============================================================================
# --- APLICACIÓN PRINCIPAL (POST-LOGIN) -----------------------------------------
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado

hoy_act = datetime.date.today()
primer_bolo_conf = next(
    (
        a
        for a in st.session_state.actuaciones
        if a.get("estado") == "CONFIRMADA" and a.get("fecha") >= hoy_act
    ),
    None,
)

if primer_bolo_conf:
  txt_ticker = f"🚨 ATENCIÓN SAFARA • Próximo Bolo: {primer_bolo_conf['titulo']} ({primer_bolo_conf['lugar']}) el {primer_bolo_conf['fecha'].strftime('%d/%m/%Y')} a las {primer_bolo_conf['hora']} • ¡Confirma tu asistencia en la Agenda! 🔥"
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
  if st.button("Cerrar Sesión"):
    st.session_state.usuario_autenticado = None
    st.session_state.mostrar_recuperacion = False
    st.rerun()

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

tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(
    ["Nuestras Movidas", "Agenda & Bolos", "Caja & Finanzas", "Administración"]
)

with tab_movidas:
  st.markdown("### PRÓXIMO ENSAYO")
  st.info("Pestaña activa.")

with tab_eventos:
  st.markdown("### AGENDA")
  st.info("Pestaña de eventos.")

with tab_gastos_app:
  st.markdown("### CAJA & FINANZAS")
  st.info("Módulo de caja.")

with tab_admin_app:
  pin_ingresado = st.text_input(
      "Clave de Administración", type="password", placeholder="Contraseña..."
  )
  if pin_ingresado == "safara2026":
    st.success("Acceso Administrador Autorizado")
    if st.session_state.usuarios_registrados:
      st.dataframe(
          pd.DataFrame.from_dict(
              st.session_state.usuarios_registrados, orient="index"
          ),
          use_container_width=True,
      )
  elif pin_ingresado:
    st.error("Contraseña incorrecta.")
