# Lanzamiento de SAFARA

La app definitiva conserva https://safara-gastos.streamlit.app/ y usa `app.py`. El entorno de pruebas conserva su enlace, su rama y sus datos. Esta rama reúne la versión técnica vigente en pruebas con un arranque que exige un proyecto de producción separado.

## Preparar el proyecto vacío

1. Crear el proyecto **SAFARA GASTOS — Producción** en la organización confirmada, en la región de Irlanda y dentro del plan gratuito. Aplicar en orden los SQL de `supabase/migrations/` y después `deploy/cierre_ensayos_produccion.sql`. Estos archivos preparan la estructura y los valores técnicos de arranque, incluido el saldo de 0 €. No importar datos de pruebas ni cargar hojas Excel antiguas.
2. Confirmar en SQL que `safara.usuarios`, `safara.invitaciones`, `safara.gastos`, `safara.votos`, `safara.actuaciones` y `safara.ensayos_historial` estén vacías. Confirmar que los roles `anon` y `authenticated` no pueden leer el esquema privado y que la tarea semanal está activa.
3. Preparar una hoja de informes y un destino de Drive exclusivos de producción. Dar permiso de edición a la cuenta técnica únicamente en la hoja que deba actualizar. Añadir en Google Cloud la URL de retorno exacta `https://safara-gastos.streamlit.app/`.
4. Preparar los Secrets a partir de `deploy/secrets.produccion.example.toml`. Usar el pooler de **sesión** del proyecto de producción y una clave de activación recién generada. Guardar ahí la contraseña de aplicación de Gmail de producción y una clave Fernet nueva. Nunca copiar los Secrets completos de pruebas. Guardar la configuración anterior en un lugar privado como parte de la recuperación.

## Activar y comprobar

1. Registrar el commit vigente de `main` y preparar la copia de seguridad de cualquier dato real que ya existiera. Promover la rama de lanzamiento y cargar los Secrets de la app definitiva en la ventana de activación acordada. Si Streamlit mezcla una versión anterior de los módulos con `app.py`, reiniciar solo la instancia definitiva y abrir una sesión nueva.
2. El responsable se da de alta con la clave de activación y elige su contraseña. Confirmar que entra en Administración. Retirar la clave de activación de Secrets al terminar. Autorizar Drive desde Administración → Control con la cuenta de SAFARA y confirmar el destino efectivo de la carpeta de justificantes.
3. Comprobar una segunda alta con invitación de un solo uso y verificar que aparece como usuario normal. El primer administrador puede otorgarle permisos desde Administración → Safarers.
4. Verificar acceso tras refrescar, votos de ensayo y cena, los estados de bolos, revisión por instrumento y un gasto controlado. Comprobar la coincidencia de referencia y titular en la app, Drive, Sheets y Gmail y, tras el cierre de la prueba, el estado de abono.
5. Iniciar un piloto pequeño en diciembre y ampliar las invitaciones tras comprobarlo. Mantener las mejoras visuales primero en la app de pruebas.

## Recuperar el servicio

Si falla antes de abrir al grupo, pausar las invitaciones y volver a desplegar el commit anterior con su configuración archivada. Si ya hay usuarios o gastos reales en Supabase, conservar ese proyecto y sus registros. Antes de volver a un código anterior, verificar que puede leerlos y escribirlos correctamente; si no, dejar el acceso en mantenimiento hasta aplicar una corrección compatible. No restaurar sobre la base activa sin revisar primero las altas y los gastos posteriores a la copia.
