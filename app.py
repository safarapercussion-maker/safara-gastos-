import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Safara Percussion - Gastos", page_icon="🔥", layout="centered")

# Estilos CSS Avanzados 2026: Estética oscura, neón dorado y degradados de fuego
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    .stApp {
        background: #000000;
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .safara-logo-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        background: #000000;
        padding: 15px 0;
    }
    
    .safara-card {
        background: linear-gradient(145deg, #0A0A0A 0%, #141414 100%);
        border: 2px solid #FFD700;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.12);
        margin-bottom: 20px;
    }
    
    .expense-item {
        background: #0D0D0D;
        border-left: 4px solid #FFD700;
        border-top: 1px solid #222;
        border-right: 1px solid #222;
        border-bottom: 1px solid #222;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        border: none !important;
        width: 100% !important;
        padding: 0.85rem !important;
        box-shadow: 0 4px 15px rgba(255, 140, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
    }
    
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #080808 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 2px solid #333333 !important;
    }
    
    div[data-baseweb="select"] > div:hover, input:hover {
        border-color: #FFD700 !important;
    }
    
    div.stMetric {
        background: #0A0A0A;
        border: 2px solid rgba(255, 215, 0, 0.4);
        padding: 15px;
        border-radius: 14px;
        text-align: center;
    }
    div.stMetric label { color: #AAAAAA !important; font-weight: 600; font-size: 13px; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 22px; }
    </style>
""", unsafe_allow_html=True)

# 1. CABECERA: Únicamente el Logo del Fuego arriba
st.markdown('<div class="safara-logo-box">', unsafe_allow_html=True)
col_fuego = st.columns([1, 2, 1])
with col_fuego[1]:
    if os.path.exists("Logo detras.png"):
        st.image("Logo detras.png", width=130)
    elif os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", width=130)
    else:
        st.markdown("<h1 style='color: #FFD700; text-align: center; margin:0;'>🔥</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"

# Inicialización de Estados
if 'gastos' not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        st.session_state.gastos = pd.read_excel(EXCEL_FILE)
    else:
        st.session_state.gastos = pd.DataFrame(columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado"])

if 'saldo_caja' not in st.session_state:
    st.session_state.saldo_caja = 1250.50

if 'admins' not in st.session_state:
    st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = []

# Selector de Perfil Activo
todos_miembros = st.session_state.admins + st.session_state.usuarios
usuario_actual = st.selectbox("👤 Identifícate como miembro:", todos_miembros)
es_admin = usuario_actual in st.session_state.admins

st.write("")

# 2. Métricas Principales
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("🏦 Caja Rural", f"{st.session_state.saldo_caja:.2f} €")
with m2:
    t_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("💸 Gastos Totales", f"{t_gastos:.2f} €")
with m3:
    pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("⏳ Pendiente", f"{pend:.2f} €")

st.divider()

# 3. Formulario para Registrar Gastos
st.markdown("""
    <div class="safara-card">
        <h3 style="color: #FFD700; margin-top: 0; font-weight: 800;">📝 Registrar Nuevo Gasto</h3>
        <p style="color: #BBBBBB; font-size: 13px; margin-bottom: 15px;">Sube tu ticket o factura para solicitar el reembolso de forma instantánea.</p>
    </div>
""", unsafe_allow_html=True)

with st.form("form_gasto", clear_on_submit=True):
    concepto = st.text_input("Concepto / Comercio*", placeholder="Ej. Material percusión, Transporte...")
    importe = st.number_input("Importe (€)*", min_value=0.0, step=1.0, value=0.0)
    fecha = st.date_input("Fecha del gasto", datetime.date.today())
    fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])
    
    enviado = st.form_submit_button("🔥 Guardar y Enviar Gasto")
    if enviado:
        if not concepto or importe <= 0:
            st.error("Por favor, introduce un concepto válido y un importe mayor a 0.")
        else:
            nombre_fichero = ""
            if fichero is not None:
                nombre_fichero = f"{datetime.date.today()}_{usuario_actual}_{fichero.name}"
                with open(os.path.join(RECEIPTS_DIR, nombre_fichero), "wb") as f:
                    f.write(fichero.getbuffer())
            
            nuevo_reg = {
                "ID": len(st.session_state.gastos) + 1,
                "Fecha": str(fecha),
                "Usuario": usuario_actual,
                "Concepto": concepto,
                "Importe": float(importe),
                "Fichero": nombre_fichero,
                "Reembolsado": False
            }
            st.session_state.gastos = pd.concat([st.session_state.gastos, pd.DataFrame([nuevo_reg])], ignore_index=True)
            st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
            st.success("¡Gasto registrado con éxito!")
            st.rerun()

st.divider()

# 4. Historial Visual en Tarjetas
st.markdown("### 📊 Historial de Gastos y Reembolsos")

if st.session_state.gastos.empty:
    st.info("No hay gastos registrados todavía en el sistema.")
else:
    for index, row in st.session_state.gastos.iterrows():
        estado_badge = "⏳ Pendiente" if not row['Reembolsado'] else "✅ Reembolsado"
        color_badge = "#FF8C00" if not row['Reembolsado'] else "#2ECC71"
        
        st.markdown(f"""
            <div class="expense-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #FFD700; font-size: 16px;">{row['Concepto']}</strong>
                    <span style="background: {color_badge}; color: #000; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 800;">{estado_badge}</span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #CCCCCC;">
                    👤 <b>{row['Usuario']}</b> &nbsp;|&nbsp; 📅 {row['Fecha']} &nbsp;|&nbsp; <span style="color: #FFD700; font-weight: 800; font-size: 15px;">{row['Importe']:.2f} €</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# 5. Panel de Administración abajo (Solo para administradores)
if es_admin:
    st.markdown("""
        <div class="safara-card" style="border: 2px dashed #FF8C00;">
            <h3 style="color: #FF8C00; margin-top: 0; font-weight: 800;">⚙️ Panel de Administración (Restringido)</h3>
            <p style="color: #AAAAAA; font-size: 13px;">Zona exclusiva para Iñigo, Rosi, Xabi, Resano y Diego.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🛠️ Administrar Caja Rural y Colaboradores", expanded=False):
        st.markdown("#### Actualizar Saldo Caja Rural")
        nuevo_saldo = st.number_input("Nuevo saldo actual (€)", value=float(st.session_state.saldo_caja), min_value=0.0, step=10.0)
        if st.button("Actualizar Saldo Banco"):
            st.session_state.saldo_caja = nuevo_saldo
            st.success("¡Saldo de la Caja Rural actualizado correctamente!")
            st.rerun()
        
        st.divider()
        
        st.markdown("#### Añadir Nuevo Colaborador")
        nuevo_colab = st.text_input("Nombre o mote del colaborador")
        if st.button("Registrar Colaborador"):
            if nuevo_colab and nuevo_colab not in st.session_state.usuarios and nuevo_colab not in st.session_state.admins:
                st.session_state.usuarios.append(nuevo_colab)
                st.success(f"¡Colaborador '{nuevo_colab}' añadido con éxito!")
                st.rerun()
            else:
                st.error("Introduce un nombre válido o que no esté duplicado.")
        
        if st.session_state.usuarios:
            st.write("Colaboradores actuales:", ", ".join(st.session_state.usuarios))

st.divider()

# 6. PIE DE PÁGINA: Únicamente el Logo de Texto Safara Percussion abajo del todo
st.markdown('<div class="safara-logo-box" style="padding-top: 20px; padding-bottom: 30px;">', unsafe_allow_html=True)
col_texto = st.columns([1, 3, 1])
with col_texto[1]:
    if os.path.exists("Logo delante.png"):
        st.image("Logo delante.png", width=200)
    elif os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", width=200)
    else:
        st.markdown("<h3 style='color: #FFD700; text-align: center; margin:0;'>SAFARA PERCUSSION</h3>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
