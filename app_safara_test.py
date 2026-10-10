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
    page_title="Safara Percussion - Control Financiero", layout="centered"
)


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
                <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 15px 0;">
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


# --- ESTILOS CSS ELEGANTE DARK-FIRE ---
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
    
    .somos-fuego-footer {
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 4px;
        text-transform: uppercase;
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 50%, #FF4500 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(255, 140, 0, 0.5);
        margin: 20px 0;
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
    
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        padding: 0.8rem !important;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.4);
    }
    
    input, textarea, select {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 2px solid #444444 !important;
    }
    
    video {
        border-radius: 14px;
        border: 2px solid #FF8C00;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.3);
        width: 100%;
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- DIRECTORIOS Y ESTADOS DE SESIÓN ---
RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"
SALDO_FILE = "saldo_caja.txt"

if "gastos" not in st.session_state:
  if os.path.exists(EXCEL_FILE):
    try:
      st.session_state.gastos = pd.read_excel(EXCEL_FILE)
      if "Reembolsado" not in st.session_state.gastos.columns:
        st.session_state.gastos["Reembolsado"] = False
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
  # Diccionario: {nombre: pin_de_4_digitos}
  st.session_state.usuarios_registrados = {
      "Diego": "2026",
      "Iñigo": "1234",
      "Rosi": "5678",
  }

if "usuario_autenticado" not in st.session_state:
  st.session_state.usuario_autenticado = None

if "admin_autenticado" not in st.session_state:
  st.session_state.admin_autenticado = False

logo_fuego_file = buscar_logo_fuego()

# ==============================================================================
# --- FLUJO DE ACCESO / SEGURIDAD (EXIGIR REGISTRO Y PIN DE 4 DÍGITOS) ---------
# ==============================================================================
if not st.session_state.usuario_autenticado:

  # 1. Logo centrado
  if logo_fuego_file:
    html_logo = render_logo_png(logo_fuego_file, width=200)
    if html_logo:
      st.markdown(html_logo, unsafe_allow_html=True)

  st.markdown(
      """
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #FFD700; font-family: 'Cinzel', serif; font-size: 22px; letter-spacing: 2px;">SAFARA PERCUSSION</h2>
            <p style="color: #AAAAAA; font-size: 13px;">Asociación Cultural Nº 9.514 — Gobierno de Navarra</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

  # 2. Vídeo de San Fermín reproduciéndose al abrir la página
  if os.path.exists("IMG_8260.mov"):
    st.video("IMG_8260.mov", loop=True, autoplay=True, muted=True)

  st.markdown("<br>", unsafe_allow_html=True)

  tab_login, tab_registro = st.tabs(["Acceso con PIN", "Nuevo Registro"])

  with tab_login:
    st.markdown(
        "<p style='font-size: 13px; color: #DDD;'>Introduce tu nombre y tu"
        " PIN de 4 dígitos para acceder:</p>",
        unsafe_allow_html=True,
    )
    nombre_login = st.selectbox(
        "Selecciona tu nombre",
        ["Selecciona..."]
        + list(st.session_state.usuarios_registrados.keys())
        + st.session_state.admins,
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
      else:
        # Los admins entran directamente o con pin genérico
        if nombre_login in st.session_state.admins:
          st.session_state.usuario_autenticado = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        elif (
            nombre_login in st.session_state.usuarios_registrados
            and st.session_state.usuarios_registrados[nombre_login] == pin_login
        ):
          st.session_state.usuario_autenticado = nombre_login
          st.success(f"¡Bienvenido de nuevo, {nombre_login}!")
          st.rerun()
        else:
          st.error("PIN incorrecto o usuario no registrado.")

  with tab_registro:
    st.markdown(
        "<p style='font-size: 13px; color: #DDD;'>Regístrate para obtener"
        " acceso seguro y tu PIN de 4 dígitos:</p>",
        unsafe_allow_html=True,
    )
    nuevo_nombre = st.text_input(
        "Nombre y Apellidos / Mote", placeholder="Ej. Alex Batucada"
    )
    nuevo_tel = st.text_input(
        "Teléfono Móvil (para recibir PIN)", placeholder="600000000"
    )

    if st.button("Registrarme y Generar PIN"):
      if not nuevo_nombre or not nuevo_tel:
        st.error("Por favor, rellena todos los campos.")
      elif (
          nuevo_nombre in st.session_state.usuarios_registrados
          or nuevo_nombre in st.session_state.admins
      ):
        st.error("Este nombre ya está registrado. Inicia sesión.")
      else:
        # Generar PIN aleatorio de 4 dígitos
        pin_generado = f"{random.randint(1000, 9999)}"
        st.session_state.usuarios_registrados[nuevo_nombre] = pin_generado

        st.success(
            f"¡Registro completado con éxito, {nuevo_nombre}! Tu PIN"
            f" provisional es: **{pin_generado}**"
        )

        # Enlace simulado de WhatsApp con el PIN
        texto_w_pin = f"Hola {nuevo_nombre}, tu PIN de acceso de 4 dígitos para la app de Safara Percussion es: {pin_generado}. ¡Guárdalo bien!"
        url_wa_pin = f"https://wa.me/34{nuevo_tel}?text={urllib.parse.quote(texto_w_pin)}"

        st.markdown(
            f"""
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{url_wa_pin}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 10px 18px; border-radius: 10px; font-weight: 800; text-decoration: none; display: inline-block; font-size: 13px;">
                        Enviar PIN por WhatsApp 📱
                    </a>
                </div>
            """,
            unsafe_allow_html=True,
        )

  st.stop()  # Detiene la ejecución aquí hasta que el usuario inicie sesión correctamente

# ==============================================================================
# --- APLICACIÓN PRINCIPAL (UNA VEZ AUTENTICADO) -------------------------------
# ==============================================================================
usuario_actual = st.session_state.usuario_autenticado

col_head_left, col_head_right = st.columns([3, 1])
with col_head_right:
  if st.button("Cerrar Sesión"):
    st.session_state.usuario_autenticado = None
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

# Cálculo de Caja y Saldos
gastos_abonados_total = (
    st.session_state.gastos[st.session_state.gastos["Reembolsado"] == True][
        "Importe"
    ].sum()
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
    st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False][
        "Importe"
    ].sum()
    if not st.session_state.gastos.empty
    else 0.0
)

m1, m2 = st.columns(2)
with m1:
  st.metric("Gastos Totales", f"{formato_espanol(total_gastos_registrados)} €")
with m2:
  st.metric("Pendiente Reembolso", f"{formato_espanol(pend)} €")

st.write("")

tab_registro, tab_historial, tab_admin = st.tabs(
    ["Registrar Gasto", "Historial", "Administración"]
)

# --- PESTAÑA 1: REGISTRAR NUEVO GASTO ---
with tab_registro:
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
      st.error("Es obligatorio adjuntar el ticket para registrar el gasto.")
    elif importe <= 0:
      st.error("Por favor, introduce un importe válido mayor a 0.")
    else:
      ext = fichero.name.split(".")[-1]
      id_nuevo = (
          int(st.session_state.gastos["ID"].max() + 1)
          if not st.session_state.gastos.empty
          else 1
      )
      nombre_fichero = f"Gasto_{id_nuevo}_{fecha}_{usuario_actual}.{ext}"
      with open(os.path.join(RECEIPTS_DIR, nombre_fichero), "wb") as f:
        f.write(fichero.getbuffer())

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
          "Reembolsado": False,
      }
      st.session_state.gastos = pd.concat(
          [st.session_state.gastos, pd.DataFrame([nuevo_reg])],
          ignore_index=True,
      )
      st.session_state.gastos.to_excel(EXCEL_FILE, index=False)

      st.success("¡Gasto registrado con éxito!")

      fecha_formateada_w = fecha.strftime("%d/%m/%Y")
      texto_w = f"Hola Diego, acabo de registrar un gasto de {formato_espanol(importe)}€ en Safara Percussion ({concepto_final}) con fecha {fecha_formateada_w}. Pendiente de abono."
      url_whatsapp = (
          f"https://wa.me/34650184254?text={urllib.parse.quote(texto_w)}"
      )

      st.markdown(
          f"""
            <div style="margin-top: 15px; text-align: center;">
                <a href="{url_whatsapp}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 12px 20px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                    Avisar por WhatsApp al Tesorero 📱
                </a>
            </div>
        """,
          unsafe_allow_html=True,
      )

# --- PESTAÑA 2: HISTORIAL DE GASTOS ---
with tab_historial:
  st.markdown(
      "<p style='color: #FFD700; font-size: 14px; font-weight:"
      " 800;'>REGISTRO HISTÓRICO</p>",
      unsafe_allow_html=True,
  )

  if not st.session_state.gastos.empty:
    filtro_estado = st.selectbox(
        "Filtrar Estado", ["Todos", "Pendientes", "Reembolsados"]
    )
    df_view = st.session_state.gastos.copy()
    if filtro_estado == "Pendientes":
      df_view = df_view[df_view["Reembolsado"] == False]
    elif filtro_estado == "Reembolsados":
      df_view = df_view[df_view["Reembolsado"] == True]

    for _, row in df_view.iterrows():
      estado_badge = "PENDIENTE" if not row["Reembolsado"] else "ABONADO"
      color_badge = "#FF8C00" if not row["Reembolsado"] else "#2ECC71"
      try:
        fecha_visual = (
            datetime.date.fromisoformat(str(row["Fecha"]))
            .strftime("%d/%m/%Y")
        )
      except:
        fecha_visual = row["Fecha"]

      st.markdown(
          f"""
            <div class="expense-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #FFD700; font-size: 14px;">{row['Concepto']}</strong>
                    <span style="background: {color_badge}; color: #000; padding: 2px 7px; border-radius: 6px; font-size: 9px; font-weight: 800;">{estado_badge}</span>
                </div>
                <div style="margin-top: 6px; font-size: 12px; color: #FFFFFF;">
                    <span>Colaborador:</span> <b>{row['Usuario']}</b> | <span>Fecha:</span> {fecha_visual} | <span style="color: #FFD700; font-weight: 800;">{formato_espanol(row['Importe'])} €</span>
                </div>
            </div>
        """,
          unsafe_allow_html=True,
      )

      fich = row["Fichero"]
      if fich and isinstance(fich, str):
        path_fich = os.path.join(RECEIPTS_DIR, fich)
        if os.path.exists(path_fich):
          with st.expander(f"Ver ticket (Gasto #{row['ID']})"):
            if fich.lower().endswith((".png", ".jpg", ".jpeg")):
              st.image(path_fich, use_container_width=True)
            else:
              st.write(f"Archivo adjunto: {fich}")
  else:
    st.info("No hay gastos registrados todavía.")

# --- PESTAÑA 3: PANEL DE ADMINISTRACIÓN ---
with tab_admin:
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

    st.markdown("#### Confirmar Reembolso a Colaboradores")
    pendientes_df = (
        st.session_state.gastos[
            st.session_state.gastos["Reembolsado"] == False
        ]
        if not st.session_state.gastos.empty
        else pd.DataFrame()
    )

    if pendientes_df.empty:
      st.info("No hay gastos pendientes.")
    else:
      for idx, prow in pendientes_df.iterrows():
        col_ab1, col_ab2 = st.columns([3, 1])
        with col_ab1:
          st.write(
              f"**#{prow['ID']} - {prow['Usuario']}**:"
              f" {formato_espanol(prow['Importe'])} € ({prow['Concepto']})"
          )
        with col_ab2:
          if st.button("Abonar", key=f"abonar_{prow['ID']}"):
            st.session_state.gastos.loc[
                st.session_state.gastos["ID"] == prow["ID"], "Reembolsado"
            ] = True
            st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
            st.success(f"Gasto #{prow['ID']} abonado")
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
              fich = row["Fichero"]
              if fich and isinstance(fich, str):
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

st.markdown('<div class="somos-fuego-footer">Somos fuego</div>', unsafe_allow_html=True)
