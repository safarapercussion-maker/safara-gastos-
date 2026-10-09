import streamlit as st
import pandas as pd
import datetime
import os
import re

st.set_page_config(page_title="Safara Percussion - Caja y Gastos", page_icon="🔥", layout="centered")

# Estilos CSS Avanzados 2026: Relieves 3D, tipografía refinada, cero iconos cutres y diseño corporativo prémium
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
        padding: 10px 0;
        width: 100%;
    }
    
    /* Selector de usuario minimalista y limpio */
    .user-select-box {
        background: #0A0A0A;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 10px 16px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Banner Foco Objetivo - Saldo Principal con relieve 3D y brillo de fuego */
    .foco-objetivo-card {
        background: linear-gradient(145deg, #120A00 0%, #1A1200 50%, #080808 100%);
        border: 3px solid #FFD700;
        border-radius: 22px;
        padding: 30px 20px;
        text-align: center;
        box-shadow: 0 15px 35px rgba(255, 140, 0, 0.25), inset 0 2px 6px rgba(255, 215, 0, 0.4);
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    
    .foco-objetivo-card h2 {
        color: #FFD700 !important;
        font-size: 13px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
        font-weight: 800;
    }
    
    .foco-objetivo-card .saldo-gigante {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFD700 50%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        margin: 10px 0;
    }
    
    .foco-objetivo-card p {
        color: #CCCCCC !important;
        font-size: 13px;
        margin-top: 5px;
        font-weight: 600;
    }
    
    /* Tarjetas de contenedores modernos */
    .safara-card {
        background: linear-gradient(145deg, #0A0A0A 0%, #121212 100%);
        border: 2px solid #FFD700;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.15);
        margin-bottom: 20px;
    }
    
    .expense-item {
        background: #0B0B0B;
        border-left: 4px solid #FF8C00;
        border-top: 1px solid #1F1F1F;
        border-right: 1px solid #1F1F1F;
        border-bottom: 1px solid #1F1F1F;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
    }
    
    /* Botones con degradado Fuego / Oro vibrante */
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 14px !important;
        border: none !important;
        width: 100% !important;
        padding: 0.9rem !important;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.35);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.6);
    }
    
    /* Inputs, Selectores y Uploader de ficheros limpios */
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #0D0D0D !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #333333 !important;
    }
    
    div[data-baseweb="select"] > div:hover, input:hover {
        border-color: #FFD700 !important;
    }
    
    /* Forzar fondo oscuro en el cargador de archivos */
    [data-testid="stFileUploader"] {
        background-color: #0D0D0D !important;
        border: 2px dashed #FFD700 !important;
        border-radius: 14px;
        padding: 10px;
    }
    [data-testid="stFileUploader"] section {
        background-color: #0D0D0D !important;
    }
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] div {
        color: #CCCCCC !important;
    }
    
    /* Métricas secundarias */
    div.stMetric {
        background: #0A0A0A;
        border: 2px solid rgba(255, 215, 0, 0.4);
        padding: 14px;
        border-radius: 14px;
        text-align: center;
    }
    div.stMetric label { color: #AAAAAA !important; font-weight: 600; font-size: 12px; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# Detección inteligente de archivos de imagen en el repositorio
archivos_dir = os.listdir(".")
logo_arriba = next((f for f in archivos_dir if any(k in f.lower() for k in ["detras", "fuego", "logo_fuego"])), None)
logo_abajo = next((f for f in archivos_dir if any(k in f.lower() for k in ["delante", "texto", "logo_texto", "percussion"])), None)

# 1. CABECERA: Logo del Fuego arriba perfectamente centrado
st.markdown('<div class="safara-logo-box">', unsafe_allow_html=True)
col_fuego = st.columns([1, 2, 1])
with col_fuego[1]:
    if logo_arriba and os.path.exists(logo_arriba):
        st.image(logo_arriba, width=130)
    elif os.path.exists("Logo detras.png"):
        st.image("Logo detras.png", width=130)
    elif os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", width=130)
    else:
        st.markdown("<h1 style='color: #FFD700; text-align: center; margin:0;'>🔥</h1>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

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

# Selector de Usuario Activo discreto y elegante (Sin iconos cutres)
todos_miembros = st.session_state.admins + st.session_state.usuarios
c_label, c_select = st.columns([1, 2])
with c_label:
    st.markdown("<p style='color: #FFD700; font-size: 11px; font-weight: 800; letter-spacing: 1px; margin-top: 10px;'>SESIÓN ACTIVA</p>", unsafe_allow_html=True)
with c_select:
    usuario_actual = st.selectbox("", todos_miembros, label_visibility="collapsed")
es_admin = usuario_actual in st.session_state.admins

st.write("")

# 2. FOCO OBJETIVO PRINCIPAL: Saldo Disponible Caja Rural de Navarra (Protagonismo Absoluto con Relieve)
st.markdown(f"""
    <div class="foco-objetivo-card">
        <h2>Caja Rural de Navarra • Fondo Común</h2>
        <div class="saldo-gigante">{st.session_state.saldo_caja:,.2f} €</div>
        <p>Objetivo: recaudación y gestión de fondos para eventos, ensayos y reuniones.</p>
    </div>
""", unsafe_allow_html=True)

# Métricas secundarias de apoyo
m1, m2 = st.columns(2)
with m1:
    t_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Gastos Totales", f"{t_gastos:.2f} €")
with m2:
    pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Pendiente Reembolso", f"{pend:.2f} €")

st.divider()

# 3. HISTÓRICO DE GASTOS VISUAL (Cuadro interactivo profesional sin iconos genéricos)
st.markdown("<p style='color: #FFD700; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;'>REGISTRO HISTÓRICO DE GASTOS</p>", unsafe_allow_html=True)

if st.session_state.gastos.empty:
    st.info("No hay gastos registrados todavía en el sistema.")
else:
    for index, row in st.session_state.gastos.iterrows():
        estado_badge = "PENDIENTE" if not row['Reembolsado'] else "REEMBOLSADO"
        color_badge = "#FF8C00" if not row['Reembolsado'] else "#2ECC71"
        
        st.markdown(f"""
            <div class="expense-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #FFD700; font-size: 15px;">{row['Concepto']}</strong>
                    <span style="background: {color_badge}; color: #000; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 800; letter-spacing: 0.5px;">{estado_badge}</span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #CCCCCC;">
                    <span style="color: #AAAAAA;">Colaborador:</span> <b>{row['Usuario']}</b> &nbsp;|&nbsp; <span style="color: #AAAAAA;">Fecha:</span> {row['Fecha']} &nbsp;|&nbsp; <span style="color: #FFD700; font-weight: 800; font-size: 15px;">{row['Importe']:.2f} €</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# 4. FORMULARIO DE REGISTRO DE GASTOS
st.markdown("""
    <div class="safara-card">
        <h3 style="color: #FFD700; margin-top: 0; font-weight: 800; font-size: 18px;">Registrar Nuevo Gasto</h3>
        <p style="color: #BBBBBB; font-size: 13px; margin-bottom: 15px;">Selecciona la categoría del gasto, adjunta tu ticket y valida el importe.</p>
    </div>
""", unsafe_allow_html=True)

categorias_safara = [
    "Instrumentos (parches, mazas, repuestos)",
    "Bebidas",
    "Accesorios (Luces, complementos)",
    "Equipamiento (Ropa)",
    "Tasa Administración",
    "Restaurantes / Dietas",
    "Gasolina",
    "Otros"
]

with st.form("form_gasto", clear_on_submit=True):
    categoria_seleccionada = st.selectbox("Categoría de Gasto*", categorias_safara)
    detalle_concepto = st.text_input("Detalle adicional / Comercio", placeholder="Ej. Tam Tam, Bar Río, Coviran...")
    
    fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF)", type=["png", "jpg", "jpeg", "pdf"])
    
    # Autodetección de importe basada en el nombre del fichero
    importe_sugerido = 0.0
    if fichero is not None:
        nums = re.findall(r'\d+[.,]?\d*', fichero.name)
        if nums:
            try:
                posible_val = float(nums[-1].replace(',', '.'))
                if posible_val < 1000:
                    importe_sugerido = posible_val
            except:
                pass
    
    importe = st.number_input("Importe (€)*", min_value=0.0, step=1.0, value=importe_sugerido)
    fecha = st.date_input("Fecha del gasto", datetime.date.today())
    
    enviado = st.form_submit_button("Guardar y Enviar Gasto")
    if enviado:
        if importe <= 0:
            st.error("Por favor, introduce un importe válido mayor a 0.")
        else:
            nombre_fichero = ""
            if fichero is not None:
                nombre_fichero = f"{datetime.date.today()}_{usuario_actual}_{fichero.name}"
                with open(os.path.join(RECEIPTS_DIR, nombre_fichero), "wb") as f:
                    f.write(fichero.getbuffer())
            
            concepto_final = f"{categoria_seleccionada}" + (f" - {detalle_concepto}" if detalle_concepto else "")
            
            nuevo_reg = {
                "ID": len(st.session_state.gastos) + 1,
                "Fecha": str(fecha),
                "Usuario": usuario_actual,
                "Concepto": concepto_final,
                "Importe": float(importe),
                "Fichero": nombre_fichero,
                "Reembolsado": False
            }
            st.session_state.gastos = pd.concat([st.session_state.gastos, pd.DataFrame([nuevo_reg])], ignore_index=True)
            st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
            st.success("¡Gasto registrado con éxito!")
            st.rerun()

st.divider()

# 5. Panel de Administración abajo (Solo para administradores)
if es_admin:
    st.markdown("""
        <div class="safara-card" style="border: 2px dashed #FF8C00;">
            <h3 style="color: #FF8C00; margin-top: 0; font-weight: 800; font-size: 18px;">Panel de Administración</h3>
            <p style="color: #AAAAAA; font-size: 13px;">Zona exclusiva para Iñigo, Rosi, Xabi, Resano y Diego.</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("Administrar Caja Rural y Colaboradores", expanded=False):
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

# 6. PIE DE PÁGINA: Logo de Texto Safara Percussion abajo del todo, centrado y más pequeño
st.markdown('<div class="safara-logo-box" style="padding-top: 20px; padding-bottom: 30px;">', unsafe_allow_html=True)
col_texto = st.columns([1, 2, 1])
with col_texto[1]:
    if logo_abajo and os.path.exists(logo_abajo):
        st.image(logo_abajo, width=130)
    elif os.path.exists("Logo delante.png"):
        st.image("Logo delante.png", width=130)
    elif os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", width=130)
    else:
        st.markdown("<h3 style='color: #FFD700; text-align: center; margin:0;'>SAFARA PERCUSSION</h3>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
