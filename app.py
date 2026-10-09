import streamlit as st
import pandas as pd
import datetime
import os
import re
import zipfile
import io
import base64
import urllib.parse

st.set_page_config(page_title="Safara Percussion - Caja y Gastos", page_icon="🔥", layout="centered")

# Función optimizada para renderizar los PNGs reales con transparencia perfecta
def render_logo_png(filename, width=180):
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            ext = filename.split('.')[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            return f"""
                <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 10px 0;">
                    <img src="data:{mime};base64,{encoded}" width="{width}" style="display: block; background: transparent; mix-blend-mode: screen; filter: brightness(1.15) contrast(1.1); pointer-events: none; user-select: none;" />
                </div>
            """
        except:
            return None
    return None

# Estilos CSS Avanzados: Estética Dark-Fire, asteriscos iluminados y toque móvil
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(circle at 15% 20%, rgba(255, 140, 0, 0.12) 0%, transparent 40%),
            radial-gradient(circle at 85% 80%, rgba(255, 215, 0, 0.1) 0%, transparent 40%),
            linear-gradient(135deg, #050505 0%, #080808 50%, #000000 100%);
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    [data-testid="stStatusWidget"], header {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Asteriscos iluminados dorados para campos obligatorios */
    label span[data-testid="stWidgetLabel"] {
        color: #FFD700 !important;
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
        margin-top: 25px;
        margin-bottom: 25px;
        width: 100%;
    }
    
    /* Tarjeta Saldo Gigante Dinámico */
    .foco-objetivo-card {
        background: linear-gradient(145deg, #180E00 0%, #261A00 50%, #0D0D0D 100%);
        border: 3px solid #FFD700;
        border-radius: 24px;
        padding: 30px 20px;
        text-align: center;
        box-shadow: 0 20px 50px rgba(255, 140, 0, 0.35), inset 0 3px 10px rgba(255, 215, 0, 0.6);
        margin-bottom: 20px;
        margin-top: 10px;
    }
    
    .foco-objetivo-card h2 {
        color: #FFD700 !important;
        font-size: 11px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 6px;
        font-weight: 800;
    }
    
    .foco-objetivo-card .saldo-gigante {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFD700 50%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 5px 25px rgba(255, 215, 0, 0.6);
        margin: 8px 0;
    }
    
    .foco-objetivo-card p {
        color: #E0E0E0 !important;
        font-size: 12px;
        margin-top: 4px;
        font-weight: 600;
    }
    
    .safara-card {
        background: linear-gradient(145deg, #0D0D0D 0%, #161616 100%);
        border: 2px solid #FFD700;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 12px 35px rgba(255, 215, 0, 0.18);
        margin-bottom: 18px;
    }
    
    .expense-item {
        background: linear-gradient(145deg, #0A0A0A 0%, #121212 100%);
        border-left: 5px solid #FF8C00;
        border-top: 1px solid #2A2A2A;
        border-right: 1px solid #2A2A2A;
        border-bottom: 1px solid #2A2A2A;
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.7);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        width: 100% !important;
        padding: 0.85rem !important;
        box-shadow: 0 6px 20px rgba(255, 140, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.7);
    }
    
    input, textarea, select {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #555555 !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #555555 !important;
    }
    
    div[data-baseweb="input"] input, input[type="text"], input[type="number"], input[type="password"], input[type="date"] {
        background-color: #161616 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    div.stMetric {
        background: linear-gradient(145deg, #0D0D0D 0%, #161616 100%);
        border: 2px solid rgba(255, 215, 0, 0.4);
        padding: 14px;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.5);
    }
    div.stMetric label { color: #E0E0E0 !important; font-weight: 600; font-size: 11px; }
    div.stMetric [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: 800; font-size: 17px; }
    </style>
""", unsafe_allow_html=True)

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)
EXCEL_FILE = "gastos_safara.xlsx"
SALDO_FILE = "saldo_caja.txt"

# Inicialización de Estados
if 'gastos' not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        try:
            st.session_state.gastos = pd.read_excel(EXCEL_FILE)
            if "Reembolsado" not in st.session_state.gastos.columns:
                st.session_state.gastos["Reembolsado"] = False
        except:
            st.session_state.gastos = pd.DataFrame(columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado"])
    else:
        st.session_state.gastos = pd.DataFrame(columns=["ID", "Fecha", "Usuario", "Concepto", "Importe", "Fichero", "Reembolsado"])

if 'saldo_caja' not in st.session_state:
    if os.path.exists(SALDO_FILE):
        try:
            with open(SALDO_FILE, "r") as f:
                st.session_state.saldo_caja = float(f.read().strip())
        except:
            st.session_state.saldo_caja = 1250.50
    else:
        st.session_state.saldo_caja = 1250.50

if 'admins' not in st.session_state:
    st.session_state.admins = ["Iñigo", "Rosi", "Xabi", "Resano", "Diego"]

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = []

if 'admin_autenticado' not in st.session_state:
    st.session_state.admin_autenticado = False

# Selector de usuario discreto en la esquina superior derecha
col_disc_1, col_disc_2 = st.columns([3.5, 1.5])
with col_disc_2:
    todos_miembros = st.session_state.admins + st.session_state.usuarios
    usuario_actual = st.selectbox("Usuario", todos_miembros, label_visibility="collapsed")

es_miembro_admin = usuario_actual in st.session_state.admins

# 1. LOGO SUPERIOR: "Logo delante PNG.png"
logo_sup = "Logo delante PNG.png"
if os.path.exists(logo_sup):
    html_s = render_logo_png(logo_sup, width=200)
    if html_s:
        st.markdown(html_s, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="font-family: 'Cinzel', serif; font-size: 30px; font-weight: 800; letter-spacing: 6px; color: #FF7A00; margin:0;">Safara</h1>
            <div style="font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 7px; color: #FFB347; margin-top: 4px;">Percussion</div>
        </div>
    """, unsafe_allow_html=True)

# Cálculo dinámico del saldo real
total_gastos_acumulados = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
saldo_dinamico_actual = st.session_state.saldo_caja - total_gastos_acumulados

# Tarjeta Saldo Dinámico
st.markdown(f"""
    <div class="foco-objetivo-card">
        <h2>Caja Rural de Navarra • Fondo Común</h2>
        <div class="saldo-gigante">{saldo_dinamico_actual:,.2f} €</div>
        <p>Nuestro objetivo: recaudar y gestionar fondos para disfrutar de nuestros eventos, ensayos y reuniones.</p>
    </div>
""", unsafe_allow_html=True)

# Métricas secundarias
m1, m2 = st.columns(2)
with m1:
    st.metric("Gastos Totales", f"{total_gastos_acumulados:.2f} €")
with m2:
    pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
    st.metric("Pendiente Reembolso", f"{pend:.2f} €")

st.write("")

# 3. ORGANIZACIÓN POR SECCIONES (PESTAÑAS TÁCTILES MÓVILES)
tab_caja, tab_registro, tab_admin = st.tabs(["📊 Caja y Gastos", "➕ Registrar Gasto", "⚙️ Administración"])

# --- PESTAÑA 1: CAJA Y GASTOS ---
with tab_caja:
    st.markdown("<p style='color: #FFD700; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;'>REGISTRO HISTÓRICO DE GASTOS</p>", unsafe_allow_html=True)
    
    if not st.session_state.gastos.empty:
        # Filtros rápidos para móvil
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_estado = st.selectbox("Filtrar Estado", ["Todos", "Pendientes", "Reembolsados"])
        with col_f2:
            cats_filtro = ["Todas"] + list(st.session_state.gastos["Concepto"].apply(lambda x: x.split(" - ")[0]).unique())
            filtro_cat = st.selectbox("Filtrar Categoría", cats_filtro)
            
        df_view = st.session_state.gastos.copy()
        if filtro_estado == "Pendientes":
            df_view = df_view[df_view["Reembolsado"] == False]
        elif filtro_estado == "Reembolsados":
            df_view = df_view[df_view["Reembolsado"] == True]
            
        if filtro_cat != "Todas":
            df_view = df_view[df_view["Concepto"].str.startswith(filtro_cat)]
            
        # Resumen colapsable por colaborador
        with st.expander("👥 Ver resumen de gastos por colaborador"):
            resumen_colab = st.session_state.gastos.groupby("Usuario")["Importe"].sum().reset_index()
            for _, rcol in resumen_colab.iterrows():
                st.write(f"• **{rcol['Usuario']}**: {rcol['Importe']:.2f} €")
        
        st.write("")
        
        if df_view.empty:
            info_msg = st.info("No hay gastos que coincidan con el filtro seleccionado.")
        else:
            for index, row in df_view.iterrows():
                estado_badge = "PENDIENTE" if not row['Reembolsado'] else "ABONADO"
                color_badge = "#FF8C00" if not row['Reembolsado'] else "#2ECC71"
                
                try:
                    f_obj = datetime.date.fromisoformat(str(row['Fecha']))
                    fecha_visual = f_obj.strftime("%d/%m/%Y")
                except:
                    fecha_visual = row['Fecha']
                    
                st.markdown(f"""
                    <div class="expense-item">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: #FFD700; font-size: 14px;">{row['Concepto']}</strong>
                            <span style="background: {color_badge}; color: #000; padding: 2px 7px; border-radius: 6px; font-size: 9px; font-weight: 800; letter-spacing: 0.5px;">{estado_badge}</span>
                        </div>
                        <div style="margin-top: 6px; font-size: 12px; color: #FFFFFF;">
                            <span style="color: #DDDDDD;">Colaborador:</span> <b>{row['Usuario']}</b> &nbsp;|&nbsp; <span style="color: #DDDDDD;">Fecha:</span> {fecha_visual} &nbsp;|&nbsp; <span style="color: #FFD700; font-weight: 800; font-size: 14px;">{row['Importe']:.2f} €</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Previsualización rápida de ticket si existe
                fich = row['Fichero']
                if fich and isinstance(fich, str):
                    path_fich = os.path.join(RECEIPTS_DIR, fich)
                    if os.path.exists(path_fich):
                        with st.expander(f"Ver ticket adjunto (Gasto #{row['ID']})"):
                            if fich.lower().endswith(('.png', '.jpg', '.jpeg')):
                                st.image(path_fich, use_container_width=True)
                            else:
                                st.write(f"Archivo adjunto: {fich}")
    else:
        st.info("No hay gastos registrados todavía en el sistema.")

# --- PESTAÑA 2: REGISTRAR GASTO ---
with tab_registro:
    st.markdown("""
        <div class="safara-card">
            <h3 style="color: #FFD700; margin-top: 0; font-weight: 800; font-size: 17px;">Registrar Nuevo Gasto</h3>
            <p style="color: #FFFFFF; font-size: 12px; margin-bottom: 12px;">Los campos marcados con <span style="color: #FFD700; font-weight: 800;">*</span> son obligatorios.</p>
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
        categoria_seleccionada = st.selectbox("Categoría de Gasto *", categorias_safara)
        detalle_concepto = st.text_input("Detalle adicional / Comercio", placeholder="Ej. Tam Tam, Bar Río, Coviran...")
        
        fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF - Cámara o Galería)", type=["png", "jpg", "jpeg", "pdf"])
        
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
        
        importe = st.number_input("Importe (€) *", min_value=0.0, step=1.0, value=importe_sugerido, format="%.2f")
        fecha = st.date_input("Fecha del gasto *", datetime.date.today())
        
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
                
                # Éxito y notificación flotante (Toast)
                st.success("¡Gasto registrado con éxito!")
                st.toast("🔥 ¡Gasto registrado correctamente!", icon="✅")
                
                # BOTÓN DIRECTO DE WHATSAPP AL TESORERO (650184254)
                texto_w = f"Hola Diego, acabo de registrar un gasto de {importe:.2f}€ en Safara Percussion ({concepto_final}). ¡Revisado y pendiente de abono!"
                url_whatsapp = f"https://wa.me/34650184254?text={urllib.parse.quote(texto_w)}"
                
                st.markdown(f"""
                    <div style="margin-top: 15px; text-align: center;">
                        <a href="{url_whatsapp}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 12px 20px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                            📲 Avisar por WhatsApp al Tesorero
                        </a>
                    </div>
                """, unsafe_allow_html=True)

# --- PESTAÑA 3: ADMINISTRACIÓN ---
with tab_admin:
    st.markdown("""
        <div class="safara-card" style="border: 2px dashed #FF8C00;">
            <h3 style="color: #FF8C00; margin-top: 0; font-weight: 800; font-size: 17px;">Acceso de Administración</h3>
            <p style="color: #FFFFFF; font-size: 12px;">Introduce la clave para desbloquear auditoría, gestión de caja y abonos.</p>
        </div>
    """, unsafe_allow_html=True)
    
    pin_ingresado = st.text_input("Clave de Administración", type="password", placeholder="Introduce la contraseña...")
    PIN_SECRETO = "safara2026"
    
    if pin_ingresado == PIN_SECRETO:
        st.session_state.admin_autenticado = True
    elif pin_ingresado != "":
        st.session_state.admin_autenticado = False
        st.error("Contraseña incorrecta.")

    if st.session_state.admin_autenticado:
        st.markdown("""
            <div class="safara-card" style="border: 2px solid #2ECC71;">
                <h3 style="color: #2ECC71; margin-top: 0; font-weight: 800; font-size: 17px;">Panel de Control y Abonos</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Gestión de Reembolsos Pendientes (Abonos)
        st.markdown("#### ✅ Confirmar Reembolso / Abono a Colaboradores")
        pendientes_df = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False] if not st.session_state.gastos.empty else pd.DataFrame()
        
        if pendientes_df.empty:
            st.info("No hay gastos pendientes de abono en este momento.")
        else:
            for idx, prow in pendientes_df.iterrows():
                col_ab1, col_ab2 = st.columns([3, 1])
                with col_ab1:
                    st.write(f"**#{prow['ID']} - {prow['Usuario']}**: {prow['Importe']:.2f} € ({prow['Concepto']})")
                with col_ab2:
                    if st.button("Abonar", key=f"abonar_{prow['ID']}"):
                        st.session_state.gastos.loc[st.session_state.gastos['ID'] == prow['ID'], 'Reembolsado'] = True
                        st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
                        st.success(f"¡Gasto #{prow['ID']} marcado como abonado!")
                        st.rerun()
        
        st.divider()
        
        with st.expander("Exportar Paquete Contable para Inspección (ZIP + Excel)", expanded=False):
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
                        label="Descargar ZIP Certificado",
                        data=zip_buffer,
                        file_name=f"Auditoria_Safara_Percussion_{datetime.date.today()}.zip",
                        mime="application/zip"
                    )

        with st.expander("Administrar Caja Rural y Colaboradores", expanded=False):
            st.markdown("#### Actualizar Saldo Base Caja Rural")
            nuevo_saldo = st.number_input("Saldo base actual (€)", value=float(st.session_state.saldo_caja), min_value=0.0, step=10.0, format="%.2f")
            if st.button("Actualizar Saldo Banco"):
                st.session_state.saldo_caja = float(nuevo_saldo)
                with open(SALDO_FILE, "w") as f:
                    f.write(str(st.session_state.saldo_caja))
                st.success("¡Saldo base actualizado correctamente!")
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

st.divider()

# 2. LOGO INFERIOR: "Logo detrás PNG.png" centrado
logo_inf = "Logo detrás PNG.png"
if os.path.exists(logo_inf):
    html_i = render_logo_png(logo_inf, width=150)
    if html_i:
        st.markdown(html_i, unsafe_allow_html=True)

# Frase final "Somos fuego"
st.markdown('<div class="somos-fuego-footer">Somos fuego</div>', unsafe_allow_html=True)
