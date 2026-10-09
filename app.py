import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Safara Percussion", page_icon="🔥", layout="centered")

st.markdown("""
    <style>
    .stApp { background: #0D0D0D; color: #FFFFFF; font-family: sans-serif; }
    h1, h2, h3, h4, h5, h6, p, span, label { color: #FFFFFF !important; }
    .stButton>button { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000000; font-weight: 800; border-radius: 10px; border: none; width: 100%; padding: 0.75rem; }
    div[data-baseweb="select"] > div, input { background-color: #1F1F1F !important; color: #FFFFFF !important; border-radius: 8px !important; border: 1px solid #444444 !important; }
    div.stMetric { background: #1A1A1A; border: 1px solid #FFD700; padding: 15px; border-radius: 12px; }
    div.stMetric label { color: #DDDDDD !important; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# Búsqueda automática de archivos de imagen de logos en el repositorio
archivos_en_directorio = os.listdir(".")
logo_fuego_encontrado = next((f for f in archivos_en_directorio if "fuego" in f.lower() or ("logo" in f.lower() and ("detras" in f.lower() or "delante" in f.lower()))), None)
logo_texto_encontrado = next((f for f in archivos_en_directorio if "texto" in f.lower() or ("logo" in f.lower() and f != logo_fuego_encontrado)), None)

# Cabecera con logotipos detectados o respaldo seguro
col1, col2 = st.columns([1, 2])
with col1:
    if logo_fuego_encontrado and os.path.exists(logo_fuego_encontrado):
        st.image(logo_fuego_encontrado, use_container_width=True)
    elif os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", use_container_width=True)
    else:
        st.markdown("<h1 style='color: #FFD700; text-align: center;'>🔥</h1>", unsafe_allow_html=True)

with col2:
    if logo_texto_encontrado and os.path.exists(logo_texto_encontrado):
        st.image(logo_texto_encontrado, use_container_width=True)
    elif os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", use_container_width=True)
    else:
        st.markdown("<h3 style='color: #FFD700; padding-top: 10px;'>SAFARA PERCUSSION</h3>", unsafe_allow_html=True)

st.divider()

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"

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

todos_miembros = st.session_state.admins + st.session_state.usuarios
usuario_actual = st.selectbox("👤 Selecciona tu perfil:", todos_miembros)
es_admin = usuario_actual in st.session_state.admins

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("🏦 Caja Rural", f"{st.session_state.saldo_caja:.2f} €")
with m2:
    t_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("💸 Gastos", f"{t_gastos:.2f} €")
with m3:
    pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("⏳ Pendiente", f"{pend:.2f} €")

st.divider()

if es_admin:
    with st.expander("⚙️ Panel de Administración (Solo Admins)"):
        nuevo_saldo = st.number_input("Actualizar saldo Caja Rural (€)", value=float(st.session_state.saldo_caja), min_value=0.0)
        if st.button("Guardar Saldo"):
            st.session_state.saldo_caja = nuevo_saldo
            st.success("¡Saldo actualizado!")
            st.rerun()
        
        nuevo_colab = st.text_input("Añadir nuevo colaborador")
        if st.button("Registrar Colaborador"):
            if nuevo_colab and nuevo_colab not in st.session_state.usuarios and nuevo_colab not in st.session_state.admins:
                st.session_state.usuarios.append(nuevo_colab)
                st.success(f"¡{nuevo_colab} añadido!")
                st.rerun()

st.divider()

st.markdown(f"### 📝 Registrar Gasto <span style='font-size:14px; color:#FFD700;'>(Usuario: {usuario_actual})</span>", unsafe_allow_html=True)

with st.form("form_gasto", clear_on_submit=True):
    concepto = st.text_input("Concepto / Comercio")
    importe = st.number_input("Importe (€)", min_value=0.0, step=1.0, value=0.0)
    fecha = st.date_input("Fecha", datetime.date.today())
    fichero = st.file_uploader("Ticket o Factura", type=["png", "jpg", "jpeg", "pdf"])
    
    enviado = st.form_submit_button("Guardar Gasto")
    if enviado:
        if not concepto or importe <= 0:
            st.error("Introduce un concepto y un importe mayor a 0.")
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
            st.success("¡Gasto guardado con éxito!")
            st.rerun()

st.divider()
st.markdown("### 📊 Historial")
if st.session_state.gastos.empty:
    st.info("No hay gastos registrados.")
else:
    st.dataframe(st.session_state.gastos, use_container_width=True)
