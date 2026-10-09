import streamlit as st
import pandas as pd
import datetime
import os
import re
import zipfile
import io

st.set_page_config(page_title="Safara Percussion - Caja y Gastos", page_icon="🔥", layout="centered")

# Estilos CSS Definitivos: Fusión total de logos, centrado real y selector compacto arriba a la derecha
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 20%, rgba(255, 140, 0, 0.1) 0%, transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(255, 215, 0, 0.08) 0%, transparent 40%),
            linear-gradient(135deg, #050505 0%, #080808 50%, #000000 100%);
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Selector de usuario ultra-compacto y discreto en la esquina superior derecha */
    .top-right-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-bottom: -20px;
    }
    .top-right-box {
        width: 140px;
    }
    
    /* Fusión perfecta del logo: adiós al recuadro negro, integrándose con el fondo oscuro */
    [data-testid="stImage"] img {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        background: transparent !important;
        mix-blend-mode: lighten !important;
    }
    
    /* Frase final "Somos fuego" */
    .somos-fuego-footer {
        text-align: center;
        font-family: 'Cinzel', serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 4px;
        text-transform: uppercase;
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 50%, #FF4500 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(255, 140, 0, 0.5);
        margin-top: 15px;
        margin-bottom: 25px;
        width: 100%;
    }
    
    /* Banner Foco Objetivo - Relieve 3D */
    .foco-objetivo-card {
        background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%);
        border: 3px solid #FFD700;
        border-radius: 26px;
        padding: 35px 22px;
        text-align: center;
        box-shadow: 0 20px 50px rgba(255, 140, 0, 0.35), inset 0 3px 10px rgba(255, 215, 0, 0.6);
        margin-bottom: 25px;
        margin-top: 25px;
    }
    
    .foco-objetivo-card h2 {
        color: #FFD700 !important;
        font-size: 12px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
        font-weight: 800;
    }
    
    .foco-objetivo-card .saldo-gigante {
        font-size: 46px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFD700 50%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 5px 25px rgba(255, 215, 0, 0.5);
        margin: 10px 0;
    }
    
    .foco-objetivo-card p {
        color: #E0E0E0 !important;
        font-size: 13px;
        margin-top: 5px;
        font-weight: 600;
    }
    
    /* Tarjetas y elementos */
    .safara-card {
        background: linear-gradient(145deg, #0D0D0D 0%, #161616 100%);
        border: 2px solid #FFD700;
        border-radius: 20px;
        padding: 26px;
        box-shadow: 0 12px 35px rgba(255, 215, 0, 0.18);
        margin-bottom: 20px;
    }
    
    .expense-item {
        background: linear-gradient(145deg, #0A0A0A 0%, #121212 100%);
        border-left: 5px solid #FF8C00;
        border-top: 1px solid #2A2A2A;
        border-right: 1px solid #2A2A2A;
        border-bottom: 1px solid #2A2A2A;
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 14px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.7);
    }
    
    /* Botones con alto contraste */
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        width: 100% !important;
        padding: 0.9rem !important;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.7);
    }
    
    /* Inputs y selectores generales con contraste impecable */
    div[data-baseweb="select"] > div, input, textarea {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #555555 !important;
    }
    
    div[data-baseweb="input"] input {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    input::placeholder {
        color: #CCCCCC !important;
        -webkit-text-fill-color: #CCCCCC !important;
    }
    
    [data-testid="stFileUploader"] {
        background-color: #161616 !important;
        border: 2px dashed #FFD700 !important;
        border-radius: 14px;
        padding: 10px;
    }
    [data-testid="stFileUploader"] section {
        background-color: #161616 !important;
    }
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] div {
        color: #FFFFFF !important;
    }
    
    div.stMetric {
        background: linear-gradient(145deg, #0D0D0D 0%, #161616 100%);
        border: 2px solid rgba(255, 215, 0, 0.4);
        padding: 16px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }
    div.stMetric label { color: #E0E0E0 !important; font-weight: 600; font-size: 12px; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# Detección inteligente de archivos de imagen en el repositorio
archivos_dir = os.listdir(".")
logo_arriba = next((f for f in archivos_dir if any(k in f.lower() for k in ["detras", "fuego", "logo_fuego"])), None)
logo_abajo = next((f for f in archivos_dir if any(k in f.lower() for k in ["delante", "texto", "logo_texto", "percussion"])), None)

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

if 'admin_autenticado' not in st.session_state:
    st.session_state.admin_autenticado = False

# SELECTOR DE USUARIO COMPACTO EN LA ESQUINA SUPERIOR DERECHA
st.markdown('<div class="top-right-container"><div class="top-right-box">', unsafe_allow_html=True)
todos_miembros = st.session_state.admins + st.session_state.usuarios
usuario_actual = st.selectbox("Usuario", todos_miembros, label_visibility="collapsed")
st.markdown('</div></div>', unsafe_allow_html=True)

es_miembro_admin = usuario_actual in st.session_state.admins

# 1. CABECERA: Logo superior CENTRADO PERFECTO en la página con columnas simétricas
col_l1, col_c1, col_r1 = st.columns([1, 2, 1])
with col_c1:
    if logo_arriba and os.path.exists(logo_arriba):
        st.image(logo_arriba, width=130)
    elif os.path.exists("Logo detras.png"):
        st.image("Logo detras.png", width=130)
    elif os.path.exists("logo_fuego.png"):
        st.image("logo_fuego.png", width=130)
    else:
        st.markdown("<h1 style='color: #FFD700; text-align: center; margin:0;'>🔥</h1>", unsafe_allow_html=True)

# 2. FOCO OBJETIVO PRINCIPAL: Saldo Disponible Caja Rural de Navarra
st.markdown(f"""
    <div class="foco-objetivo-card">
        <h2>Caja Rural de Navarra • Fondo Común</h2>
        <div class="saldo-gigante">{st.session_state.saldo_caja:,.2f} €</div>
        <p>Nuestro objetivo: recaudar y gestionar fondos para disfrutar de nuestros eventos, ensayos y reuniones.</p>
    </div>
""", unsafe_allow_html=True)

# Métricas secundarias
m1, m2 = st.columns(2)
with m1:
    t_gastos = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Gastos Totales", f"{t_gastos:.2f} €")
with m2:
    pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Pendiente Reembolso", f"{pend:.2f} €")

st.write("")

# 3. HISTÓRICO DE GASTOS VISUAL E INTERACTIVO
st.markdown("<p style='color: #FFD700; font-size: 16px; font-weight: 800; letter-spacing: 0.5px;'>REGISTRO HISTÓRICO DE GASTOS</p>", unsafe_allow_html=True)

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
                <div style="margin-top: 8px; font-size: 13px; color: #FFFFFF;">
                    <span style="color: #DDDDDD;">Colaborador:</span> <b>{row['Usuario']}</b> &nbsp;|&nbsp; <span style="color: #DDDDDD;">Fecha:</span> {row['Fecha']} &nbsp;|&nbsp; <span style="color: #FFD700; font-weight: 800; font-size: 15px;">{row['Importe']:.2f} €</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if es_miembro_admin and st.session_state.admin_autenticado:
            if st.button(f"Eliminar Gasto #{row['ID']}", key=f"del_{row['ID']}_{index}"):
                st.session_state.gastos = st.session_state.gastos[st.session_state.gastos['ID'] != row['ID']]
                st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
                st.success(f"¡Gasto #{row['ID']} eliminado correctamente!")
                st.rerun()

st.divider()

# 4. FORMULARIO DE REGISTRO DE GASTOS
st.markdown("""
    <div class="safara-card">
        <h3 style="color: #FFD700; margin-top: 0; font-weight: 800; font-size: 18px;">Registrar Nuevo Gasto</h3>
        <p style="color: #FFFFFF; font-size: 13px; margin-bottom: 15px;">Selecciona la categoría, adjunta tu ticket y valida el importe.</p>
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
                ext = fichero.name.split('.')[-1]
                nombre_fichero = f"Gasto_{int(st.session_state.gastos['ID'].max() + 1) if not st.session_state.gastos.empty else 1}_{fecha}_{usuario_actual}.{ext}"
                with open(os.path.join(RECEIPTS_DIR, nombre_fichero), "wb") as f:
                    f.write(fichero.getbuffer())
            
            concepto_final = f"{categoria_seleccionada}" + (f" - {detalle_concepto}" if detalle_concepto else "")
            
            nuevo_reg = {
                "ID": int(st.session_state.gastos["ID"].max() + 1) if not st.session_state.gastos.empty else 1,
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

# 5. PANEL DE ADMINISTRACIÓN PROTEGIDO POR PIN
if es_miembro_admin:
    st.markdown("""
        <div class="safara-card" style="border: 2px dashed #FF8C00;">
            <h3 style="color: #FF8C00; margin-top: 0; font-weight: 800; font-size: 18px;">Acceso de Administración</h3>
            <p style="color: #FFFFFF; font-size: 13px;">Introduce la clave de administración para desbloquear las opciones de auditoría y gestión.</p>
        </div>
    """, unsafe_allow_html=True)
    
    pin_ingresado = st.text_input("Clave de Administración", type="password", placeholder="Introduce la contraseña...")
    PIN_SECRETO = "safara2026"
    
    if pin_ingresado == PIN_SECRETO:
        st.session_state.admin_autenticado = True
        st.success("¡Acceso de administración autorizado!")
    elif pin_ingresado != "":
        st.session_state.admin_autenticado = False
        st.error("Contraseña incorrecta.")

    if st.session_state.admin_autenticado:
        st.markdown("""
            <div class="safara-card" style="border: 2px solid #2ECC71;">
                <h3 style="color: #2ECC71; margin-top: 0; font-weight: 800; font-size: 18px;">Panel de Administración y Auditoría</h3>
                <p style="color: #FFFFFF; font-size: 13px;">Zona desbloqueada para miembros autorizados.</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Exportar Paquete Contable para Inspección (ZIP + Excel)", expanded=True):
            st.markdown("Genera un archivo comprimido ZIP conteniendo el libro oficial en Excel y todos los justificantes indexados.")
            
            if st.button("Generar Paquete ZIP de Auditoría"):
                if st.session_state.gastos.empty:
                    st.warning("No hay gastos registrados para exportar.")
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        excel_buffer = io.BytesIO()
                        st.session_state.gastos.to_excel(excel_buffer, index=False)
                        zip_file.writestr("Libro_Registro_Safara_Percussion.xlsx", excel_buffer.getvalue())
                        
                        for _, row in st.session_state.gastos.iterrows():
                            fich = row['Fichero']
                            if fich and isinstance(fich, str):
                                path_fich = os.path.join(RECEIPTS_DIR, fich)
                                if os.path.exists(path_fich):
                                    clean_concept = re.sub(r'[^a-zA-Z0-9]', '_', row['Concepto'])[:30]
                                    ext = fich.split('.')[-1]
                                    zip_name = f"Justificantes/ID_{row['ID']}_{row['Fecha']}_{clean_concept}_{row['Importe']}EUR.{ext}"
                                    zip_file.write(path_fich, zip_name)
                    
                    zip_buffer.seek(0)
                    st.success("¡Paquete de auditoría generado con éxito!")
                    st.download_button(
                        label="Descargar ZIP Certificado para Inspección",
                        data=zip_buffer,
                        file_name=f"Auditoria_Safara_Percussion_{datetime.date.today()}.zip",
                        mime="application/zip"
                    )

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

# 6. PIE DE PÁGINA: Logo inferior CENTRADO EXACTO con columnas simétricas y fusión limpia
col_l2, col_c2, col_r2 = st.columns([1, 2, 1])
with col_c2:
    if logo_abajo and os.path.exists(logo_abajo):
        st.image(logo_abajo, width=130)
    elif os.path.exists("Logo delante.png"):
        st.image("Logo delante.png", width=130)
    elif os.path.exists("logo_texto.png"):
        st.image("logo_texto.png", width=130)
    else:
        st.markdown("<h3 style='color: #FFD700; text-align: center; margin:0;'>SAFARA PERCUSSION</h3>", unsafe_allow_html=True)

st.markdown('<div class="somos-fuego-footer">Somos fuego</div>', unsafe_allow_html=True)
