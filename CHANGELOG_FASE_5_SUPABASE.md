Attempting to perform the InitializeDefaultDrives operation on the 'FileSystem' provider failed.
# SAFARA GASTOS 1.0 — Fase 5: base transaccional de pruebas

## Alcance

- Solo afecta a `app_safara_test.py` y sus auxiliares.
- `app.py` no se modifica.
- El diseño visual queda intacto.

## Resultado

- Supabase/PostgreSQL pasa a ser el origen único de los datos críticos de pruebas.
- Google Drive conserva el uso exclusivo de justificantes; las hojas quedan para informes posteriores.
- La información se protege en un espacio privado, no expuesto como API pública.
- Las altas, invitaciones de un solo uso, votos, actuaciones, gastos, reembolsos, caja y mensajes usan operaciones atómicas.
- Se añaden restricciones, índices y registro de auditoría para concurrencia.

## Activación

1. Añadir la URL privada de la base creada a los Secrets de Streamlit.
2. Activar `enable_supabase_storage`.
3. Mantener configurado Google únicamente para los justificantes.
4. Reiniciar la aplicación de pruebas y crear un nuevo primer administrador.

No se incluyen secretos, contraseñas, usuarios ni datos reales en el repositorio.

