# Auditoría de SAFARA GASTOS 1.0 — corte de Fase 1

Fecha de revisión: 15 de noviembre de 2026

## Límites de la revisión

Se ha revisado el ZIP disponible a través de su copia base de pruebas y se ha
trabajado en `app_safara_test.py`. No se ha cambiado `app.py`, no se ha
publicado código y no se han usado Google Sheets, WhatsApp ni otros servicios
externos.

## Hallazgos críticos corregidos en esta fase

| Hallazgo | Riesgo anterior | Estado |
| --- | --- | --- |
| Usuarios y credenciales de ejemplo en el código | Acceso no autorizado desde una instalación limpia | Corregido: el registro v2 empieza vacío |
| Identidad en `?user=` | Inicio de sesión sin contraseña | Corregido: no se leen parámetros de usuario |
| Votos con `voter` en URL | Cualquiera podía votar por otro usuario | Corregido: las acciones usan la sesión autenticada |
| Contraseñas/PIN en texto, recuperación y exportación | Divulgación de credenciales | Corregido: hash PBKDF2, sin recuperación ni exportación |
| Clave maestra de administrador en el código | Escalada total de privilegios | Corregido: rol del primer administrador mediante secreto externo |
| Número de WhatsApp incrustado | Exposición de dato personal y flujo externo no autorizado | Corregido: se ha retirado del entorno de pruebas |

## Hallazgos pendientes, no modificados todavía

| Prioridad | Hallazgo | Tratamiento previsto |
| --- | --- | --- |
| Alta | Excel y ficheros locales como base de datos | Migrar a almacenamiento compartido, transaccional y con copias de seguridad antes del lanzamiento |
| Alta | Cargas de tickets sin límite de tamaño ni comprobación real de formato | Limitar tamaño, validar contenido y aislar ficheros en Fase 2 |
| Alta | Textos de usuarios y datos de actuaciones interpolados con `unsafe_allow_html=True` | Escapar/sanitizar cada valor antes de mostrarlo en HTML en Fase 2 |
| Media | Excepciones silenciadas con `except: pass` | Sustituirlas por errores controlados y registro de auditoría |
| Media | Cuenta de Google con permisos de Drive y Sheets, y operaciones destructivas disponibles | Aplicar mínimo privilegio y revisar con autorización explícita |
| Media | Bloqueo de acceso solo por sesión de navegador | Añadir limitación persistente, auditoría y proceso de restablecimiento |
| Media | Fechas y actuaciones de ejemplo en la aplicación | Decidir en Fase 2 si deben conservarse como contenido de demostración o cargarse vacías |

## Dependencias

El código usaba exportación/importación Excel y Google Sheets, pero el fichero de
dependencias no declaraba todas sus bibliotecas. `requirements.txt` incorpora
`openpyxl`, `gspread` y `google-auth`. Declararlas no establece conexiones ni
modifica las credenciales existentes.
