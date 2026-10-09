import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="Safara Percussion - Gastos", page_icon="🔥", layout="centered")

# Estilos CSS corporativos (Negro, Amarillo y Fuego)
st.markdown("""
    <style>
    .main { background-color: #121212; color: #FFFFFF; }
    .stButton>button { background-color: #FFD700; color: #000000; font-weight: bold; border-radius: 8px; border: none; width: 100%; }
    .stButton>button:hover { background-color: #FFC000; color: #000000; }
    .safara-card { background-color: #1E1E1E; padding: 20px; border-radius: 12px; border: 1px solid #333333; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# Cabecera oficial con logotipos
col_logo1, col_logo2 = st.columns([1, 2])
with col_logo1:
    if os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", use_container_width=True)
    else:
        st.markdown("🔥")
with col_logo2:
    if os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", use_container_width=True)
    else:
        st.markdown("### SAFARA PERCUSSION")
    st.markdown("<p style='color: #AAAAAA; font-size: 14px; margin: 0;'>Panel de Transparencia Financiera y Junta</p>", unsafe_allow_html=True)

st.divider()

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"

# Inicializar bases de datos y estados
if 'gastos' not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        st.session_state.gastos = pd.read_excel(EXCEL_FILE)
    else:
        st.session_state.gastos = pd.DataFrame(columns=[
            "ID", "Fecha", "Admin", "Concepto", "Importe", "Fichero", "Reembolsado"
        ])

if 'saldo_caja' not in st.session_state:
    st.session_state.saldo_caja = 1250.50

if 'admins' not in st.session_state:
    st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = []

# Métricas principales
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Saldo Caja Rural", f"{st.session_state.saldo_caja:.2f} €")
with m2:
    total_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Gastos Totales", f"{total_gastos:.2f} €")
with m3:
    pendientes = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Pendiente Reembolsar", f"{pendientes:.2f} €")

st.divider()

# Sección de Gestión de Usuarios y Administradores
with st.expander("👥 Gestión de Miembros y Usuarios"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Administradores actuales")
        st.write(", ".join(st.session_state.admins))
    with col_b:
        st.subheader("Añadir nuevo Usuario / Colaborador")
        nuevo_usuario = st.text_input("Nombre del nuevo usuario")
        if st.button("Registrar Usuario"):
            if nuevo_usuario and nuevo_usuario not in st.session_state.usuarios and nuevo_usuario not in st.session_state.admins:
                st.session_state.usuarios.append(nuevo_usuario)
                st.success(f"¡Usuario '{nuevo_usuario}' añadido con éxito!")
                st.rerun()
            else:
                st.error("Introduce un nombre válido o que no exista ya.")
        if st.session_state.usuarios:
            st.write("Usuarios adicionales:", ", ".join(st.session_state.usuarios))

st.divider()

# Formulario para registrar gasto
st.markdown("### 📝 Registrar Nuevo Gasto")
st.write("Sube el ticket o factura para solicitar el reembolso de forma rápida e intuitiva.")

todos_los_miembros = st.session_state.admins + st.session_state.usuarios

with st.form("form_gasto", clear_on_submit=True):
    miembro_seleccionado = st.selectbox("¿Quién realiza el gasto?", todos_los_miembros)
    concepto = st.text_input("Concepto / Comercio", placeholder="Ej. Material percusión, Transporte...")
    importe = st.number_input("Importe (€)", min_value=0.0, step=1.0, value=0.0)
    fecha = st.date_input("Fecha", datetime.date.today())
    fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])

    enviado = st.form_submit_button("Guardar Gasto")

    if enviado:
        if not concepto or importe <= 0:
            st.error("Por favor, introduce un concepto válido y un importe mayor a 0.")
        else:
            nombre_fichero = ""
            if fichero is not None:
                nombre_fichero = f"{datetime.date.today()}_{miembro_seleccionado}_{fichero.name}"
                ruta_destino = os.path.join(RECEIPTS_DIR, nombre_fichero)
                with open(ruta_destino, "wb") as f:
                    f.write(fichero.getbuffer())

            nuevo_id = len(st.session_state.gastos) + 1
            nuevo_registro = {
                "ID": nuevo_id,
                "Fecha": str(fecha),
                "Admin": miembro_seleccionado,
                "Concepto": concepto,
                "Importe": float(importe),
                "Fichero": nombre_fichero,
                "Reembolsado": False
            }
            
            st.session_state.gastos = pd.concat([st.session_state.gastos, pd.DataFrame([nuevo_registro])], ignore_index=True)
            st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
            st.success("¡Gasto registrado con éxito!")
            st.rerun()

st.divider()

# Historial de gastos
st.markdown("### 📊 Historial de Gastos y Reembolsos")
if st.session_state.gastos.empty:
    st.info("No hay gastos registrados todavía.")
else:
    st.dataframe(st.session_state.gastos, use_container_width=True)

# Ajustes de saldo y finanzas
with st.expander("⚙️ Ajustes de Saldo de Caja"):
    nuevo_saldo = st.number_input("Actualizar saldo actual en cuenta (€)", value=float(st.session_state.saldo_caja), min_value=0.0)
    if st.button("Guardar Nuevo Saldo"):
        st.session_state.saldo_caja = nuevo_saldo
        st.success("Saldo actualizado correctamente.")
        st.rerun()
