# SAFARA GASTOS 1.0 — Fase 3 técnica

Fecha: 15 de noviembre de 2026

## Alcance

Esta fase mantiene intactos el diseño visual y `app.py`. Refuerza la
persistencia local y evita conexiones externas accidentales en
`app_safara_test.py`.

## Mejoras

- Votos, actuaciones, mensajes, gastos, saldo y reembolsos se guardan de forma
  atómica: un fallo no sustituye el fichero previo por uno incompleto.
- Si no se puede guardar un dato, la interfaz informa del error y revierte el
  cambio en memoria cuando es posible.
- Se genera `auditoria_safara.log` con eventos técnicos mínimos: altas,
  inicios de sesión, votos, gastos, invitaciones y ajustes. No guarda
  contraseñas, códigos ni secretos.
- Google Sheets queda desactivado por defecto, incluso aunque permanezcan
  credenciales antiguas en Streamlit. Solo se habilita con
  `enable_google_sheets_sync = true` tras autorización explícita.
- Cuando Google Sheets está desactivado, las actuaciones se crean y guardan en
  local sin bloquear el uso de la aplicación de pruebas.

## Pendientes

- Excel local no resuelve edición simultánea entre varias personas ni aporta
  copia de seguridad compartida. La migración de almacenamiento se tratará
  antes de producción.
- La integración Google Sheets requiere revisión de permisos mínimos y una
  autorización específica antes de activarla.
