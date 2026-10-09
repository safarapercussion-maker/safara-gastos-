import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Safara Percussion - Gastos", page_icon="🔥", layout="centered")

# Estilos CSS modernos 2026: Alto contraste garantizado, modo oscuro profesional y tarjetas flotantes
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    .stApp {
        background: #0D0D0D;
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #FFFFFF !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .safara-card {
        background: #161616;
        padding: 20px;
        border-radius: 14px;
        border: 2px solid #FFD700;
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.15);
        animation: fadeIn 0.5s ease-out;
        margin-bottom: 20px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #000000;
        font-weight: 800;
        border-radius: 10px;
        border: none;
        width: 100%;
        padding: 0.75rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(255, 215, 0, 0.5);
        background: linear-gradient(135deg, #FFE44D 0%, #FFB733 100%);
    }
    
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #1F1F1F !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #444444 !important;
    }
    
    div.stMetric {
        background: #1A1A1A;
        border: 1px solid #FFD700;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    
    div.stMetric label {
        color: #DDDDDD !important;
        font-weight: 600;
    }
    
    div.stMetric [data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado visual con los logotipos reales de Safara
col_logo1, col_logo2 = st.columns([1, 2])

with col_logo1:
    if os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #FFD700;'>🔥</h1>", unsafe_allow_html=True)

with col_logo2:
    if os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", use_container_width=True)
    else:
        st.markdown("""
            <div class="safara-card" style="text-align: center; padding: 15px;">
                <h2 style="color: #FFD700; margin: 0; font-weight: 800;">SAFARA PERCUSSION</h2>
                <p style="color: #FFFFFF; margin: 4px 0 0 0; font-size: 13px;">Gestión de Gastos y Tesorería</p>
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
usuario_actual = st.selectbox("👤 Selecciona tu perfil para operar:", todos_los_miembros)

es_administrador = usuario_actual in st.session_state.admins

# Tarjetas de Métricas Principales con alto contraste
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

# Panel de control exclusivo para administradores (Modificar saldo y registrar colaboradores)
if es_administrador:
    with st.expander("⚙️ Panel de Administración (Solo Administradores)"):
        col_adm1, col_adm2 = st.columns(2)
        
        with col_adm1:
            st.subheader("Actualizar Saldo Caja Rural")
            nuevo_saldo = st.number_input("Nuevo saldo (€)", value=float(st.session_state.saldo_caja), min_value=0.0, step=10.0)
            if st.button("Guardar Saldo Banco"):
                st.session_state.saldo_caja = nuevo_saldo
                st.success("¡Saldo de Caja Rural actualizado con éxito!")
                st.rerun()

        with col_adm2:
            st.subheader("Añadir Colaborador")
            nuevo_colaborador = st.text_input("Nombre del nuevo usuario")
            if st.button("Registrar Colaborador"):
                if nuevo_colaborador and nuevo_colaborador not in st.session_state.usuarios and nuevo_colaborador not in st.session_state.admins:
                    st.session_state.usuarios.append(nuevo_colaborador)
                    st.success(f"¡Colaborador '{nuevo_colaborador}' añadido!")
                    st.rerun()
                else:
                    st.error("Introduce un nombre válido o que no esté duplicado.")
        
        if st.session_state.usuarios:
            st.write("Colaboradores registrados:", ", ".join(st.session_state.usuarios))

st.divider()

# Formulario para registrar gasto
st.markdown(f"### 📝 Registrar Nuevo Gasto <span style='font-size:14px; color:#FFD700;'>(Activo como: {usuario_actual})</span>", unsafe_allow_html=True)
st.write("Sube el ticket o factura en imagen o PDF para solicitar tu reembolso.")

with st.form("form_gasto", clear_on_submit=True):
    concepto = st.text_input("Concepto / Comercio*", placeholder="Ej. Material percusión, Transporte...")
    importe = st.number_input("Importe (€)*", min_value=0.0, step=1
