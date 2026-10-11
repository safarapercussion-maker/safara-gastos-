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


def render_logo_png(filename, width=170):
  if filename and os.path.exists(filename):
    try:
      with open(filename, "rb") as f:
        data = f.read()
      encoded = base64.b64encode(data).decode()
      ext = filename.split(".")[-1].lower()
      mime = "image/png" if ext == "png" else "image/jpeg"
      return f"""
                <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 10px 0 5px 0;">
                    <img src="data:{mime};base64,{encoded}" width="{width}" style="display: block; background: transparent; mix-blend-mode: screen; filter: brightness(1.2) contrast(1.15);" />
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
  return None


# --- ESTILOS CSS ELEGANTE DARK-FIRE + WEGOW TICKER ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 20%, rgba(255, 140, 0, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 85% 80%, rgba(255, 215, 0, 0.1) 0%, transparent 45%),
            linear-gradient(135deg, #050505 0%, #080808 50%, #000000 100%);
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    [data-testid="stStatusWidget"], header {
        visibility: hidden !important;
        display: none !important;
    }

    /* WEGOW MARQUESINA TICKER ANIMADO */
    .ticker-container {
        width: 100%;
        background: linear-gradient(90deg, #FF4500 0%, #FF8C00 50%, #FFD700 100%);
        color: #000000;
        overflow: hidden;
        white-space: nowrap;
        box-sizing: border-box;
        border-radius: 10px;
        padding: 8px 0;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.5);
    }
    .ticker-text {
        display: inline-block;
        padding-left: 100%;
        animation: ticker 18s linear infinite;
        font-weight: 800;
        font-size: 13px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    @keyframes ticker {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }
    
    .header-user-card {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 0 15px 0;
    }
    .header-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #0D0D0D;
        border: 2px solid #FFD700;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        box-shadow: 0 4px 18px rgba(255, 215, 0, 0.4);
        flex-shrink: 0;
    }
    .header-avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        padding: 2px;
        background: #000000;
    }
    .header-greeting h2 {
        font-size: 20px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        color: #FFFFFF !important;
    }
    .header-greeting p {
        font-size: 13px !important;
        color: #AAAAAA !important;
        margin: 2px 0 0 0 !important;
        font-weight: 600;
    }
    
    .somos-fuego-titulo {
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 3px;
        text-transform: uppercase;
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 50%, #FF4500 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(255, 140, 0, 0.5);
        margin: 5px 0 5px 0;
    }

    .frase-chapa-badge {
        text-align: center;
        font-size: 12px;
        color: #FFD700;
        font-weight: 700;
        font-style: italic;
        margin-bottom: 15px;
        letter-spacing: 1px;
    }
    
    .foco-objetivo-card {
        background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%);
        border: 2px solid #FFD700;
        border-radius: 20px;
        padding: 24px 18px;
        text-align: center;
        box-shadow: 0 15px 40px rgba(255, 140, 0, 0.3);
        margin-bottom: 20px;
    }
    .foco-objetivo-card h2 {
        color: #FFD700 !important;
        font-family: 'Cinzel', serif !important;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .foco-objetivo-card .saldo-gigante {
        font-size: 38px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFD700 50%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 6px 0;
    }
    
    .expense-item {
        background: linear-gradient(145deg, #0A0A0A 0%, #121212 100%);
        border-left: 5px solid #FF8C00;
        border: 1px solid #2A2A2A;
        padding: 14px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 50%, #FF4500 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        padding: 0.85rem !important;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.4);
    }
    
    input, textarea {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 2px solid #444444 !important;
    }
    
    [data-testid="stFileUploader"], [data-testid="stFileUploader"] section {
        background-color: #12141a !important;
        border: 2px dashed #FF8C00 !important;
        border-radius: 14px !important;
        color: #FFFFFF !important;
    }
    [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small {
        color: #FFFFFF !important;
    }
    
    [data-testid="stDateInput"] div, [data-testid="stDateInput"] input {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 2px solid #555555 !important;
        font-weight: 700 !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 2px solid #555555 !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"], [role="listbox"] {
        background-color: #121212 !important;
        color: #FFFFFF !important;
        border: 2px solid #FF8C00 !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="popover"] li, div[data-baseweb="menu"] li, [role="option"] {
        background-color: #121212 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 10px 14px !important;
    }
    div[data-baseweb="popover"] li:hover, div[data-baseweb="menu"] li:hover, [role="option"]:hover, [aria-selected="true"] {
        background-color: #FF8C00 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    div[data-baseweb="select"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    video {
        border-radius: 14px;
        border: 2px solid #FF8C00;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.3);
        width: 100%;
        margin-top: 15px;
    }

    /* ESTILO BOTONES DE ENCUESTA CON LOGO INTERACTIVO */
    .fire-vote-card-green {
        background: linear-gradient(145deg, #0e2a14 0%, #15421f 100%);
        border: 2px solid #2ECC71;
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
    }
    .fire-vote-card-red {
        background: linear-gradient(145deg, #2a0e0e 0%, #421515 100%);
        border: 2px solid #E74C3C;
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }
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

# CÁLCULO DE ROTACIÓN SEMANAL DE ENSAYO
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

# CONFESIONARIO
if "confesionario_mensajes" not in st.session_state:
  st.session_state.confesionario_mensajes = []

# DATOS REALES DE ACTUACIONES DE GOOGLE DRIVE (2026 Y FUTURAS)
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
      else:
        # Normalizar booleanos a etiquetas legibles
        st.session_state.gastos["Reembolsado"] = st.session_state.gastos[
            "Reembolsado"
        ].replace(
            {True: "ABONADO", False: "PENDIENTE ABONO", "True": "ABONADO", "False": "PENDIENTE ABONO"}
        )
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
  st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if "usuarios_registrados" not in st.session_state:
  if os.path.exists(EXCEL_USUARIOS):
    try:
      df_u = pd.read_excel(EXCEL_USUARIOS)
      st.session_state.usuarios_registrados = df_u.set_index("Nombre").to_dict(
          orient="index"
      )
    except:
      st.session_state.usuarios_registrados = {
          "Diego": {
              "pin": "2026",
              "email": "85diegoalvarez@gmail.com",
              "tel": "650184254",
              "fnac": "15/06/1998",
              "instrumento": "Surdo de contra",
              "rgpd": True,
          }
      }
  else:
    st.session_state.usuarios_registrados = {
        "Diego": {
            "pin": "2026",
            "email": "85diegoalvarez@gmail.com",
            "tel": "650184264",
            "fnac": "15/06/1998",
            "instrumento": "Surdo de contra",
            "rgpd": True,
        }
    }


def guardar_usuarios_excel():
  df_u = pd.DataFrame.from_dict(
      st.session_state.usuarios_registrados, orient="index"
  ).reset_index()
  df_u.rename(columns={"index": "Nombre"}, inplace=True)
  df_u.to_excel(EXCEL_USUARIOS, index=False)


if "usuario_autenticado" not in st.session_state:
  st.session_state.usuario_autenticado = None

if "admin_autenticado" not in st.session_state:
  st.session_state.admin_autenticado = False

if "ultimo_whatsapp_url" not in st.session_state:
  st.session_state.ultimo_whatsapp_url = None

if "recientemente_registrado" not in st.session_state:
  st.session_state.recientemente_registrado = None

logo_fuego_file = buscar_logo_fuego()

# ==============================================================================
# --- PANTALLA DE ACCESO Y SEGURIDAD (LOGIN, REGISTRO Y RECUPERAR PIN) ----------
# ==============================================================================
if not st.session_state.usuario_autenticado:

  if logo_fuego_file:
    html_logo = render_logo_png(logo_fuego_file, width=200)
    if html_logo:
      st.markdown(html_logo, unsafe_allow_html=True)

  st.markdown(
      '<div class="somos-fuego-titulo">SOMOS FUEGO</div>', unsafe_allow_html=True
  )
  frase_actual = random.choice(FRASES_SAFARA)
  st.markdown(
      f'<div class="frase-chapa-badge">"{frase_actual}"</div>',
      unsafe_allow_html=True,
  )

  tab_login, tab_registro, tab_recuperar = st.tabs(
      ["Acceso Miembros", "Unirse al Grupo", "Recuperar Clave"]
  )

  with tab_login:
    st.markdown(
        "<p style='font-size: 13px; color: #DDD;'>Introduce tu nombre y tu"
        " PIN de 4 dígitos para acceder:</p>",
        unsafe_allow_html=True,
    )

    nombres_disponibles = ["Selecciona..."] + list(
        st.session_state.usuarios_registrados.keys()
    ) + [a for a in st.session_state.admins if a not in st.session_state.usuarios_registrados]

    index_def = 0
    if (
        st.session_state.recientemente_registrado
        and st.session_state.recientemente_registrado in nombres_disponibles
    ):
      index_def = nombres_disponibles.index(
          st.session_state.recientemente_registrado
      )

    nombre_login = st.selectbox(
        "Selecciona tu nombre", nombres_disponibles, index=index_def
    )
    pin_login = st.text_input(
        "PIN de Seguridad (4 dígitos)",
        type="password",
        max_chars=4,
        placeholder="••••",
    )

    if st.button("Entrar a la Aplicación"):
      if nombre_login == "Selecciona...":
        st.error("Por favor, selecciona tu nombre.")
      elif not pin_login or len(pin_login.strip()) == 0:
        st.error("Por favor, introduce tu PIN de 4 dígitos.")
      else:
        user_info = st.session_state.usuarios_registrados.get(nombre_login)
        if user_info and str(user_info.get("pin")).strip() == pin_login.strip():
          st.session_state.usuario_autenticado = nombre_login
          st.session_state.recientemente_registrado = None
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        elif (
            nombre_login in st.session_state.admins
            and pin_login.strip() == "2026"
        ):
          st.session_state.usuario_autenticado = nombre_login
          st.session_state.recientemente_registrado = None
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        else:
          st.error("PIN incorrecto o usuario no verificado.")

  with tab_registro:
    st.markdown(
        "<p style='font-size: 13px; color: #DDD;'>Regístrate para formar"
        " parte de la asociación y obtener tu PIN:</p>",
        unsafe_allow_html=True,
    )

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
      with st.expander(
          "Ver Cláusula Legal de Protección de Datos y Derechos de Imagen (RGPD)"
      ):
        st.caption(
            "De conformidad con el RGPD (UE 2016/679), la LOPDGDD 3/2018 y la"
            " LO 1/1982 sobre Protección del Derecho al Honor e Imagen, los"
            " datos recabados por SAFARA PERCUSSION serán utilizados para la"
            " gestión interna del grupo. Al registrarte, autorizas"
            " expresamente la captación y difusión de imágenes/vídeos de"
            " actuaciones en TikTok, Instagram, YouTube y la web oficial del"
            " grupo. Puedes revocar tu consentimiento en cualquier momento"
            " escribiendo a safarapercussion@gmail.com."
        )

      reg_acepta_rgpd = st.checkbox(
          "Acepto la política de privacidad y autorizo el uso de derechos de"
          " imagen para TikTok, Instagram y web *"
      )

      btn_reg_submit = st.form_submit_button("Registrarme y Generar PIN")

      if btn_reg_submit:
        if not (reg_nombre and reg_email and reg_tel):
          st.error("Por favor, completa todos los campos obligatorios.")
        elif not reg_acepta_rgpd:
          st.warning(
              "Debes aceptar la casilla de Protección de Datos e Imagen para"
              " continuar."
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

          st.session_state.recientemente_registrado = reg_nombre

          st.success(
              f"¡Registro completado con éxito, {reg_nombre}! Tu PIN"
              f" personal es: **{pin_generado}** (Guardado en el sistema)"
          )

          texto_w_pin = f"Hola {reg_nombre}, tu PIN de acceso de 4 dígitos para la app de Safara Percussion es: {pin_generado}. ¡Bienvenido a la batucada!"
          url_wa_pin = f"https://wa.me/34{reg_tel}?text={urllib.parse.quote(texto_w_pin)}"

          st.markdown(
              f"""
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{url_wa_pin}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 12px 20px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                        Enviar PIN por WhatsApp 📱
                    </a>
                </div>
            """,
              unsafe_allow_html=True,
          )

    if st.session_state.recientemente_registrado:
      st.markdown("---")
      if st.button("👉 Ir al Acceso con mi PIN"):
        st.rerun()

  with tab_recuperar:
    st.markdown(
        "<p style='font-size: 13px; color: #DDD;'>Si has olvidado tu PIN,"
        " selecciona tu usuario e introduce tu correo electrónico registrado:</p>",
        unsafe_allow_html=True,
    )

    rec_nombre = st.selectbox(
        "Usuario a recuperar",
        ["Selecciona..."]
        + list(st.session_state.usuarios_registrados.keys()),
    )
    rec_email = st.text_input("Correo electrónico registrado")

    if st.button("Recordar PIN"):
      if rec_nombre == "Selecciona...":
        st.error("Selecciona tu nombre.")
      elif not rec_email:
        st.error("Introduce tu correo electrónico.")
      else:
        datos_user = st.session_state.usuarios_registrados.get(rec_nombre)
        if datos_user and (
            str(datos_user.get("email")).strip().lower()
            == rec_email.strip().lower()
        ):
          pin_rec = datos_user.get("pin")
          st.success(
              f"¡Verificado! Tu PIN de acceso registrado es: **{pin_rec}**"
          )

          texto_rec_w = f"Hola {rec_nombre}, tu PIN de acceso a la app de Safara Percussion es: {pin_rec}."
          tel_rec = datos_user.get("tel", "")
          if tel_rec:
            url_rec_wa = f"https://wa.me/34{tel_rec}?text={urllib.parse.quote(texto_rec_w)}"
            st.markdown(
                f"""
                        <div style="margin-top: 10px; text-align: center;">
                            <a href="{url_rec_wa}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 10px 16px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block;">
                                Enviar Recordatorio por WhatsApp 📱
                            </a>
                        </div>
                    """,
                unsafe_allow_html=True,
            )
        else:
          st.error("El correo introducido no coincide con el usuario registrado.")

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown(
      "<p style='text-align: center; color: #FFD700; font-size: 13px;"
      " font-weight: 600;'>Siente la energía de la calle:</p>",
      unsafe_allow_html=True,
  )
  if os.path.exists("IMG_8260.mov"):
    st.video("IMG_8260.mov", loop=True, autoplay=True, muted=True)

  st.stop()

# ==============================================================================
# --- APLICACIÓN PRINCIPAL (POST-REGISTRO / ACCESO DENTRO) ---------------------
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado

# FILTRAR ÚNICAMENTE LA PRÓXIMA ACTUACIÓN FUTURA REAL DE DRIVE
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
    st.session_state.ultimo_whatsapp_url = None
    st.rerun()

src_avatar = (
    render_logo_inline_b64(logo_fuego_file) if logo_fuego_file else None
)
fecha_hoy_str = obtener_fecha_espanol()

with col_head_left:
  img_html = (
      f'<img src="{src_avatar}" />'
      if src_avatar
      else '<span style="font-size:20px; color:#FFD700; font-weight:800;">S</span>'
  )
  st.markdown(
      f"""
        <div class="header-user-card">
            <div class="header-avatar">{img_html}</div>
            <div class="header-greeting">
                <h2>¡Hola, {usuario_actual}!</h2>
                <p>{fecha_hoy_str}</p>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

logo_sup = "Logo delante PNG.png"
if os.path.exists(logo_sup):
  html_s = render_logo_png(logo_sup, width=170)
  if html_s:
    st.markdown(html_s, unsafe_allow_html=True)

# LEMA ALEATORIO DENTRO DE LA APP
st.markdown(
    f'<div class="frase-chapa-badge">"{random.choice(FRASES_SAFARA)}"</div>',
    unsafe_allow_html=True,
)

# NAV DE PESTAÑAS PRINCIPALES INTERNAS
tab_movidas, tab_eventos, tab_gastos_app, tab_admin_app = st.tabs(
    ["Nuestras Movidas", "Agenda & Bolos", "Caja & Finanzas", "Administración"]
)

# --- PESTAÑA 1: NUESTRAS MOVIDAS ---
with tab_movidas:

  # 1. NOTIFICACIÓN DE CUMPLEAÑOS DEL DÍA
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
            <div style="background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%); border-radius: 14px; padding: 14px; text-align: center; margin-bottom: 15px; color: #000; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);">
                <strong style="font-size: 16px; color: #000;">¡HOY ES EL CUMPLEAÑOS DE {c_nombre.upper()}!</strong><br>
                <span style="font-size: 13px; font-style: italic; font-weight: 600; color: #111;">"{random.choice(FRASES_CUMPLE)}"</span>
            </div>
        """,
          unsafe_allow_html=True,
      )

  # 2. PRÓXIMO ENSAYO Y ENCUESTA DE ASISTENCIA SEMANAL (CON ESTADO PENDIENTE/CONFIRMADO Y SAFARERS)
  ensayo_info = st.session_state.proximo_ensayo
  fecha_ens_str = ensayo_info["fecha"].strftime("%d/%m/%Y")

  confirmados_list = [
      u for u, v in ensayo_info["asistencia"].items() if "tope" in v.lower()
  ]
  num_confirmados = len(confirmados_list)

  # Mínimo de 6 Safarers para confirmar automáticamente el ensayo
  ensayo_confirmado = num_confirmados >= 6
  badge_estado_ens = (
      "🟢 CONFIRMADO" if ensayo_confirmado else "🟡 PENDIENTE DE QUORUM"
  )
  color_badge_ens = "#2ECC71" if ensayo_confirmado else "#FF8C00"

  st.markdown(
      f"""
        <div style="background: linear-gradient(145deg, #180E00 0%, #0D0D0D 100%); border: 2px solid #FF8C00; border-radius: 18px; padding: 18px; text-align: center; margin-bottom: 15px;">
            <span style="background: {color_badge_ens}; color: #000; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 800;">{badge_estado_ens}</span>
            <h3 style="color: #FFD700; margin: 10px 0 4px 0; font-size: 18px;">PRÓXIMO ENSAYO</h3>
            <p style="font-size: 15px; margin: 4px 0;"><b>Fecha:</b> {fecha_ens_str} ({ensayo_info['hora']})</p>
            <p style="font-size: 14px; margin: 4px 0;"><b>Ubicación:</b> {ensayo_info['ubicacion_nombre']}</p>
            <div style="margin-top: 10px;">
                <a href="{ensayo_info['url_maps']}" target="_blank" style="background: #FF8C00; color: #000; padding: 8px 16px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block;">
                    Ver Ubicación en Google Maps 📍
                </a>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # ENCUESTA CON LOGO DE FUEGO CLICABLE (VERDE / ROJO)
  st.markdown(
      """
        <div style="text-align: center; margin: 20px 0 10px 0;">
            <h4 style="color: #FFD700; font-size: 18px; margin-bottom: 5px;">¿Le damos caña este viernes?</h4>
            <p style="font-size: 12px; color: #AAA; margin-top: 0;">Haz clic en la llama correspondiente para registrar tu voto:</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  col_e1, col_e2 = st.columns(2)
  with col_e1:
    if logo_fuego_file:
      b64_logo_v = render_logo_inline_b64(logo_fuego_file)
      st.markdown(
          f"""
                <div class="fire-vote-card-green">
                    <img src="{b64_logo_v}" style="width: 45px; filter: drop-shadow(0 0 8px #2ECC71); margin-bottom: 5px;" />
                </div>
            """,
          unsafe_allow_html=True,
      )
    if st.button("¡A tope, se le da!", key="ens_si"):
      ensayo_info["asistencia"][usuario_actual] = "¡A tope, se le da!"
      st.success("¡Asistencia confirmada!")
      st.rerun()

  with col_e2:
    if logo_fuego_file:
      b64_logo_r = render_logo_inline_b64(logo_fuego_file)
      st.markdown(
          f"""
                <div class="fire-vote-card-red">
                    <img src="{b64_logo_r}" style="width: 45px; filter: drop-shadow(0 0 8px #E74C3C); margin-bottom: 5px;" />
                </div>
            """,
          unsafe_allow_html=True,
      )
    if st.button("No puedo, ¡tengo lío!", key="ens_no"):
      ensayo_info["asistencia"][usuario_actual] = "No puedo, ¡tengo lío!"
      st.warning("Ausencia registrada.")
      st.rerun()

  # CONTADOR DE SAFARERS CONFIRMADAS/OS
  st.markdown(
      f"<p style='text-align: center; font-size: 15px; font-weight: 800;"
      f" color: #FFD700; margin-top: 15px;'>🔥 {num_confirmados} Safarers han"
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
        f"🥁 Repenikes: {counts['Repenike']} | 🥁 Cajas: {counts['Caja']} | 🥁"
        f" Surdos: {counts['Surdo']} | 🥁 Surdos de contra:"
        f" {counts['Surdo de contra']} | 💃 Bailarinas:"
        f" {counts['Ganza (bailarinas)']}"
    )

  st.markdown("---")

  # 3. ENCUESTA EXPRESS CENA (DESTACADA Y CENTRADA)
  st.markdown(
      """
        <div style="background: linear-gradient(145deg, #12141a 0%, #1a0f00 100%); border: 1px solid #FF8C00; border-radius: 16px; padding: 16px; text-align: center; margin-bottom: 20px;">
            <h4 style="color: #FFD700; margin-top: 0; font-size: 16px;">🍻 LA PRE-CENA POST-ENSAYO 🍔</h4>
            <p style="font-size: 13px; color: #DDD; margin-bottom: 12px;">¿Hoy se cena tras el ensayo?</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  c_col1, c_col2 = st.columns(2)
  with c_col1:
    if st.button("¡De una! A cenar y lo que surja", key="cena_si"):
      ensayo_info["votos_cena"][usuario_actual] = "¡De una! A cenar"
      st.success("¡Voto registrado para la cena!")
  with c_col2:
    if st.button("Hoy me recojo pronto tras tocar", key="cena_no"):
      ensayo_info["votos_cena"][usuario_actual] = "Hoy me recojo pronto"
      st.warning("Voto registrado.")

  st.markdown("---")

  # 4. DASHBOARD DE MÉTRICAS HISTÓRICAS REALES DE GOOGLE DRIVE (2024 - 2026)
  st.markdown(
      "<h4 style='color: #FFD700;'>Evolución de Actuaciones Safara</h4>",
      unsafe_allow_html=True,
  )

  m_col1, m_col2, m_col3 = st.columns(3)
  with m_col1:
    st.metric("2024", "5 bolos")
  with m_col2:
    st.metric("2025", "21 bolos")
  with m_col3:
    st.metric("2026", "14 bolos")

  st.caption(
      "🚀 CRECIMIENTO: Más de 40 actuaciones acumuladas en Navarra haciendo"
      " retumbar la calle."
  )

  st.markdown("---")

  # 5. REDES SOCIALES
  st.markdown(
      "<h4 style='color: #FFD700;'>Safara en Redes Sociales</h4>",
      unsafe_allow_html=True,
  )

  r_col1, r_col2 = st.columns(2)
  with r_col1:
    st.markdown(
        """
            <div style="background: #12141a; border: 1px solid #FF8C00; border-radius: 12px; padding: 12px; text-align: center;">
                <b style="color: #FFD700;">Instagram Oficial</b><br><br>
                <a href="https://www.instagram.com/safarapercussion?srtk=Ym9jYTB0eWF2cjQz" target="_blank" style="background: #E1306C; color: #FFF; padding: 8px 14px; border-radius: 8px; font-weight: 800; text-decoration: none; display: inline-block;">
                    Ver Instagram
                </a>
            </div>
        """,
        unsafe_allow_html=True,
    )

  with r_col2:
    st.markdown(
        """
            <div style="background: #12141a; border: 1px solid #FF8C00; border-radius: 12px; padding: 12px; text-align: center;">
                <b style="color: #FFD700;">TikTok Oficial</b><br><br>
                <a href="https://www.tiktok.com/@safarapercussion?_r=1&_t=ZN-9ASh8h0A2Le" target="_blank" style="background: #000; color: #FFF; border: 1px solid #FFF; padding: 8px 14px; border-radius: 8px; font-weight: 800; text-decoration: none; display: inline-block;">
                    Ver TikTok
                </a>
            </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("---")

  # 6. EL CONFESIONARIO
  st.markdown(
      "<h4 style='color: #FFD700;'>El Confesionario</h4>", unsafe_allow_html=True
  )
  confesion_txt = st.text_area(
      "Tu mensaje confidencial para el grupo",
      placeholder="Escribe tu idea o propuesta aquí...",
      key="confesion_input",
  )
  if st.button("Enviar al Confesionario"):
    if confesion_txt.strip():
      st.session_state.confesionario_mensajes.append({
          "fecha": datetime.date.today().strftime("%d/%m/%Y"),
          "usuario": usuario_actual,
          "mensaje": confesion_txt.strip(),
      })
      st.success("¡Mensaje guardado en el confesionario!")
      st.rerun()
    else:
      st.error("Escribe un mensaje antes de enviar.")

# --- PESTAÑA 2: AGENDA & BOLOS (SISTEMA DE QUORUM MÍNIMO) ---
with tab_eventos:
  st.markdown(
      "<h3 style='color: #FFD700;'>Agenda de Actuaciones</h3>",
      unsafe_allow_html=True,
  )

  # 1. BOLO MÁS CERCANO CONFIRMADO (SOLO FUTUROS RECTIFICADOS CON DRIVE)
  if primer_bolo_conf:
    st.markdown(
        f"""
            <div style="background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%); border: 2px solid #FFD700; border-radius: 18px; padding: 18px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(255, 140, 0, 0.4);">
                <span style="background: #2ECC71; color: #000; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 800;">PRÓXIMO BOLO CONFIRMADO</span>
                <h3 style="color: #FFD700; margin: 8px 0 4px 0;">{primer_bolo_conf['titulo']}</h3>
                <p style="margin: 4px 0; font-size: 14px;">📅 <b>Fecha:</b> {primer_bolo_conf['fecha'].strftime('%d/%m/%Y')} | ⏰ <b>Hora:</b> {primer_bolo_conf['hora']}<br>📍 <b>Lugar:</b> {primer_bolo_conf['lugar']}</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

  # 2. BOLOS EN EVALUACIÓN DE QUORUM (FILTRADOS SOLO FUTUROS)
  st.markdown("#### 🟡 Bolos en Evaluación (Encuesta con Quorum)")
  evaluaciones = [
      a
      for a in st.session_state.actuaciones
      if a.get("estado") == "EVALUACION" and a.get("fecha") >= hoy_act
  ]

  if not evaluaciones:
    st.info("No hay encuestas de bolos activas ahora mismo.")
  else:
    for ev in evaluaciones:
      st.markdown(
          f"""
                <div style="background: #12141a; border-left: 5px solid #FF8C00; border: 1px solid #2a2a2a; border-radius: 14px; padding: 16px; margin-bottom: 15px;">
                    <strong style="color: #FFD700; font-size: 16px;">{ev['titulo']}</strong><br>
                    <span>📅 Fecha: {ev['fecha'].strftime('%d/%m/%Y')} | 📍 Lugar: {ev['lugar']}</span>
                </div>
            """,
          unsafe_allow_html=True,
      )

      col_av1, col_av2 = st.columns(2)
      with col_av1:
        if logo_fuego_file:
          b64_logo_v = render_logo_inline_b64(logo_fuego_file)
          st.markdown(
              f"""
                    <div class="fire-vote-card-green">
                        <img src="{b64_logo_v}" style="width: 40px; filter: drop-shadow(0 0 8px #2ECC71);" />
                    </div>
                """,
              unsafe_allow_html=True,
          )
        if st.button("¡De una! A arder", key=f"v_si_{ev['id']}"):
          ev["votos"][usuario_actual] = "SI"
          st.success("¡Voto SI registrado!")
          st.rerun()

      with col_av2:
        if logo_fuego_file:
          b64_logo_r = render_logo_inline_b64(logo_fuego_file)
          st.markdown(
              f"""
                    <div class="fire-vote-card-red">
                        <img src="{b64_logo_r}" style="width: 40px; filter: drop-shadow(0 0 8px #E74C3C);" />
                    </div>
                """,
              unsafe_allow_html=True,
          )
        if st.button("No puedo, FOMO!", key=f"v_no_{ev['id']}"):
          ev["votos"][usuario_actual] = "NO"
          st.warning("Voto NO registrado.")
          st.rerun()

      votos_si_users = [u for u, v in ev["votos"].items() if v == "SI"]
      q_counts = {
          "Repenike": 0,
          "Caja": 0,
          "Surdo": 0,
          "Surdo de contra": 0,
          "Ganza (bailarinas)": 0,
      }
      for v_u in votos_si_users:
        u_inst = st.session_state.usuarios_registrados.get(v_u, {}).get(
            "instrumento", "Repenike"
        )
        if u_inst in q_counts:
          q_counts[u_inst] += 1
        else:
          q_counts["Repenike"] += 1

      cumple_quorum = (
          q_counts["Repenike"] >= 1
          and q_counts["Caja"] >= 1
          and q_counts["Surdo de contra"] >= 1
          and q_counts["Surdo"] >= 3
          and q_counts["Ganza (bailarinas)"] >= 2
      )

      if cumple_quorum:
        st.success(
            "🟢 ¡QUORUM ALCANZADO! Este bolo es viable segun las cuotas del"
            " grupo."
        )
      else:
        st.warning(
            "🟡 PENDIENTE DE QUORUM: Requisitos mínimos: 1 Repenike, 1 Caja, 1"
            " Surdo de contra, 3 Surdos y 2 Bailarinas."
        )

      st.caption(
          f"Confirmados actual: Repenikes: {q_counts['Repenike']}/1 | Cajas:"
          f" {q_counts['Caja']}/1 | Contra: {q_counts['Surdo de contra']}/1 |"
          f" Surdos: {q_counts['Surdo']}/3 | Bailarinas:"
          f" {q_counts['Ganza (bailarinas)']}/2"
      )

  st.markdown("---")
  st.markdown("#### 🟢 Próximas Actuaciones Confirmadas")
  conf_list = [
      a
      for a in st.session_state.actuaciones
      if a.get("estado") == "CONFIRMADA" and a.get("fecha") >= hoy_act
  ]
  if conf_list:
    for c_act in conf_list:
      st.write(
          f"• **{c_act['fecha'].strftime('%d/%m/%Y')}** - {c_act['titulo']} en"
          f" {c_act['lugar']} ({c_act['hora']})"
      )
  else:
    st.info("No hay más actuaciones confirmadas por ahora.")

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
        <div class="foco-objetivo-card">
            <h2>Caja Rural de Navarra • Fondo Común</h2>
            <div class="saldo-gigante">{saldo_formateado_es} €</div>
            <p>Recaudación y gestión de fondos para ensayos, eventos y material.</p>
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
        "Importe (€) *", min_value=0.0, value=0.0, step=1.0, format="%.2f"
    )
    fecha = st.date_input(
        "Fecha del gasto *",
        datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))
        .date()
        .today(),
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

        # NOMENCLATURA HOMOGÉNEA SOLICITADA
        nombre_fichero = (
            f"Gasto_{id_nuevo}_{fecha}_{usuario_actual}_{importe}EUR.{ext}"
        )
        path_destino = os.path.join(RECEIPTS_DIR, nombre_fichero)

        with open(path_destino, "wb") as f:
          f.write(fichero.getbuffer())

        concepto_final = f"{categoria_seleccionada}" + (
            f" - {detalle_concepto}" if detalle_concepto else ""
        )

        # HIPERVÍNCULO EN EXCEL
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

        # MENSAJE EXACTO DE WHATSAPP ACORDADO
        texto_w = f"¡Aupa! Hay nuevo gasto registrado en la app: {formato_espanol(importe)} € por {concepto_final}. Ticket adjuntado y listo para revisión y abono. ¡Seguimos On Fire! 🔥🥁"
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
      if st.button("✔ Confirmar Aviso Enviado (Ocultar Botón)"):
        st.session_state.ultimo_whatsapp_url = None
        st.rerun()

  with tab_sub_hist:
    st.markdown(
        "<p style='color: #FFD700; font-size: 14px; font-weight:"
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
          color_badge = (
              "#2ECC71" if estado_txt == "ABONADO" else "#FF8C00"
          )
          try:
            fecha_visual = (
                datetime.date.fromisoformat(str(row["Fecha"]))
                .strftime("%d/%m/%Y")
            )
          except:
            fecha_visual = str(row["Fecha"])

          st.markdown(
              f"""
                    <div class="expense-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: #FFD700; font-size: 14px;">{row['Concepto']}</strong>
                            <span style="background: {color_badge}; color: #000; padding: 2px 7px; border-radius: 6px; font-size: 9px; font-weight: 800;">{estado_txt}</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 12px; color: #FFFFFF;">
                            <span>Colaborador:</span> <b>{row['Usuario']}</b> | <span>Fecha:</span> {fecha_visual} | <span style="color: #FFD700; font-weight: 800;">{formato_espanol(row['Importe'])} €</span>
                        </div>
                    </div>
                """,
              unsafe_allow_html=True,
          )

          # PREVISUALIZACIÓN DE TICKETS Y FOTOS REPARADA
          fich = row.get("Fichero")
          if fich and isinstance(fich, str) and str(fich) != "nan":
            path_fich = os.path.join(RECEIPTS_DIR, fich)
            if os.path.exists(path_fich):
              with st.expander(f"📷 Previsualizar Ticket (Gasto #{row['ID']})"):
                ext = fich.lower().split(".")[-1]
                if ext in ["png", "jpg", "jpeg"]:
                  st.image(path_fich, use_container_width=True)
                elif ext == "pdf":
                  st.write(
                      f"📄 Archivo PDF adjunto: `{fich}` (Disponible en"
                      " auditoría)"
                  )
                else:
                  st.write(f"📁 Archivo adjunto: `{fich}`")
      else:
        st.info("No hay gastos registrados todavía.")
    except Exception as e:
      st.warning(
          "Cargando historial de gastos... Presiona recargar si es necesario."
      )

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
    st.success("✅ Acceso de Administración Autorizado")

    # CREAR ENCUESTA DE BOLO
    st.markdown("#### 📅 Lanzar Nueva Encuesta de Bolo")
    with st.form("form_crear_bolo_admin"):
      b_tit = st.text_input("Título de la Actuación")
      b_fec = st.date_input("Fecha del Evento", datetime.date.today())
      b_hor = st.text_input("Hora", value="Tarde")
      b_lug = st.text_input("Lugar / Municipio")
      b_est = st.selectbox(
          "Estado Inicial", ["EVALUACION", "CONFIRMADA", "STANDBY"]
      )
      if st.form_submit_button("Guardar Actuación"):
        nuevo_id_act = len(st.session_state.actuaciones) + 1
        st.session_state.actuaciones.append({
            "id": nuevo_id_act,
            "titulo": b_tit,
            "fecha": b_fec,
            "hora": b_hor,
            "lugar": b_lug,
            "estado": b_est,
            "limite_votacion": datetime.datetime.now()
            + datetime.timedelta(days=3),
            "votos": {},
        })
        st.success("¡Actuación creada y publicada!")
        st.rerun()

    st.markdown("---")

    # MENSAJES DEL CONFESIONARIO
    st.markdown("#### 💬 Mensajes del Confesionario")
    if st.session_state.confesionario_mensajes:
      for m_conf in st.session_state.confesionario_mensajes:
        st.write(
            f"• **[{m_conf['fecha']}] {m_conf['usuario']}**: {m_conf['mensaje']}"
        )
    else:
      st.info("No hay mensajes nuevos en el confesionario.")

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
      st.markdown("#### 🗑️ Depurar / Eliminar Usuarios Duplicados")
      socios_lista = list(st.session_state.usuarios_registrados.keys())
      socio_a_borrar = st.selectbox(
          "Selecciona el usuario que quieras eliminar:", socios_lista
      )

      if st.button("❌ Eliminar Socio Seleccionado"):
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

    with st.expander("Generar Paquete de Auditoría (ZIP + Excel)", expanded=False):
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
                  clean_concept = re.sub(
                      r"[^a-zA-Z0-9]", "_", row["Concepto"]
                  )[:30]
                  ext = fich.split(".")[-1]
                  zip_name = f"Justificantes/ID_{row['ID']}_{row['Fecha']}_{clean_concept}_{row['Importe']}EUR.{ext}"
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

if logo_fuego_file:
  html_i = render_logo_png(logo_fuego_file, width=170)
  if html_i:
    st.markdown(html_i, unsafe_allow_html=True)

st.markdown('<div class="somos-fuego-titulo">SOMOS FUEGO</div>', unsafe_allow_html=True)
