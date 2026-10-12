import streamlit as st
import pandas as pd
import datetime
import os
import base64

# ==========================================
# CONFIGURACIÓN DE PÁGINA (MOBILE FIRST)
# ==========================================
st.set_page_config(
    page_title="Safara Percussion • App Oficial v2.1 LITE",
    page_icon="🥁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# GESTIÓN DE SESIÓN Y ESTADOS
# ==========================================
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = ""
if "instrumento_usuario" not in st.session_state:
    st.session_state.instrumento_usuario = "Surdo"
if "voto_ensayo" not in st.session_state:
    st.session_state.voto_ensayo = None
if "voto_cena" not in st.session_state:
    st.session_state.voto_cena = None

# Base de datos completa de Safarers
USUARIOS_DB = {
    "Diego": {"pin": "1234", "instrumento": "Surdo"},
    "Resano": {"pin": "5678", "instrumento": "Repenike"},
    "Rezusta": {"pin": "9012", "instrumento": "Caja"},
    "Roslana": {"pin": "3456", "instrumento": "Bailarina"},
    "Alazne": {"pin": "1111", "instrumento": "Surdo de Contra"},
    "Andres": {"pin": "2222", "instrumento": "Repenike"},
    "Lucia": {"pin": "3333", "instrumento": "Caja"},
    "Naia": {"pin": "4444", "instrumento": "Bailarina"}
}

# ==========================================
# ESTILOS CSS - PANTALLA SPARTA VS DEEP BLACK
# ==========================================
def aplicar_estilos():
    bg_image_css = ""
    # Cargamos la foto en blanco y negro (IMG_0753.jpeg) para el fondo del login[span_1](start_span)[span_1](end_span)
    if os.path.exists("IMG_0753.jpeg"):
        with open("IMG_0753.jpeg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            bg_image_css = f"""
            .stApp {{
                background: linear-gradient(rgba(0, 0, 0, 0.78), rgba(0, 0, 0, 0.90)), url('data:image/jpeg;base64,{encoded_string}');
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            """
    else:
        bg_image_css = """
        .stApp {
            background-color: #080808;
        }
        """

    if not st.session_state.usuario_autenticado:
        # PANTALLA DE ACCESO ESTILO SPARTA (Con la foto JPG de fondo)
        css = f"""
        <style>
        {bg_image_css}
        
        .sparta-logo-container {{
            text-align: center;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
        }}
        .sparta-circle-logo {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            border: 3px solid rgba(231, 76, 60, 0.9);
            box-shadow: 0 0 30px rgba(231, 76, 60, 0.6);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(10px);
        }}
        .sparta-title {{
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: 3px;
            margin-top: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.9);
        }}
        .sparta-subtitle {{
            color: #FF8C00;
            font-size: 0.85rem;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}
        .glass-card {{
            background: rgba(15, 15, 15, 0.82);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        }}
        .stButton>button {{
            background: linear-gradient(135deg, #FF4500 0%, #CC3300 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: bold !important;
            letter-spacing: 1px !important;
            width: 100% !important;
            padding: 12px !important;
            box-shadow: 0 4px 15px rgba(255, 69, 0, 0.4) !important;
        }}
        </style>
        """
    else:
        # INTERIOR DE LA APP (DEEP BLACK MOOD - SIN FOTO DE FONDO)
        css = """
        <style>
        .stApp {
            background-color: #080808 !important;
            color: #E0E0E0 !important;
            background-image: none !important;
        }
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
        }
        .user-greeting {
            color: #FFFFFF;
            font-weight: 700;
            font-size: 1.1rem;
        }
        .date-sub {
            color: #888888;
            font-size: 0.75rem;
        }
        .logout-btn button {
            background: transparent !important;
            color: #888888 !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 20px !important;
            font-size: 0.8rem !important;
            padding: 4px 12px !important;
            box-shadow: none !important;
        }
        .logout-btn button:hover {
            color: #FF4500 !important;
            border-color: #FF4500 !important;
        }
        .ensayo-card {
            background: #111111;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 140, 0, 0.3);
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            margin-bottom: 25px;
        }
        .badge-quorum {
            background: rgba(255, 140, 0, 0.15);
            color: #FF8C00;
            border: 1px solid #FF8C00;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }
        .badge-confirmado {
            background: rgba(46, 204, 113, 0.15);
            color: #2ECC71;
            border: 1px solid #2ECC71;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }
        /* BOTONES DE FUEGO 3D EN LÍNEA CON RELIEVE */
        .btn-fire-green button {
            background: linear-gradient(145deg, #1e3c2b, #14281d) !important;
            color: #2ECC71 !important;
            border: 1px solid #2ECC71 !important;
            border-radius: 12px !important;
            font-weight: bold !important;
            padding: 12px 15px !important;
            width: 100% !important;
            box-shadow: 0 0 15px rgba(46, 204, 113, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        .btn-fire-green button:active {
            transform: scale(0.95) !important;
        }
        .btn-fire-red button {
            background: linear-gradient(145deg, #3c1e1e, #281414) !important;
            color: #E74C3C !important;
            border: 1px solid #E74C3C !important;
            border-radius: 12px !important;
            font-weight: bold !important;
            padding: 12px 15px !important;
            width: 100% !important;
            box-shadow: 0 0 15px rgba(231, 76, 60, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        .btn-fire-red button:active {
            transform: scale(0.95) !important;
        }
        .stSelectbox label, .stTextInput label, .stFileUploader label, .stNumberInput label {
            color: #FFFFFF !important;
            font-weight: bold !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #181818 !important;
            color: white !important;
            border-color: #333333 !important;
        }
        div[data-testid="stFileUploader"] {
            background-color: #121212 !important;
            border: 1px dashed #444444 !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
        div[data-testid="stFileUploader"] span {
            color: #FFFFFF !important;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

aplicar_estilos()

# ==========================================
# VISTA 1: ACCESO Y REGISTRO (SPARTA)
# ==========================================
if not st.session_state.usuario_autenticado:
    st.markdown("""
        <div class="sparta-logo-container">
            <div class="sparta-circle-logo">
                <span style="font-size: 2.8rem; color: #E74C3C; font-weight:900;">🔥</span>
            </div>
            <div class="sparta-title">SAFARA</div>
            <div class="sparta-subtitle">PERCUSSION • V2.1 LITE</div>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_registro = st.tabs(["ACCESO SAFARERS", "UNIRSE AL GRUPO"])

    with tab_login:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        usuario = st.selectbox("Safarer", list(USUARIOS_DB.keys()))
        pin = st.text_input("PIN de Acceso", type="password")
        
        if st.button("ENTRAR EN SAFARA"):
            if USUARIOS_DB[usuario]["pin"] == pin:
                st.session_state.usuario_autenticado = True
                st.session_state.nombre_usuario = usuario
                st.session_state.instrumento_usuario = USUARIOS_DB[usuario]["instrumento"]
                st.rerun()
            else:
                st.error("PIN incorrecto. Revisa e inténtalo de nuevo.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_registro:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.text_input("Nombre Completo")
        st.text_input("Teléfono de Contacto")
        st.selectbox("Instrumento Principal", ["Surdo", "Repenike", "Caja", "Surdo de Contra", "Bailarina"])
        if st.button("SOLICITAR ALTA"):
            st.success("Solicitud enviada a la junta directiva correctamente.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# VISTA 2: APLICACIÓN INTERIOR (DEEP BLACK)
# ==========================================
else:
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.markdown(f"""
            <div class="user-greeting">¡Hola, {st.session_state.nombre_usuario}!</div>
            <div class="date-sub">{datetime.datetime.now().strftime('%A, %d/%m/%Y')}</div>
        """, unsafe_allow_html=True)
    with col_head2:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("⏻ Salir"):
            st.session_state.usuario_autenticado = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Pestañas Principales del Sistema
    tab_movidas, tab_agenda, tab_finanzas, tab_admin = st.tabs([
        "Nuestras Movidas", "Agenda & Bolos", "FINANZAS", "ÁREA DE ADMINISTRACIÓN"
    ])

    # ------------------------------------------
    # TAB 1: NUESTRAS MOVIDAS
    # ------------------------------------------
    with tab_movidas:
        st.markdown("""
            <div class="ensayo-card">
                <div class="badge-quorum">PENDIENTE • FALTAN SAFARERS</div>
                <h2 style="color:white; margin:0; font-weight:800;">PRÓXIMO ENSAYO</h2>
                <p style="color:#BBBBBB; margin-top:5px;">Fecha: 16/10/2026 (19:00h - 19:30h)<br>Ubicación: Gaztetxe de Zizur</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='text-align:center; color:white;'>¿Le damos caña este viernes?</h4>", unsafe_allow_html=True)

        # Votación Ensayo en Línea (Verde / Rojo)
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown('<div class="btn-fire-green">', unsafe_allow_html=True)
            if st.button("🟢 ¡A tope, se le da!"):
                st.session_state.voto_ensayo = "SI"
                st.toast("¡Vaaaaamosss! ¡Ya hay un voto más! Esta actuación la sacamos fijo!")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_v2:
            st.markdown('<div class="btn-fire-red">', unsafe_allow_html=True)
            if st.button("🔴 No puedo, ¡tengo lío!"):
                st.session_state.voto_ensayo = "NO"
            st.markdown('</div>', unsafe_allow_html=True)

        st.progress(0.66)
        st.caption("8 Safarers han confirmado asistencia")
        st.markdown("**Desglose por sección:** Repenikes: 2 | Cajas: 2 | Surdos: 3 | Contra: 1 | Bailarinas: 0")

        st.divider()

        # Votación Cena en Línea (Verde / Rojo)
        st.markdown("<h4 style='text-align:center; color:white;'>CENA POST ENSAYO • ¿Hoy se cena después de darle?</h4>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown('<div class="btn-fire-green">', unsafe_allow_html=True)
            if st.button("🟢 De una, a cenar..."):
                st.session_state.voto_cena = "SI"
                st.toast("¡Cena confirmada! Guardando sitio en la mesa...")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_c2:
            st.markdown('<div class="btn-fire-red">', unsafe_allow_html=True)
            if st.button("🔴 Hoy me recojo pronto"):
                st.session_state.voto_cena = "NO"
            st.markdown('</div>', unsafe_allow_html=True)

        st.caption("5 Safarers se quedan a cenar")

        st.divider()

        # Redes Sociales Top
        st.markdown("<h4 style='color:white;'>SAFARA EN REDES SOCIALES</h4>", unsafe_allow_html=True)
        col_ig, col_tk = st.columns(2)
        with col_ig:
            st.info("📷 **Instagram Top**\nCampaña Captación (Dic 2024)\n149 Me Gusta • 66 Seguidores")
        with col_tk:
            st.info("🎵 **TikTok Top**\nRitmo On Fire - Directo\n+10K Visualizaciones")

    # ------------------------------------------
    # TAB 2: AGENDA & BOLOS
    # ------------------------------------------
    with tab_agenda:
        st.markdown("<h4 style='color:#FF8C00;'>🟡 BOLOS PENDIENTES DE CONFIRMACIÓN</h4>", unsafe_allow_html=True)
        st.write("• **Halloween Ocasiones Especiales** - 31/10/2026")
        
        st.markdown("<h4 style='color:#2ECC71;'>🟢 PRÓXIMAS ACTUACIONES CONFIRMADAS</h4>", unsafe_allow_html=True)
        st.write("• **07/11/2026** - Boda Amaia (Iruña Park) - 19:00h")
        st.write("• **14/02/2026** - Carnavales Apyma (Cárcar)")

        st.divider()

        st.markdown("<h4 style='color:white;'>EVOLUCIÓN DE ACTUACIONES SAFARA</h4>", unsafe_allow_html=True)
        col_y1, col_y2, col_y3 = st.columns(3)
        with col_y1:
            st.metric("★ 2026 ★", "14 bolos", "Año Actual")
        with col_y2:
            st.metric("2025", "21 bolos")
        with col_y3:
            st.metric("2024", "5 bolos")

    # ------------------------------------------
    # TAB 3: FINANZAS
    # ------------------------------------------
    with tab_finanzas:
        st.markdown("<h3 style='color:white;'>FINANZAS</h3>", unsafe_allow_html=True)
        st.caption("Fondo Común: 1.250,50 € | Pendiente: 0,00 €")

        st.markdown("#### Adjuntar Nuevo Gasto")
        categoria = st.selectbox("Categoría de Gasto", ["Parking", "Gasolina", "Material / Reparación", "Comida / Bebida", "Otros"])
        importe = st.number_input("Importe (€)", min_value=0.0, step=0.50, format="%.2f")
        fecha_gasto = st.date_input("Fecha", datetime.date.today())
        ticket_file = st.file_uploader("Adjuntar Ticket (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])

        if st.button("Guardar y Enviar Gasto"):
            if ticket_file and importe > 0:
                fecha_str = fecha_gasto.strftime("%d/%m/%Y")
                fecha_fich = fecha_gasto.strftime("%d%m%Y")
                ext = ticket_file.name.split(".")[-1]
                nombre_formateado = f"Gasto_001_{fecha_fich}_{st.session_state.nombre_usuario}_{importe:.2f}EUR.{ext}"
                st.success(f"Gasto registrado correctamente: {nombre_formateado}")
            else:
                st.warning("Adjunta el ticket y especifica un importe válido superior a 0.")

        st.divider()
        st.markdown("#### Exportación de Datos")
        if st.button("Exportar Gastos a Excel"):
            st.info("Archivo Excel generado con éxito. Importes formateados como XX,XX € e hipervínculos operativos.")

    # ------------------------------------------
    # TAB 4: ÁREA DE ADMINISTRACIÓN
    # ------------------------------------------
    with tab_admin:
        st.markdown("<h3 style='color:white;'>ÁREA DE ADMINISTRACIÓN</h3>", unsafe_allow_html=True)
        
        st.markdown("#### Listado de Safarers y PINs de Acceso")
        df_socios = pd.DataFrame([
            {"Safarer": "Diego", "Instrumento": "Surdo", "PIN": "1234"},
            {"Safarer": "Resano", "Instrumento": "Repenike", "PIN": "5678"},
            {"Safarer": "Rezusta", "Instrumento": "Caja", "PIN": "9012"},
            {"Safarer": "Roslana", "Instrumento": "Bailarina", "PIN": "3456"},
            {"Safarer": "Alazne", "Instrumento": "Surdo de Contra", "PIN": "1111"},
            {"Safarer": "Andres", "Instrumento": "Repenike", "PIN": "2222"},
            {"Safarer": "Lucia", "Instrumento": "Caja", "PIN": "3333"},
            {"Safarer": "Naia", "Instrumento": "Bailarina", "PIN": "4444"},
        ])
        st.dataframe(df_socios, use_container_width=True)

        if st.button("Copiar PIN de Usuario"):
            st.toast("PIN copiado al portapapeles con éxito.")
