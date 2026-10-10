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
ADMIN_PASSWORD = (
    "safara2026"  # Contraseña para acceder al panel de administración
)

# Estética Dark-Fire (CSS personalizado avanzado)
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    .stButton>button { background-color: #ff4b4b; color: white; border-radius: 8px; font-weight: bold; border: none; width: 100%; }
    .stButton>button:hover { background-color: #ff2121; color: white; }
    .metric-card { background-color: #1a1c23; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; }
    .welcome-banner { text-align: center; padding: 30px; background: linear-gradient(135deg, #1a1c23 0%, #2d1313 100%); border-radius: 15px; border: 2px solid #ff4b4b; margin-bottom: 25px; }
    .logo-img { display: block; margin-left: auto; margin-right: auto; width: 180px; }
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

# --- PANTALLA DE BIENVENIDA / ONBOARDING ---
if not st.session_state["usuario_actual"]:
  # Carga de logo PNG centrado si existe
  if os.path.exists("Logo delante PNG.png"):
    st.image("Logo delante PNG.png", width=180, use_container_width=False)
  elif os.path.exists("Logo detrás PNG.png"):
    st.image("Logo detrás PNG.png", width=180, use_container_width=False)
  else:
    st.markdown(
        "<h1 style='text-align: center; font-size: 80px;'>🔥</h1>",
        unsafe_allow_html=True,
    )

  st.markdown(
      f"""
    <div class="welcome-banner">
        <h1 style="color: #ff4b4b; margin-bottom: 5px;">SAFARA PERCUSSION</h1>
        <p style="font-size: 1.2em; font-weight: bold;">¡Ritmo, fuego y pura energía en la calle!</p>
        <p style="font-size: 0.9em; color: #bbbbbb;">
            Asociación Cultural Nº 9.514 (Gobierno de Navarra) • {dias_activos} días haciendo retumbar Navarra
        </p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.subheader("🥁 Acceso a la App de Safara")
    tipo_acceso = st.radio(
        "¿Cómo quieres acceder?",
        ["Ya estoy registrado", "Soy nuevo / Registrarme"],
    )

    if tipo_acceso == "Soy nuevo / Registrarme":
      with st.form("form_nuevo_registro"):
        nombre_reg = st.text_input("Nombre y Apellidos")
        tel_reg = st.text_input("Teléfono Móvil")
        email_reg = st.text_input("Correo Electrónico")

        st.write("**Fecha de Nacimiento (Día / Mes / Año):**")
        col_d, col_m, col_a = st.columns(3)
        with col_d:
          dia_nac = st.number_input("Día", 1, 31, 15)
        with col_m:
          mes_nac = st.number_input("Mes", 1, 12, 6)
        with col_a:
          anio_nac = st.number_input("Año", 1950, 2018, 1998)

        instrumento_reg = st.selectbox(
            "Selecciona tu instrumento principal",
            [
                "Repenike",
                "Caja",
                "Surdo",
                "Surdo de contra",
                "Ganza (bailarinas)",
            ],
        )

        st.markdown("---")
        with st.expander(
            "📄 Ver Cláusula de Protección de Datos y Derechos de Imagen (RGPD"
            " 2026 / LO 1/1982)"
        ):
          st.caption(
              "De conformidad con el RGPD (UE 2016/679), la LOPDGDD 3/2018 y la"
              " Ley Orgánica 1/1982 sobre el Derecho al Honor, Intimidad y"
              " Propia Imagen, los datos recogidos serán tratados por SAFARA"
              " PERCUSSION (Reg. Navarra Nº 9.514) con la finalidad de gestionar"
              " la pertenencia a la asociación, la organización de ensayos y"
              " actuaciones, y la difusión comercial o promocional del grupo."
              " Al registrarte, autorizas expresamente la captación y uso de"
              " tu imagen/voz en actuaciones para ser publicadas en la Web"
              " oficial, TikTok, Instagram, YouTube y materiales gráficos del"
              " grupo. Puedes revocar tu consentimiento en cualquier momento"
              " escribiendo a safarapercussion@gmail.com."
          )

        acepta_rgpd = st.checkbox(
            "Acepto la Política de Protección de Datos y autorizo el uso de"
            " derechos de imagen para TikTok, Instagram y difusiones oficiales."
        )

        btn_reg = st.form_submit_button("¡A QUEMAR LA CALLE! 🔥")

        if btn_reg:
          if not (nombre_reg and tel_reg and email_reg):
            st.error("Por favor, rellena todos los campos obligatorios.")
          elif not acepta_rgpd:
            st.warning(
                "Debes aceptar la casilla de Protección de Datos e Imagen para"
                " poder registrarte."
            )
          else:
            fecha_nac_str = f"{dia_nac:02d}/{mes_nac:02d}/{anio_nac}"
            nuevo_miembro = {
                "id": len(st.session_state["usuarios"]) + 1,
                "nombre": nombre_reg,
                "telefono": tel_reg,
                "email": email_reg,
                "fnac": fecha_nac_str,
                "instrumento": instrumento_reg,
                "rgpd_aceptado": True,
                "fecha_registro": datetime.date.today().strftime("%d/%m/%Y"),
            }
            st.session_state["usuarios"].append(nuevo_miembro)
            st.session_state["usuario_actual"] = nombre_reg
            st.success(f"¡Bienvenido a la familia, {nombre_reg}! 🔥")
            st.rerun()

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
  # --- APLICACIÓN PRINCIPAL (POST-REGISTRO / LOGIN) ---
  st.sidebar.markdown(
      f"👤 **Conectado como:**\n`{st.session_state['usuario_actual']}`"
  )
  if st.sidebar.button("Cerrar Sesión"):
    st.session_state["usuario_actual"] = None
    st.rerun()

  menu = st.sidebar.selectbox(
      "Navegación",
      [
          "🏠 Inicio & Tablón",
          "🥁 Actuaciones & Votaciones",
          "💶 Control de Gastos",
          "🔒 Área de Administración",
      ],
  )

  # --- MÓDULO 1: INICIO & TABLÓN ---
  if menu == "🏠 Inicio & Tablón":
    st.subheader(f"👋 ¡A tope, {st.session_state['usuario_actual']}!")
    st.write(
        "Bienvenido/a al panel oficial de Safara Percussion. Aquí tienes las"
        " novedades del grupo y los próximos compromisos."
    )

    st.markdown(
        """
        <div class="metric-card">
            <h3>🔥 Próximo Ensayo General</h3>
            <p>Mantén las baquetas preparadas. Revisa la sección de actuaciones para confirmar tu presencia en los próximos bolos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  # --- MÓDULO 2: ACTUACIONES & VOTACIONES ---
  elif menu == "🥁 Actuaciones & Votaciones":
    st.subheader("🥁 Próximas Actuaciones y Votaciones")

    for act in st.session_state["actuaciones"]:
      st.markdown(
          f"""
          <div class="metric-card">
              <h3>🔥 {act['titulo']}</h3>
              <p><b>Fecha:</b> {act['fecha'].strftime('%d/%m/%Y')} • <b>Hora:</b> {act['hora']} • <b>Lugar:</b> {act['lugar']}</p>
          </div>
          """,
          unsafe_allow_html=True,
      )

      dias_restantes = (act["fecha"] - hoy).days
      if dias_restantes > 0:
        st.warning(f"⏳ ¡Faltan **{dias_restantes} días** para este bolo!")
      elif dias_restantes == 0:
        st.error("🚨 ¡El bolo es HOY! ¡A darlo todo!")

      st.markdown("#### Vota tu asistencia:")
      col_v1, col_v2 = st.columns(2)

      with col_v1:
        if st.button("De una! A arder en el infierno! 🔥", key=id(act)):
          act["votos"][st.session_state["usuario_actual"]] = (
              "De una! A arder en el infierno! 🔥"
          )
          st.success("¡Voto registrado con éxito!")

      with col_v2:
        if st.button("No puedo! Fomo máximo! 😭", key=id(act) + 1):
          act["votos"][st.session_state["usuario_actual"]] = (
              "No puedo! Fomo máximo! 😭"
          )
          st.warning("¡Voto registrado!")

      if act["votos"]:
        st.markdown("##### 📋 Recuento de Asistencia:")
        for u, v in act["votos"].items():
          st.write(f"- **{u}**: {v}")

  # --- MÓDULO 3: CONTROL DE GASTOS ---
  elif menu == "💶 Control de Gastos":
    st.subheader("💶 Gestión Económica de la Asociación")

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
        st.success("¡Gasto registrado correctamente!")

    st.markdown("### 📊 Registro Contable")
    if not st.session_state["gastos"].empty:
      st.dataframe(st.session_state["gastos"], use_container_width=True)
      csv_gastos = (
          st.session_state["gastos"].to_csv(index=False).encode("utf-8")
      )
      st.download_button(
          label="📥 Descargar Libro de Gastos Oficial (Excel/CSV para Hacienda)",
          data=csv_gastos,
          file_name=f"SAFARA_GASTOS_HACIENDA_{datetime.date.today()}.csv",
          mime="text/csv",
      )

  # --- MÓDULO 4: ÁREA DE ADMINISTRACIÓN (PROTEGIDA) ---
  elif menu == "🔒 Área de Administración":
    st.subheader("🔒 Gestión Interna de la Directiva")

    pass_input = st.text_input(
        "Introduce la Contraseña de Administrador", type="password"
    )

    if pass_input == ADMIN_PASSWORD:
      st.success("✅ Acceso autorizado como Administrador")

      st.markdown("### 👥 Listado de Miembros y Consentimientos RGPD")
      if st.session_state["usuarios"]:
        df_users = pd.DataFrame(st.session_state["usuarios"])
        st.dataframe(df_users, use_container_width=True)

        # Exportación legal a Excel/CSV por si la solicita Hacienda o Administración
        csv_users = df_users.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Exportar Registro Oficial de Socios (Excel/CSV)",
            data=csv_users,
            file_name=f"SAFARA_REGISTRO_SOCIOS_{datetime.date.today()}.csv",
            mime="text/csv",
        )

        st.markdown("---")
        st.markdown("### 🗑️ Depuración de Usuarios Duplicados")
        nombres_miembros = [u["nombre"] for u in st.session_state["usuarios"]]
        usuario_a_borrar = st.selectbox(
            "Selecciona usuario para eliminar o corregir duplicado:",
            nombres_miembros,
        )

        if st.button("❌ Eliminar Usuario Seleccionado"):
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
        st.info("No hay miembros registrados actualmente.")

    elif pass_input != "":
      st.error("❌ Contraseña incorrecta.")
