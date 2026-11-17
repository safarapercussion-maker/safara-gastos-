# SAFARA GASTOS 1.0 — Fase 6: continuidad e informes seguros

## Corrección complementaria de pruebas

- La sesión se reinicia automáticamente al cambiar entre almacenamiento local, Google y Supabase. De este modo no puede interpretar usuarios antiguos como si pertenecieran a la nueva base segura.
- Una incidencia de conexión con Supabase ya no se muestra como un código de invitación inválido: se informa de que el alta no se ha creado y de que debe revisarse la conexión privada.
- Las credenciales incorrectas se detectan con un mensaje específico y la aplicación corta los reintentos durante ese arranque para no saturar el agrupador seguro de conexiones.
- El permiso de Administración se puede conceder o retirar desde el panel de una persona administradora. Cada cambio queda registrado y nunca se puede retirar el último acceso de Administración.
- La aplicación reutiliza un grupo pequeño de conexiones seguras y ya no ejecuta sincronizaciones de Google al abrir cada página. Esto reduce la espera inicial y los destellos de recarga.

## Alcance

Esta fase refuerza exclusivamente el entorno de pruebas. No modifica `app.py`, no altera la apariencia de la aplicación y no activa ninguna conexión externa por sí misma.

## Cambios funcionales

- Supabase se mantiene como registro principal de usuarios, invitaciones, votaciones, actuaciones, gastos, caja y auditoría.
- Google Sheets recibe una vista de consulta independiente, solo cuando Supabase esté activado y haya cambios pendientes.
- El informe de Sheets excluye contraseñas, hashes, teléfonos, fechas de nacimiento y códigos de invitación.
- Google Drive conserva los tickets originales y recibe copias administrativas en una subcarpeta separada.
- Si una subida de ticket llega a Drive pero falla el alta económica correspondiente, la aplicación intenta retirar ese archivo para no dejar un justificante sin registro.
- La sincronización de informes y las copias se ejecutan sin bloquear una votación, un gasto o cualquier otra acción de las personas usuarias.
- Se prepara una comprobación diaria para activarla cuando esta arquitectura se apruebe en la rama definitiva; mientras tanto puede ejecutarse manualmente en pruebas.

## Límites explícitos

- Google Sheets es un informe de consulta, no una vía para editar la aplicación. Los cambios manuales allí no se trasladan a Supabase y podrán ser sustituidos por la siguiente actualización.
- Las copias contienen gastos, caja y actuaciones; los tickets originales permanecen en Drive. No se incluyen mensajes privados ni datos personales innecesarios.
- La comprobación automática reduce el riesgo de pausa por inactividad en servicios gratuitos, pero no sustituye un servicio de disponibilidad garantizada.

## Activación pendiente y controlada

Cuando las pruebas de esta fase estén aprobadas, habrá una única acción manual: completar el secreto privado de conexión de Supabase en Streamlit y activar su uso. Esa conexión no se copia en GitHub ni se comparte por chat.
