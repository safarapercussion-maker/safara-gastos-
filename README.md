# Safara Gastos

La aplicación oficial permanece en `app.py`. El entorno de pruebas ejecuta
`app_safara_test.py`, que delega en `secure_app.py`.

El entorno de pruebas exige una base de datos PostgreSQL configurada mediante
Secretos de Streamlit. Nunca debe usar archivos Excel, PINs de ejemplo ni
archivos de tickets locales como almacenamiento de producción.
