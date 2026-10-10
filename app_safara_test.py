import datetime
import os
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Safara Percussion",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Constantes de la asociación
FECHA_FUNDACION = datetime.date(2023, 4, 23)
ADMIN_PASSWORD = (
    "safara2026"  # Contraseña para acceder al panel de administración
)

# CSS Elegante Dark-Fire Premium (Centrado y Legibilidad Móvil)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0c10;
        color: #f0f0f0;
    }
    
    /* Contenedor y cabecera central */
    .brand-container {
        text-align: center;
        padding: 10px 0px 15px 0px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .brand-subtitle {
        color: #ff4b4b;
        font-size: 1.2em;
        font-weight: 700;
        letter-spacing: 2px;
        margin-top: 8px;
        margin-bottom: 2px;
        text-shadow: 0 0 12px rgba(255, 75, 75, 0.6);
        text-align: center;
    }
    
    .brand-tagline {
        color: #8a8d93;
        font-size: 0.85em;
        text-align: center;
    }
    
    .custom-card {
        background-color: #15181e;
        border: 1px solid #2b2e36;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
        text-align: center;
    }
    
    /* Botones principales súper visibles */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(135deg, #e63946 0%, #b71c1c 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 1.05em !important;
        border: none !important;
        padding: 14px 20px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(230, 57, 70, 0.4) !important;
        text-transform: uppercase !important;
    }
    
    .stButton>button:hover, div[data-testid="stFormSubmitButton"]>button:hover {
        background: linear-gradient(135deg, #ff4d6d 0%, #e63946 100%) !important;
        color: #ffffff !important;
    }
    
    /* Textos e inputs */
    label, .stRadio p {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
    }
    
    video {
        border-radius: 14px;
        border: 1px solid #ff4b4b;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Inicialización del estado de sesión
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

# --- CABECERA Y LOGO CENTRADO ---
st.markdown('<div class="brand-container">', unsafe_allow_html=True)

if os.path.exists("Logo detrás PNG.png"):
  st.image("Logo detrás PNG.png", width=220)
elif os.path.exists("Logo delante PNG.png"):
  st.image("Logo delante PNG.png", width=220)
else:
  st.markdown(
      "<h1 style='text-align: center; color: #ff4b4b;'>SAFARA PERCUSSION</h1>",
      unsafe_allow_html=True,
  )

st.markdown(
    """
    <div class="brand-subtitle">RITMO • FUEGO • ENERGÍA</div>
    <div class="brand-tagline">Asociación Cultural Nº 9.514 — Gobierno de Navarra</div>
</div>
""",
    unsafe_allow_html=True,
)

# --- FLIUJO DE ONBOARDING / ACCESO ---
if not st.session_state["usuario_actual"]:

  # Vídeo de entrada de San Fermín
  if os.path.exists("IMG_8260.mov"):
    st.video("IMG_8260.mov", loop=True, autoplay=True, muted=True)

  st.markdown("---")
  st.markdown(
      "<h3 style='text-align: center;'>Acceso a la Plataforma</h3>",
      unsafe_allow_html=True,
  )

  opcion_acceso = st.radio(
      "Selecciona tu opción:",
      ["Acceder a mi cuenta", "Registrarme como nuevo miembro"],
      horizontal=True,
  )

  if opcion_acceso == "Registrarme como nuevo miembro":
    st.markdown("#### Registro de Nuevo Miembro")

    with st.form("form_registro_elegante"):
      nombre = st.text_input("Nombre y Apellidos *")
      telefono = st.text_input("Teléfono Móvil *")
      email = st.text_input("Correo Electrónico *")

      st.markdown("**Fecha de Nacimiento:**")
      col_d, col_m, col_a = st.columns(3)
      with col_d:
        dia_nac = st.number_input("Día", 1, 31, 15)
      with col_m:
        mes_nac = st.number_input("Mes", 1, 12, 6)
      with col_a:
        anio_nac = st.number_input("Año", 1950, 2018, 1998)

      instrumento = st.selectbox(
          "Instrumento principal",
          ["Repenike", "Caja", "Surdo", "Surdo de contra", "Ganza (bailarinas)"],
      )

      st.markdown("---")
      with st.expander(
          "Ver Cláusula Legal de Protección de Datos y Derechos de Imagen"
      ):
        st.caption(
            "De conformidad con el RGPD (UE 2016/679), la LOPDGDD 3/2018 y la"
            " LO 1/1982 sobre Protección del Derecho al Honor e Imagen, los"
            " datos recabados por SAFARA PERCUSSION serán utilizados para la"
            " gestión interna del grupo. Al registrarte, autorizas"
            " expresamente la difusión de imágenes/vídeos de actuaciones en"
            " TikTok, Instagram, Youtube y la web oficial del grupo. Puedes"
            " revocar tu consentimiento en cualquier momento mediante escrito"
            " a safarapercussion@gmail.com."
        )

      acepta_rgpd = st.checkbox(
          "Acepto la política de privacidad e imagen (TikTok, Instagram y web) *"
      )

      btn_reg = st.form_submit_button("¡UNIRME AL GRUPO!")

      if btn_reg:
        if not (nombre and telefono and email):
          st.error("Por favor, completa todos los campos obligatorios.")
        elif not acepta_rgpd:
          st.warning(
              "Debes aceptar la casilla de Protección de Datos para continuar."
          )
        else:
          fecha_nac_str = f"{dia_nac:02d}/{mes_nac:02d}/{anio_nac}"
          nuevo_miembro = {
              "id": len(st.session_state["usuarios"]) + 1,
              "nombre": nombre,
              "telefono": telefono,
              "email": email,
              "fnac": fecha_nac_str,
              "instrumento": instrumento,
              "rgpd_aceptado": True,
              "fecha_registro": datetime.date.today().strftime("%d/%m/%Y"),
          }
          st.session_state["usuarios"].append(nuevo_miembro)
          st.session_state["usuario_actual"] = nombre
          st.rerun()

  else:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    nombre_login = st.text_input("Nombre y Apellidos registrados")
    if st.button("ACCEDER A LA PLATAFORMA"):
      if nombre_login:
        st.session_state["usuario_actual"] = nombre_login
        st.rerun()
      else:
        st.error("Por favor, introduce tu nombre registrado.")
    st.markdown("</div>", unsafe_allow_html=True)

else:
  # --- PANTALLA PRINCIPAL INTERNA (POST-REGISTRO Y LOGIN) ---
  st.markdown(
      f"<h2 style='text-align: center; color: #ff4b4b;'>¡A tope,"
      f" {st.session_state['usuario_actual']}! 🔥</h2>",
      unsafe_allow_html=True,
  )

  # Botón de cerrar sesión siempre visible arriba
  col_logout1, col_logout2, col_logout3 = st.columns([1, 2, 1])
  with col_logout2:
    if st.button("Cerrar Sesión"):
      st.session_state["usuario_actual"] = None
      st.rerun()

  st.markdown("---")

  # Selector de navegación en pantalla
  seccion = st.selectbox(
      "📌 Selecciona la sección que quieres consultar:",
      [
          "🏠 Muro Principal & Novedades",
          "🥁 Actuaciones & Votaciones",
          "💶 Control de Gastos",
          "🔒 Área de Administración",
      ],
  )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- SECCIÓN 1: MURO PRINCIPAL & NOVEDADES ---
  if seccion == "🏠 Muro Principal & Novedades":
    if os.path.exists("IMG_8260.mov"):
      st.video("IMG_8260.mov", loop=True, autoplay=True, muted=True)

    st.markdown(
        f"""
        <div class="custom-card">
            <h3 style="color: #ff4b4b; margin-top:0;">🔥 Muro del Grupo</h3>
            <p style="font-size: 1.1em;">Llevamos <b>{dias_activos} días</b> haciendo retumbar las calles.</p>
            <p>Utiliza el desplegable superior para revisar los próximos bolos, confirmar tu asistencia o acceder a la gestión interna.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  # --- SECCIÓN 2: ACTUACIONES & VOTACIONES ---
  elif seccion == "🥁 Actuaciones & Votaciones":
    st.markdown("### 🥁 Próximas Actuaciones")

    for act in st.session_state["actuaciones"]:
      st.markdown(
          f"""
          <div class="custom-card">
              <h4 style="color: #ff4b4b; margin-top:0;">{act['titulo']}</h4>
              <p>📅 <b>Fecha:</b> {act['fecha'].strftime('%d/%m/%Y')}<br>
              ⏰ <b>Hora:</b> {act['hora']}<br>
              📍 <b>Lugar:</b> {act['lugar']}</p>
          </div>
          """,
          unsafe_allow_html=True,
      )

      dias_restantes = (act["fecha"] - hoy).days
      if dias_restantes > 0:
        st.info(f"Faltan **{dias_restantes} días** para este evento.")
      elif dias_restantes == 0:
        st.error("¡El bolo es hoy!")

      st.markdown("**Confirma tu asistencia:**")
      col_v1, col_v2 = st.columns(2)

      with col_v1:
        if st.button(
            "De una! A arder en el infierno!", key=f"voto_si_{act['id']}"
        ):
          act["votos"][st.session_state["usuario_actual"]] = (
              "De una! A arder en el infierno!"
          )
          st.success("¡Asistencia confirmada!")

      with col_v2:
        if st.button("No puedo! Fomo máximo!", key=f"voto_no_{act['id']}"):
          act["votos"][st.session_state["usuario_actual"]] = (
              "No puedo! Fomo máximo!"
          )
          st.warning("Ausencia registrada.")

      if act["votos"]:
        with st.expander("Ver estado de respuestas del grupo"):
          for u, v in act["votos"].items():
            st.write(f"- **{u}**: {v}")

  # --- SECCIÓN 3: CONTROL DE GASTOS ---
  elif seccion == "💶 Control de Gastos":
    st.markdown("### 💶 Gestión Económica")

    with st.form("form_gasto"):
      col1, col2 = st.columns(2)
      with col1:
        f_gasto = st.date_input("Fecha")
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
        nota = st.text_input("Concepto / Nota")
      btn_add_gasto = st.form_submit_button("Guardar Gasto")

      if btn_add_gasto:
        nuevo_gasto = pd.DataFrame(
            [{
                "Fecha": f_gasto.strftime("%d/%m/%Y"),
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
        st.success("¡Gasto guardado con éxito!")

    if not st.session_state["gastos"].empty:
      st.markdown("### Contabilidad Registrada")
      st.dataframe(st.session_state["gastos"], use_container_width=True)
      csv_gastos = (
          st.session_state["gastos"].to_csv(index=False).encode("utf-8")
      )
      st.download_button(
          label="Descargar Libro de Gastos (Excel/CSV para Hacienda)",
          data=csv_gastos,
          file_name=f"SAFARA_GASTOS_{datetime.date.today()}.csv",
          mime="text/csv",
      )

  # --- SECCIÓN 4: ÁREA DE ADMINISTRACIÓN (PROTEGIDA) ---
  elif seccion == "🔒 Área de Administración":
    st.markdown("### 🔒 Gestión de Administración")

    pass_input = st.text_input("Contraseña de Administrador", type="password")

    if pass_input == ADMIN_PASSWORD:
      st.success("Acceso autorizado como Administrador")

      st.markdown("#### Listado Oficial de Socios y RGPD")
      if st.session_state["usuarios"]:
        df_users = pd.DataFrame(st.session_state["usuarios"])
        st.dataframe(df_users, use_container_width=True)

        csv_users = df_users.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Exportar Registro Oficial de Socios (Excel/CSV)",
            data=csv_users,
            file_name=f"SAFARA_SOCIOS_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("#### Depuración de Usuarios Duplicados")
        nombres_miembros = [u["nombre"] for u in st.session_state["usuarios"]]
        usuario_a_borrar = st.selectbox(
            "Seleccionar usuario para eliminar:", nombres_miembros
        )

        if st.button("Eliminar Usuario Seleccionado"):
          st.session_state["usuarios"] = [
              u
              for u in st.session_state["usuarios"]
              if u["nombre"] != usuario_a_borrar
          ]
          st.success(
              f"Usuario '{usuario_a_borrar}' eliminado correctamente del"
              " registro."
          )
          st.rerun()
      else:
        st.info("No hay miembros registrados todavía.")

    elif pass_input != "":
      st.error("Contraseña incorrecta.")
