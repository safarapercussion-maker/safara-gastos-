import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Safara Percussion - Gastos", page_icon="🔥", layout="centered")

# Estilos CSS modernos 2026: Animaciones, fondo oscuro dinámico, efectos de brillo y tipografía cuidada
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1a1a1a 0%, #0d0d0d 100%);
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .safara-hero {
        background: linear-gradient(135deg, #000000 0%, #222222 100%);
        padding: 25px;
        border-radius: 16px;
        border: 2px solid #FFD700;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.15);
        animation: fadeIn 0.8s ease-out;
        margin-bottom: 25px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000000;
        font-weight: 800;
        border-radius: 10px;
        border: none;
        width: 100%;
        padding: 0.75rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
        background: linear-gradient(135deg, #FFE44D 0%, #FFB733 100%);
    }
    
    div[data-baseweb="select"] > div, input {
        background-color: #1A1A1A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #333333 !important;
    }
    
    div.stMetric {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 215, 0, 0.2);
        padding: 15px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        animation: fadeIn 1s ease-out;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado dinámico con integración de logos (si están subidos en GitHub) o respaldo estético
col_logo1, col_logo2 = st.columns([1, 2])
with col_logo1:
    if os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center;'>🔥</h1>", unsafe_allow_html=True)

with col_logo2:
    if os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", use_container_width=True)
    else:
        st.markdown("""
            <div class="safara-hero" style="margin:0; padding:12px;">
                <h2 style="color: #FFD700; margin: 0; font-weight: 800; letter-spacing: 1px;">SAFARA PERCUSSION</h2>
                <p style="color: #AAAAAA; margin: 2px 0 0 0; font-size: 13px;">Financial Management 2026</p>
            </div>
        """, unsafe_allow_html=True)

st.divider()

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"

# Inicializar estados y base de datos
if 'gastos' not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        st.session_state.gastos = pd.read_excel(EXCEL_FILE)
    else:
        st.session_state.gastos = pd.DataFrame(columns=[
            "ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado"
        ])

if 'saldo_caja' not in st.session_state:
    st.session_state.saldo_caja = 1250.50

if 'admins' not in st.session_state:
    st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = []

# Selector de perfil activo
todos_los_miembros = st.session_state.admins + st.session_state.usuarios
usuario_actual = st.selectbox("👤 Selecciona tu perfil:", todos_los_miembros)

es_administrador = usuario_actual in st.session_state.admins

# Tarjetas de Métricas Principales con diseño moderno
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("🏦 Saldo Caja Rural", f"{st.session_state.saldo_caja:.2f} €")
with m2:
    total_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("💸 Gastos Totales", f"{total_gastos:.2f} €")
with m3:
    pendientes = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("⏳ Pendiente Reembolso", f"{pendientes:.2f} €")

st.divider()

# Panel exclusivo de administración (Solo para Admins: Cambiar saldo y añadir colaboradores)
if es_administrador:
    with st.expander("⚙️ Panel de Control (Restringido a Administradores)"):
        col_adm1, col_adm2 = st.columns(2)
        
        with col_adm1:
            st.subheader("Actualizar Caja Rural")
            nuevo_saldo = st.number_input("Nuevo saldo (€)", value=float(st.session_state.saldo_caja), min_value=0.0, step=10.0)
            if st.button("Guardar Saldo Banco"):
                st.session_state.saldo_caja = nuevo_saldo
                st.success("¡Saldo actualizado correctamente!")
                st.rerun()

        with col_adm2:
            st.subheader("Añadir Colaborador")
            nuevo_colaborador = st.text_input("Nombre del nuevo usuario")
            if st.button("Registrar Usuario"):
                if nuevo_colaborador and nuevo_colaborador not in st.session_state.usuarios and nuevo_colaborador not in st.session_state.admins:
                    st.session_state.usuarios.append(nuevo_colaborador)
                    st.success(f"¡{nuevo_colaborador} añadido con éxito!")
                    st.rerun()
                else:
                    st.error("Nombre inválido o ya existente.")
        
        if st.session_state.usuarios:
            st.write("Colaboradores activos:", ", ".join(st.session_state.usuarios))

st.divider()

# Formulario dinámico para registrar gastos
st.markdown(f"### 📝 Registrar Nuevo Gasto <span style='font-size:14px; color:#FFD700;'>(Activo como: {usuario_actual})</span>", unsafe_allow_html=True)
st.write("Sube tu ticket o factura para solicitar el reembolso de forma instantánea.")

with st.form("form_gasto", clear_on_submit=True):
    concepto = st.text_input("Concepto / Comercio*", placeholder="Ej. Material percusión, Transporte...")
    importe = st.number_input("Importe (€)*", min_value=0.0, step=1.0, value=0.0)
    fecha = st.date_input("Fecha del gasto", datetime.date.today())
    fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])

    enviado = st.form_submit_button("Guardar y Enviar Gasto")

    if enviado:
        if not concepto or importe <= 0:
            st.error("Por favor, introduce un concepto y un importe mayor a 0.")
        else:
            nombre_fichero = ""
            if fichero is not None:
                nombre_fichero = f"{datetime.date.today()}_{usuario_actual}_{fichero.name}"
                ruta_destino = os.path.join(RECEIPTS_DIR, nombre_fichero)
                with open(ruta_destino, "wb") as f:
                    f.write(fichero.getbuffer())

            nuevo_id = len(st.session_state.gastos) + 1
            nuevo_registro = {
                "ID": nuevo_id,
                "Fecha": str(fecha),
                "Usuario": usuario_actual,
                "Concepto": concepto,
                "Importe": float(importe),
                "Fichero": nombre_fichero,
                "Reembolsado": False
