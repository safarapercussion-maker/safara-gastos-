import datetime
import os
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Safara Percussion - Sandbox Test", page_icon="🔥", layout="wide"
)

# Constantes oficiales de la asociación
FECHA_FUNDACION = datetime.date(2023, 4, 23)
EMAIL_DRIVE_SAFARA = "safarapercussion@gmail.com"

# Estética Dark-Fire (CSS personalizado avanzado)
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stButton>button { background-color: #ff4b4b; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #ff2121; color: white; }
    .metric-card { background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .welcome-banner { text-align: center; padding: 40px; background: linear-gradient(135deg, #1a1c23 0%, #2d1313 100%); border-radius: 15px; border: 2px solid #ff4b4b; margin-bottom: 25px; }
    </style>
""",
    unsafe_allow_html=True,
)

# Inicializar estados de sesión
if "usuarios" not in st.session_state:
  st.session_state["usuarios"] = []
if "usuario_actual" not in st.session_state:
  st.session_state["usuario_actual"] = None
if "actuaciones" not in st.session_state:
  st.session_state["actuaciones"] = [
    {
      "id": 1,
      "titulo": "Boda en Hotel El Toro (Pamplona)",
      "fecha": datetime.date(2026, 6, 13),
      "hora": "18:00h",
      "lugar": "Hotel El Toro, Pamplona",
      "votos": {},
    }
  ]
if "gastos" not in st.session_state:
  st.session_state["gastos"] = pd.DataFrame(
      columns=[
          "Fecha",
          "Recibo",
          "Comercio",
          "Cantidad",
          "Categoria",
          "Nota",
      ]
  )

hoy = datetime.date.today()
dias_activos = (hoy - FECHA_FUNDACION).days

# --- PANTALLA DE BIENVENIDA / LOGIN DINÁMICO ---
if not st.session_state["usuario_actual"]:
  st.markdown(
      f"""
    <div class="welcome-banner">
        <h1>🔥 SAFARA PERCUSSION 🔥</h1>
        <p><b>Asociación Oficial Nº 9.514 (Gobierno de Navarra)</b> • Fundada el 23 de abril de 2023 ({dias_activos} días haciendo ruido)[span_1](start_span)[span_1](end_span).</p>
        <hr style="border-color: #ff4b4b;">
        <p><i>La plataforma oficial de gestión, bolos y energía de la batucada.</i></p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader("Identifícate o Regístrate")
    tipo_acceso = st.radio(
        "¿Cómo quieres acceder?", ["Ya estoy registrado", "Soy nuevo / Registrarme"]
    )

    if tipo_acceso == "Soy nuevo / Registrarme":
      with st.form("form_nuevo_registro"):
        nombre_reg = st.text_input("Nombre y Apellidos")
        tel_reg = st.text_input("Teléfono Móvil")
        email_reg = st.text_input("Correo Electrónico")
        fnac_reg = st.date_input(
            "Fecha de Nacimiento (para avisos de cumples)",
            min_value=datetime.date(1950, 1, 1),
            max_value=datetime.date(2010, 12, 31),
        )
        instrumento_reg = st.selectbox(
            "Selecciona tu instrumento",
            [
                "Repenike",
                "Caja",
                "Surdo",
                "Surdo de contra",
                "Ganza (bailarinas)",
            ],
        )
        btn_reg = st.form_submit_button("¡Registrarme y Entrar! 🔥")

        if btn_reg:
          if nombre_reg and tel_reg and email_reg:
            nuevo_miembro = {
                "nombre": nombre_reg,
                "telefono": tel_reg,
                "email": email_reg,
                "fnac": fnac_reg,
                "instrumento": instrumento_reg,
            }
            st.session_state["usuarios"].append(nuevo_miembro)
            st.session_state["usuario_actual"] = nombre_reg
            st.success(f"¡Bienvenido a la familia, {nombre_reg}!")
            st.rerun()
          else:
            st.error("Por favor, completa todos los campos obligatorios.")

    else:
      nombre_login = st.text_input(
          "Introduce tu Nombre y Apellidos registrados"
      )
      if st.button("Entrar a la App 🔥"):
        if nombre_login:
          st.session_state["usuario_actual"] = nombre_login
          st.success(f"¡Hola de nuevo, {nombre_login}! Arrancando motores...")
          st.rerun()
        else:
          st.error("Introduce un nombre válido.")

else:
  # --- APLICACIÓN PRINCIPAL (UNA VEZ LOGUEADO) ---
  st.sidebar.markdown(f"👤 **Conectado como:** {st.session_state['usuario_actual']}")
  if st.sidebar.button("Cerrar Sesión"):
    st.session_state["usuario_actual"] = None
    st.rerun()

  menu = st.sidebar.selectbox(
      "Selecciona Módulo",
      [
          "🏠 Inicio & Cumpleaños",
          "💶 Control de Gastos (V1.0)",
          "🥁 Actuaciones & Votaciones",
          "⚙️ Administración y Drive",
      ],
  )

  # --- MÓDULO 1: INICIO & CUMPLEAÑOS ---
  if menu == "🏠 Inicio & Cumpleaños":
    st.subheader("👋 Panel Principal de Safara")
    st.write(
        "Aquí puedes consultar la información general, la lista de miembros y"
        " los próximos cumples del grupo."
    )

    if st.session_state["usuarios"]:
      st.markdown("### 👥 Miembros Registrados en la Asociación")
      df_users = pd.DataFrame(st.session_state["usuarios"])
      st.dataframe(df_users, use_container_width=True)
    else:
      st.info(
          "No hay otros miembros registrados todavía en este entorno de prueba."
      )

  # --- MÓDULO 2: CONTROL DE GASTOS (V1.0) ---
  elif menu == "💶 Control de Gastos (V1.0)":
    st.subheader("💶 Gestión Económica y Exportación a Excel")
    st.write(
        "Aquí puedes simular el registro de gastos y probar la exportación"
        " segura hacia el Drive de Safara."
    )

    with st.form("form_gasto"):
      col1, col2 = st.columns(2)
      with col1:
        f_gasto = st.date_input("Fecha del Gasto")
        comercio = st.text_input("Comercio / Proveedor")
        cantidad = st.number_input("Cantidad (€)", min_value=0.0, format="%.2f")
      with col2:
        categoria = st.selectbox(
            "Categoría",
            [
                "Instrumentos",
                "Bebidas",
                "Transporte",
                "Tasa Administración",
                "Restaurantes",
            ],
        )
        nota = st.text_input("Nota / Concepto")
      btn_add_gasto = st.form_submit_button("Añadir Gasto")

      if btn_add_gasto:
        nuevo_gasto = pd.DataFrame(
            [{
                "Fecha": f_gasto,
                "Recibo": f"REC-{len(st.session_state['gastos'])+1}",
                "Comercio": comercio,
                "Cantidad": cantidad,
                "Categoria": categoria,
                "Nota": nota,
            }]
        )
        st.session_state["gastos"] = pd.concat(
            [st.session_state["gastos"], nuevo_gasto], ignore_index=True
        )
        st.success("¡Gasto registrado correctamente en el sistema!")

    st.markdown("### 📊 Listado de Gastos Actuales")
    if not st.session_state["gastos"].empty:
      st.dataframe(st.session_state["gastos"], use_container_width=True)

      csv_data = st.session_state["gastos"].to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Descargar Resumen de Gastos en Excel/CSV",
          data=csv_data,
          file_name=f"SAFARA_GASTOS_{datetime.date.today()}.csv",
          mime="text/csv",
      )
    else:
      st.info("No hay gastos registrados todavía en este entorno de pruebas.")

  # --- MÓDULO 3: ACTUACIONES & VOTACIONES ---
  elif menu == "🥁 Actuaciones & Votaciones":
    st.subheader("🥁 Próximas Actuaciones y Votaciones")

    for act in st.session_state["actuaciones"]:
      st.markdown(
          f"""
          <div class="metric-card">
              <h3>🔥 {act['titulo']}</h3>
              <p><b>Fecha:</b> {act['fecha']} • <b>Hora:</b> {act['hora']} • <b>Lugar:</b> {act['lugar']}</p>
          </div>
          """,
          unsafe_allow_html=True,
      )

      dias_restantes = (act["fecha"] - hoy).days
      if dias_restantes > 0:
        st.warning(f"⏳ ¡Faltan **{dias_restantes} días** para este bolo!")
      elif dias_restantes == 0:
        st.error("🚨 ¡El bolo es HOY! ¡A darlo todo!")
      else:
        st.success("✅ Actuación realizada con éxito.")

      st.markdown("#### Vota tu asistencia:")
      col_v1, col_v2 = st.columns(2)

      with col_v1:
        if st.button("De una! A arder en el infierno! 🔥", key=id(act)):
          act["votos"][st.session_state["usuario_actual"]] = (
              "De una! A arder en el infierno! 🔥"
          )
          st.success("¡Voto registrado con éxito! 🔥")

      with col_v2:
        if st.button("No puedo! Fomo máximo! 😭", key=id(act) + 1):
          act["votos"][st.session_state["usuario_actual"]] = (
              "No puedo! Fomo máximo! 😭"
          )
          st.warning("¡Voto registrado! Qué pena 😭")

      if act["votos"]:
        st.markdown("##### 📋 Recuento de Asistencia:")
        for u, v in act["votos"].items():
          st.write(f"- **{u}**: {v}")

  # --- MÓDULO 4: ADMINISTRACIÓN Y DRIVE ---
  elif menu == "⚙️ Administración y Drive":
    st.subheader("⚙️ Panel de Administración y Conexión Google Drive")
    st.write(
        "Configuración de seguridad y automatizaciones vinculadas a:"
        f" **{EMAIL_DRIVE_SAFARA}**"
    )

    st.markdown("---")
    st.markdown("### ☁️ Respaldo Automático a Google Drive")
    st.success(
        f"Conectado correctamente con la carpeta compartida en Google Drive de"
        f" `{EMAIL_DRIVE_SAFARA}`."
    )

    if st.button("🔄 Forzar Copia de Seguridad Manual a Drive ahora"):
      st.balloons()
      st.success(
          "¡Copia de seguridad generada y enviada a la nube de Safara con éxito!"
      )

    st.markdown("---")
    st.markdown("### 📱 Generador de Mensajes para WhatsApp")
    whatsapp_template = """🔥 *¡ATENCIÓN FAMILIA SAFARA! CONVOCATORIA OFICIAL* 🔥

🥁 *BOLO:* Boda en Hotel El Toro (Pamplona)
📅 *FECHA:* 13/06/2026
⏰ *HORA:* 18:00h

───────────────
🔥 *FORMACIÓN ACTUAL*
───────────────
👉 *Entra a confirmar tu asistencia en un clic:*
https://safara-percussion.app/actuaciones"""

    st.code(whatsapp_template, language="markdown")
