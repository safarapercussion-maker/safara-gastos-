import streamlit as st
import pandas as pd
import datetime
import os
import zipfile
import io

# Configuración de la página con estética Safara
st.set_page_config(page_title="Safara Percussion - Gestión de Gastos", page_icon="🥁", layout="wide")

# Estilos CSS personalizados inspirados en la identidad visual de Safara (Negro y Amarillo vibrante)
st.markdown("""
    <style>
    .main { background-color: #FAFAFA; }
    .stButton>button { background-color: #000000; color: #FFEB3B; border-radius: 8px; font-weight: 700; border: 2px solid #FFEB3B; }
    .stButton>button:hover { background-color: #FFEB3B; color: #000000; }
    .safara-header { background-color: #000000; padding: 20px; border-radius: 12px; text-align: center; color: #FFEB3B; border-bottom: 4px solid #FF5722; }
    </style>
""", unsafe_allow_html=True)

RECEIPTS_DIR = "recibos_subidos"
os.makedirs(RECEIPTS_DIR, exist_ok=True)

# Base de datos simulada en memoria
if "banco_caja_rural" not in st.session_state:
    st.session_state.banco_caja_rural = 1250.50  # Saldo actual en Caja Rural

if "gastos" not in st.session_state:
    st.session_state.gastos = [
        {
            "id": 1,
            "fecha_gasto": datetime.date(2026, 10, 5),
            "hora_subida": "2026-10-05 16:30:00",
            "comercio": "Tam Tam Percusión",
            "importe": 89.40,
            "moneda": "EUR",
            "pagador": "Diego",
            "metodo_pago": "Tarjeta personal",
            "reembolsado": False,
            "ref_transferencia": "",
            "categoria": "Material y Recambios",
            "nota": "Compra de baquetas para ensayo",
            "recibo": "tam_tam_2026.png"
        }
    ]

# Configuración de usuarios de la asociación y los 5 administradores de la junta
if "usuarios_roles" not in st.session_state:
    st.session_state.usuarios_roles = {
        "Iñigo": "Administrador (Junta)",
        "Rosi": "Administrador (Junta)",
        "Xabi": "Administrador (Junta)",
        "Resano": "Administrador (Junta)",
        "Diego": "Administrador (Junta)",
        "Marta": "Miembro",
        "Jon": "Miembro",
        "Ana": "Miembro"
    }

CATEGORIAS_SAFARA = [
    "Material y Recambios",
    "Gasolina",
    "Kilometraje",
    "Peajes",
    "Parking",
    "Transporte / Furgoneta",
    "Dietas y Comidas",
    "Bebidas",
    "Alquiler de Local",
    "Otros gastos"
]

# Cabecera visual en la barra lateral con los colores de Safara
st.sidebar.markdown("""
    <div style="background-color: #000000; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #FFEB3B;">
        <h2 style="color: #FFEB3B; margin: 0; font-family: sans-serif;">SAFARA</h2>
        <p style="color: #FFFFFF; font-size: 12px; margin: 0;">PERCUSSION • PAMPLONA</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
usuario_activo = st.sidebar.selectbox("Selecciona tu usuario:", list(st.session_state.usuarios_roles.keys()))
rol_activo = st.session_state.usuarios_roles[usuario_activo]
st.sidebar.info(f"👤 Rol: **{rol_activo}**")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Menú Principal", ["Panel General y Saldos", "Registrar Gasto (Adelanto)", "Control de Reembolsos (Admin)", "Exportar para Hacienda (ZIP)"])

# ----------------- 1. PANEL GENERAL Y SALDOS -----------------
if menu == "Panel General y Saldos":
    st.markdown("""
        <div class="safara-header">
            <h1>🥁 SAFARA PERCUSSION</h1>
            <p>Panel de Transparencia Financiera y Cuentas de la Asociación</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    df_general = pd.DataFrame(st.session_state.gastos) if st.session_state.gastos else pd.DataFrame()
    
    total_gastado_ano = df_general["importe"].sum() if not df_general.empty else 0.0
    pendientes_pago = df_general[df_general["reembolsado"] == False]["importe"].sum() if not df_general.empty else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("🏦 Saldo Caja Rural", f"{st.session_state.banco_caja_rural:.2f} €")
    col2.metric("💸 Gastos Totales del Año", f"{total_gastado_ano:.2f} €")
    col3.metric("⏳ Pendiente Reembolsar", f"{pendientes_pago:.2f} €")

    st.markdown("---")
    st.subheader("📊 Gasto por Categorías")
    if not df_general.empty:
        gasto_cat = df_general.groupby("categoria")["importe"].sum()
        st.bar_chart(gasto_cat)
    else:
        st.info("No hay datos suficientes para mostrar gráficos todavía.")

# ----------------- 2. REGISTRAR GASTO -----------------
elif menu == "Registrar Gasto (Adelanto)":
    st.title("➕ Registrar Nuevo Gasto")
    st.markdown("Sube la foto del ticket del gasto que has pagado de tu bolsillo para solicitar el reembolso.")

    with st.form("form_gasto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            comercio = st.text_input("Comercio / Proveedor / Concepto*", placeholder="Ej. Peaje autopista / Gasolinera")
            importe = st.number_input("Importe (€)*", min_value=0.01, format="%.2f", value=0.00)
            fecha_gasto = st.date_input("Fecha del ticket*", value=datetime.date.today())
            
        with col2:
            metodo_pago = st.selectbox("Forma de pago inicial", ["Tarjeta personal", "Efectivo personal", "Transferencia personal"])
            categoria = st.selectbox("Categoría*", ["Obligatorio seleccionar..."] + CATEGORIAS_SAFARA)
            nota = st.text_area("Descripción / Justificación para Hacienda*", placeholder="¿Para qué ha sido este gasto?")

        archivo_recibo = st.file_uploader("Foto del Ticket / Factura*", type=["png", "jpg", "jpeg", "pdf"])
        
        submitted = st.form_submit_button("Guardar Gasto en Safara")
        
        if submitted:
            if not comercio or importe <= 0 or categoria == "Obligatorio seleccionar..." or not nota or not archivo_recibo:
                st.error("⚠️ Rellena todos los campos obligatorios, selecciona una categoría y adjunta el ticket.")
            else:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename_safe = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo_recibo.name}"
                file_path = os.path.join(RECEIPTS_DIR, filename_safe)
                
                with open(file_path, "wb") as f:
                    f.write(archivo_recibo.getbuffer())
                
                nuevo_gasto = {
                    "id": len(st.session_state.gastos) + 1,
                    "fecha_gasto": fecha_gasto,
                    "hora_subida": now_str,
                    "comercio": comercio,
                    "importe": importe,
                    "moneda": "EUR",
                    "pagador": usuario_activo,
                    "metodo_pago": metodo_pago,
                    "reembolsado": False,
                    "ref_transferencia": "",
                    "categoria": categoria,
                    "nota": nota,
                    "recibo": filename_safe
                }
                st.session_state.gastos.append(nuevo_gasto)
                st.success(f"✅ ¡Gasto guardado correctamente por **{usuario_activo}**! Queda pendiente de reembolso.")

# ----------------- 3. CONTROL DE REEMBOLSOS (SOLO ADMINS) -----------------
elif menu == "Control de Reembolsos (Admin)":
    if "Administrador" not in rol_activo:
        st.error("🔒 Acceso restringido. Esta sección de administración y control de Caja Rural es exclusiva para los 5 miembros de la junta (Iñigo, Rosi, Xabi, Resano y Diego).")
    else:
        st.title("🔒 Panel de Administración y Reembolsos")
        st.markdown("Gestión de transferencias, marcado de checks y actualización del saldo de Caja Rural.")

        with st.expander("🏦 Actualizar Saldo Real de Caja Rural (Solo Admins)"):
            nuevo_saldo_banco = st.number_input("Introduce el saldo actual que marca la app de Caja Rural (€):", value=float(st.session_state.banco_caja_rural), format="%.2f")
            if st.button("Actualizar Saldo en Safara"):
                st.session_state.banco_caja_rural = nuevo_saldo_banco
                st.success(f"✅ Saldo de Caja Rural actualizado a {nuevo_saldo_banco:.2f} € visible para todos los socios.")

        st.markdown("---")

        if not st.session_state.gastos:
            st.info("No hay gastos registrados.")
        else:
            df = pd.DataFrame(st.session_state.gastos)
            pendientes_df = df[df["reembolsado"] == False]
            
            tab_pendientes, tab_confirmados = st.tabs(["⏳ Pendientes de Reembolso", "✅ Reembolsados y Confirmados"])
            
            with tab_pendientes:
                if pendientes_df.empty:
                    st.success("🎉 ¡No hay reembolsos pendientes en este momento!")
                else:
                    for idx, row in df[df["reembolsado"] == False].iterrows():
                        st.markdown(f"""
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #FF5722; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h4 style="margin:0; color:#111;">{row['comercio']} - {row['importe']:.2f} {row['moneda']}</h4>
                            <p style="margin: 4px 0; font-size:14px; color:#555;"><b>Pagado por:</b> {row['pagador']} | <b>Fecha:</b> {row['fecha_gasto']} | <b>Categoría:</b> {row['categoria']}</p>
                            <p style="margin: 4px 0; background:#F8F9FA; padding:6px; border-radius:4px;"><b>Nota:</b> {row['nota']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_chk, col_ref = st.columns([1, 2])
                        with col_chk:
                            marcar_reembolsado = st.checkbox("✅ Marcar Reembolso Efectuado", key=f"chk_{row['id']}")
                        with col_ref:
                            ref_trans = st.text_input("Ref. Transferencia Caja Rural", key=f"ref_{row['id']}", placeholder="Ej. TR-2026-00123")
                        
                        if marcar_reembolsado:
                            st.session_state.gastos[idx]["reembolsado"] = True
                            st.session_state.gastos[idx]["ref_transferencia"] = ref_trans if ref_trans else "Transferencia Caja Rural"
                            st.success(f"¡Reembolso a {row['pagador']} marcado como completado!")
                            st.rerun()
                        st.markdown("---")

            with tab_confirmados:
                confirmados_df = df[df["reembolsado"] == True]
                if confirmados_df.empty:
                    st.info("Aún no hay gastos marcados como reembolsados.")
                else:
                    for idx, row in confirmados_df.iterrows():
                        st.markdown(f"""
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #4CAF50; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h4 style="margin:0; color:#111;">{row['comercio']} - {row['importe']:.2f} {row['moneda']}</h4>
                            <p style="margin: 4px 0; font-size:14px; color:#555;"><b>Pagado por:</b> {row['pagador']} | <b>Fecha:</b> {row['fecha_gasto']} | <b>Ref:</b> <i>{row['ref_transferencia']}</i></p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("↩️ Deshacer y pasar a pendiente", key=f"deshacer_{row['id']}"):
                            st.session_state.gastos[idx]["reembolsado"] = False
                            st.session_state.gastos[idx]["ref_transferencia"] = ""
                            st.rerun()

# ----------------- 4. EXPORTAR PARA HACIENDA -----------------
elif menu == "Exportar para Hacienda (ZIP)":
    st.title("📥 Safara: Exportación Contable")
    st.markdown("Genera el archivo Excel detallado y la carpeta organizada con todos los recibos para la justificación.")

    if st.button("🚀 Generar Paquete ZIP Contable de Safara"):
        excel_buffer = io.BytesIO()
        df_exp = pd.DataFrame(st.session_state.gastos)
        df_exp.to_excel(excel_buffer, index=False, sheet_name="Gastos")
        excel_bytes = excel_buffer.getvalue()
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("Contabilidad_Safara.xlsx", excel_bytes)
            for g in st.session_state.gastos:
                path = os.path.join(RECEIPTS_DIR, g["recibo"])
                if os.path.exists(path):
                    zip_file.write(path, arcname=f"recibos_safara/{g['recibo']}")
                    
        zip_buffer.seek(0)
        st.download_button("⬇️ Descargar ZIP Contable Safara", data=zip_buffer, file_name="Contabilidad_Safara_Gastos.zip", mime="application/zip")
