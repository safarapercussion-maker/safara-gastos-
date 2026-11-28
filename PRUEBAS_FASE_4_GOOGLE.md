# Pruebas de Fase 4 — Google Sheets y Drive

## Antes de activar

- Hoja de pruebas compartida como editora con la cuenta técnica.
- Carpeta de justificantes compartida como editora con la misma cuenta.
- Google Sheets API y Google Drive API habilitadas en el proyecto correcto.
- Ninguna clave privada ni secreto se ha subido a GitHub.

## Prueba mínima

1. Activar la configuración de Google en Streamlit Secrets.
2. Abrir la aplicación de prueba y crear la persona administradora inicial.
3. Recargar la aplicación: la persona administradora debe seguir apareciendo.
4. Crear un código de alta, registrar una segunda persona y recargar.
5. Registrar un gasto con un justificante PNG, JPG o PDF válido.
6. Comprobar que el gasto aparece en la pestaña `Gastos` de la hoja y el archivo en la carpeta de Drive.
7. Actualizar la aplicación y comprobar que usuarios, invitaciones usadas y gastos siguen disponibles.

## Criterio de parada

Si la aplicación informa de que Google no está configurado o no puede escribir, no crear usuarios de prueba. Revisar primero los permisos de la hoja/carpeta y el contenido de Streamlit Secrets.

