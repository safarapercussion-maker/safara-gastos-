# SAFARA GASTOS 1.0 — Fase 1 de seguridad

Fecha: 15 de noviembre de 2026

## Alcance entregado

- Se modifica únicamente el entorno de pruebas: `app_safara_test.py` y sus
  auxiliares imprescindibles. `app.py` no se ha modificado.
- Se elimina la carga de usuarios heredados y todo usuario, PIN, clave maestra
  o administrador predefinido del código de pruebas.
- El registro seguro usa `usuarios_safara_v2.xlsx`, un fichero nuevo. El
  registro anterior no se borra ni se lee: la prueba empieza sin cuentas.
- El primer registro exige `bootstrap_admin_token` desde Streamlit Secrets. Si
  se valida, recibe el rol `admin`; el secreto no se guarda en Excel ni en Git.
- Las contraseñas se guardan como PBKDF2-HMAC-SHA256 con sal aleatoria e
  iteraciones elevadas; nunca se muestran, envían por WhatsApp ni exportan.
- Se suprimen la autenticación y las votaciones mediante parámetros URL. Las
  votaciones se realizan desde una sesión autenticada.
- El panel administrativo usa el rol de la sesión, no una segunda contraseña
  universal. Tampoco permite eliminar al último administrador.
- Se añade una pausa de un minuto tras cinco intentos fallidos de inicio de
  sesión dentro de la misma sesión del navegador.
- Se añaden dependencias declaradas para la persistencia Excel y la integración
  de Google Sheets ya existente, sin realizar llamadas externas durante esta
  actualización.

## Ficheros incluidos

- `app_safara_test.py`: aplicación de pruebas actualizada, manteniendo el CSS,
  estructura de pestañas, textos e identidad visual existentes.
- `safara_security.py`: funciones locales y comprobables para contraseña,
  validación y bootstrap.
- `requirements.txt`: dependencias declaradas.
- `secrets.example.toml`: plantilla sin secretos reales.
- `tests/test_safara_security.py`: pruebas automáticas de los controles nuevos.

## Pendiente para fases posteriores

- Sustituir los ficheros Excel locales por almacenamiento compartido y con
  control de concurrencia antes de abrir la aplicación a más personas.
- Diseñar recuperación de contraseña y gestión de altas/bajas con verificación
  de identidad, sin enviar credenciales por mensajería.
- Revisar y reforzar cargas de justificantes, sanitización de todos los textos
  mostrados como HTML y trazabilidad administrativa.
- Revisar permisos mínimos y errores de la integración de Google Sheets sin
  tocar esa cuenta hasta recibir autorización explícita.
