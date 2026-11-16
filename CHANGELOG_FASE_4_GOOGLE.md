# SAFARA GASTOS 1.0 — Fase 4: persistencia en Google

## Alcance

- Solo modifica `app_safara_test.py` y auxiliares de la versión de pruebas.
- `app.py` permanece sin cambios.
- No se reutiliza ninguna hoja histórica de gastos ni el proyecto de Supabase eliminado.

## Cambios

- Nuevo adaptador `safara_google_storage.py` para la hoja y carpeta de pruebas autorizadas.
- Usuarios, invitaciones, votos, actuaciones, gastos, saldo, confesionario y auditoría se preparan para almacenarse en la hoja de Google.
- Los justificantes validados se suben a la carpeta de Drive configurada y el gasto conserva su enlace.
- Si la integración de Google se activa sin credenciales válidas, la app no escribe una copia local efímera.
- Se elimina el uso de la hoja histórica de actuaciones cuando la nueva integración está activa.

## Seguridad

- La cuenta técnica solo tiene acceso a la hoja y carpeta de pruebas compartidas.
- Las contraseñas conservan su hash PBKDF2; no se guardan en texto visible.
- Las claves privadas se almacenan exclusivamente en Streamlit Secrets, nunca en GitHub.
- Las subidas mantienen la validación de extensión, tamaño y firma de archivo de las fases anteriores.

## Pendiente de activación controlada

1. Crear la clave JSON de la cuenta de servicio.
2. Copiarla a Streamlit Secrets con la configuración de ejemplo.
3. Activar `enable_google_sheets_sync = true`.
4. Subir solo los archivos de Fase 4 a la rama de pruebas y comprobar el alta inicial.

