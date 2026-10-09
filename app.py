import streamlit as st
import pandas as pd
import datetime
import os
import re
import zipfile
import io
import base64
import urllib.parse
from datetime import timezone, timedelta

st.set_page_config(page_title="Safara Percussion - Control Financiero", layout="centered")

# Función para obtener la hora exacta en España (UTC+2 en verano / UTC+1 en invierno)
def obtener_fecha_espanol():
    # Ajuste manual preciso a zona horaria de España (CEST / CET)
    # Octubre está en CEST (UTC+2)
    tz_espana = timezone(timedelta(hours=2))
    hoy = datetime.datetime.now(tz_espana).date()
    
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    
    dia_semana = dias[hoy.weekday()]
    mes = meses[hoy.month - 1]
    return f"{dia_semana}, {hoy.day} de {mes}"

# Formato de números en español (1.523,48 €)
def formato_espanol(valor):
    try:
        s = f"{valor:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s
    except:
        return "0,00"

def render_logo_png(filename, width=170):
    if filename and os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            ext = filename.split('.')[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            return f"""
                <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin: 20px 0 10px 0;">
                    <img src="data:{mime};base64,{encoded}" width="{width}" style="display: block; background: transparent; mix-blend-mode: screen; filter: brightness(1.2) contrast(1.15); pointer-events: none; user-select: none;" />
                </div>
            """
        except:
            return None
    return None

def render_logo_inline_b64(filename):
    if filename and os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            ext = filename.split('.')[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime};base64,{encoded}"
        except:
            return None
    return None

def buscar_logo_fuego():
    for f in os.listdir("."):
        f_lower = f.lower()
        if "detra" in f_lower and f_lower.endswith(('.png', '.jpg', '.jpeg')):
            return f
    return None

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
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    [data-testid="stStatusWidget"], header {
        visibility: hidden !important;
        display: none !important;
    }
    
    .header-user-card {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 0 20px 0;
    }
    .header-avatar {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        background: #0D0D0D;
        border: 2px solid #FFD700;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.35);
        flex-shrink: 0;
    }
    .header-avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        padding: 2px;
        background: #000000;
    }
    .header-greeting {
        flex: 1;
    }
    .header-greeting h2 {
        font-size: 24px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        color: #FFFFFF !important;
        line-height: 1.2;
    }
    .header-greeting p {
        font-size: 14px !important;
        color: #AAAAAA !important;
        margin: 2px 0 0 0 !important;
        font-weight: 600;
    }
    
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
        margin-top: 5px;
        margin-bottom: 25px;
        width: 100%;
    }
    
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

logo_fuego_file = buscar_logo_fuego()

col_head_left, col_head_right = st.columns([3, 1.2])

with col_head_right:
    todos_miembros = st.session_state.admins + st.session_state.usuarios
    usuario_actual = st.selectbox("Usuario", todos_miembros, label_visibility="collapsed")

es_miembro_admin = usuario_actual in st.session_state.admins

src_avatar = render_logo_inline_b64(logo_fuego_file) if logo_fuego_file else None

with col_head_left:
    img_html = f'<img src="{src_avatar}" />' if src_avatar else '<span style="font-size:20px; color:#FFD700; font-weight:800;">S</span>'
    fecha_hoy_str = obtener_fecha_espanol()
    st.markdown(f"""
        <div class="header-user-card">
            <div class="header-avatar">
                {img_html}
            </div>
            <div class="header-greeting">
                <h2>Hola, {usuario_actual}</h2>
                <p>{fecha_hoy_str}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

logo_sup = "Logo delante PNG.png"
if os.path.exists(logo_sup):
    html_s = render_logo_png(logo_sup, width=180)
    if html_s:
        st.markdown(html_s, unsafe_allow_html=True)

# Cálculo dinámico del saldo real (Solo resta lo ABONADO)
gastos_abonados_total = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == True]["Importe"].sum() if not st.session_state.gastos.empty else 0.0
saldo_dinamico_actual = st.session_state.saldo_caja - gastos_abonados_total
saldo_formateado_es = formato_espanol(saldo_dinamico_actual)

st.markdown(f"""
    <div class="foco-objetivo-card">
        <h2>Caja Rural de Navarra • Fondo Común</h2>
        <div class="saldo-gigante">{saldo_formateado_es} €</div>
        <p>Nuestro objetivo: recaudar y gestionar fondos para disfrutar de nuestros eventos, ensayos y reuniones.</p>
    </div>
""", unsafe_allow_html=True)

total_gastos_registrados = st.session_state.gastos["Importe"].sum() if not st.session_state.gastos.empty else 0.0
pend = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False]["Importe"].sum() if not st.session_state.gastos.empty else 0.0

m1, m2 = st.columns(2)
with m1:
    st.metric("Gastos Totales", f"{formato_espanol(total_gastos_registrados)} €")
with m2:
    st.metric("Pendiente Reembolso", f"{formato_espanol(pend)} €")

st.write("")

tab_registro, tab_historial, tab_admin = st.tabs(["Registrar Nuevo Gasto", "Historial de Gastos", "Panel de Administración"])

# --- PESTAÑA 1: REGISTRAR NUEVO GASTO ---
with tab_registro:
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

    categoria_seleccionada = st.selectbox("Categoría de Gasto *", categorias_safara)
    detalle_concepto = st.text_input("Detalle adicional / Comercio", placeholder="Ej. Tam Tam, Bar Río, Coviran...")
    fichero = st.file_uploader("Adjuntar Ticket (Imagen o PDF) *", type=["png", "jpg", "jpeg", "pdf"])
    importe = st.number_input("Importe (€) *", min_value=0.0, value=0.0, step=1.0, format="%.2f")
    fecha = st.date_input("Fecha del gasto (Día / Mes / Año) *", datetime.datetime.now(timezone(timedelta(hours=2))).date(), min_value=datetime.date(2023, 1, 1), max_value=datetime.datetime.now(timezone(timedelta(hours=2))).date() + datetime.timedelta(days=1), format="DD/MM/YYYY")

    # Feedback dinámico de validación
    listo_para_enviar = (fichero is not None) and (importe > 0)
    
    if listo_para_enviar:
        st.markdown("""
            <div style="background: rgba(46, 204, 113, 0.15); border: 2px solid #2ECC71; padding: 12px; border-radius: 12px; margin: 10px 0; text-align: center;">
                <span style="color: #2ECC71; font-weight: 800; font-size: 13px;">✔ Formulario completado correctamente. ¡Listo para guardar!</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background: rgba(255, 140, 0, 0.1); border: 1px dashed #FF8C00; padding: 10px; border-radius: 12px; margin: 10px 0; text-align: center;">
                <span style="color: #FFD700; font-size: 12px;">Recuerda adjuntar el ticket y fijar un importe mayor a 0,00 €.</span>
            </div>
        """, unsafe_allow_html=True)

    if st.button("Guardar y Enviar Gasto"):
        if fichero is None:
            st.error("Es obligatorio adjuntar la foto o archivo del ticket para registrar el gasto.")
        elif importe <= 0:
            st.error("Por favor, introduce un importe válido mayor a 0.")
        else:
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
            st.toast("Gasto registrado correctamente")
            
            fecha_formateada_w = fecha.strftime("%d/%m/%Y")
            texto_w = f"Hola Diego, acabo de registrar un gasto de {formato_espanol(importe)}€ en Safara Percussion ({concepto_final}) con fecha {fecha_formateada_w}. Revisado y pendiente de abono."
            url_whatsapp = f"https://wa.me/34650184254?text={urllib.parse.quote(texto_w)}"
            
            st.markdown(f"""
                <div style="margin-top: 15px; text-align: center;">
                    <a href="{url_whatsapp}" target="_blank" style="background: #25D366; color: #FFFFFF; padding: 12px 20px; border-radius: 12px; font-weight: 800; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);">
                        Avisar por WhatsApp al Tesorero
                    </a>
                </div>
            """, unsafe_allow_html=True)

# --- PESTAÑA 2: HISTORIAL DE GASTOS ---
with tab_historial:
    st.markdown("<p style='color: #FFD700; font-size: 15px; font-weight: 800; letter-spacing: 0.5px;'>REGISTRO HISTÓRICO DE GASTOS</p>", unsafe_allow_html=True)
    
    if not st.session_state.gastos.empty:
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
            
        with st.expander("Ver resumen de gastos por colaborador"):
            resumen_colab = st.session_state.gastos.groupby("Usuario")["Importe"].sum().reset_index()
            for _, rcol in resumen_colab.iterrows():
                st.write(f"• **{rcol['Usuario']}**: {formato_espanol(rcol['Importe'])} €")
        
        st.write("")
        
        if df_view.empty:
            st.info("No hay gastos que coincidan con el filtro seleccionado.")
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
                            <span style="color: #DDDDDD;">Colaborador:</span> <b>{row['Usuario']}</b> &nbsp;|&nbsp; <span style="color: #DDDDDD;">Fecha:</span> {fecha_visual} &nbsp;|&nbsp; <span style="color: #FFD700; font-weight: 800; font-size: 14px;">{formato_espanol(row['Importe'])} €</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

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

# --- PESTAÑA 3: PANEL DE ADMINISTRACIÓN ---
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
        
        st.markdown("#### Confirmar Reembolso / Abono a Colaboradores")
        pendientes_df = st.session_state.gastos[st.session_state.gastos["Reembolsado"] == False] if not st.session_state.gastos.empty else pd.DataFrame()
        
        if pendientes_df.empty:
            st.info("No hay gastos pendientes de abono en este momento.")
        else:
            for idx, prow in pendientes_df.iterrows():
                col_ab1, col_ab2 = st.columns([3, 1])
                with col_ab1:
                    st.write(f"**#{prow['ID']} - {prow['Usuario']}**: {formato_espanol(prow['Importe'])} € ({prow['Concepto']})")
                with col_ab2:
                    if st.button("Abonar", key=f"abonar_{prow['ID']}"):
                        st.session_state.gastos.loc[st.session_state.gastos['ID'] == prow['ID'], 'Reembolsado'] = True
                        st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
                        st.success(f"Gasto #{prow['ID']} marcado como abonado")
                        st.rerun()
        
        st.divider()
        
        st.markdown("#### Eliminar Gastos Erróneos o de Prueba")
        if not st.session_state.gastos.empty:
            gasto_a_borrar = st.selectbox("Selecciona gasto a eliminar", st.session_state.gastos["ID"].astype(str) + " - " + st.session_state.gastos["Usuario"] + " (" + st.session_state.gastos["Importe"].astype(str) + "€)")
            if st.button("Eliminar Gasto Seleccionado"):
                g_id = int(gasto_a_borrar.split(" - ")[0])
                fich_asociado = st.session_state.gastos.loc[st.session_state.gastos['ID'] == g_id, 'Fichero'].values[0]
                if fich_asociado and isinstance(fich_asociado, str):
                    p_f = os.path.join(RECEIPTS_DIR, fich_asociado)
                    if os.path.exists(p_f):
                        os.remove(p_f)
                st.session_state.gastos = st.session_state.gastos[st.session_state.gastos['ID'] != g_id]
                st.session_state.gastos.to_excel(EXCEL_FILE, index=False)
                st.success("¡Gasto eliminado correctamente!")
                st.rerun()
        else:
            st.info("No hay gastos para eliminar.")
        
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
                    st.success("Paquete de auditoría generado con éxito")
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
                st.success("Saldo base actualizado correctamente")
                st.rerun()
            
            st.divider()
            
            st.markdown("#### Añadir Nuevo Colaborador")
            nuevo_colab = st.text_input("Nombre o mote del colaborador")
            if st.button("Registrar Colaborador"):
                if nuevo_colab and nuevo_colab not in st.session_state.usuarios and nuevo_colab not in st.session_state.admins:
                    st.session_state.usuarios.append(nuevo_colab)
                    st.success(f"Colaborador '{nuevo_colab}' añadido con éxito")
                    st.rerun()
                else:
                    st.error("Introduce un nombre válido o que no esté duplicado.")

st.divider()

if logo_fuego_file:
    html_i = render_logo_png(logo_fuego_file, width=170)
    if html_i:
        st.markdown(html_i, unsafe_allow_html=True)

st.markdown('<div class="somos-fuego-footer">Somos fuego</div>', unsafe_allow_html=True)
