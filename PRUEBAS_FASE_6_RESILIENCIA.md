# Pruebas — Fase 6: continuidad e informes seguros

## Aislamiento de almacenamiento

1. Activar Supabase desde una sesión que antes hubiese usado Google o archivos locales.
2. Recargar la aplicación.
3. Confirmar que la primera alta se identifica como inicial cuando la tabla segura no contiene usuarios.
4. Si la conexión a la base fallase, confirmar que aparece un aviso de conexión y no un mensaje incorrecto sobre el código de invitación.
5. Con una contraseña privada incorrecta, confirmar que la aplicación informa de ello sin repetir conexiones hasta que Streamlit se reinicie tras guardar la credencial correcta.
6. Como administración, autorizar a una persona usuaria y confirmar que, tras volver a iniciar sesión, accede al panel de Administración.
7. Retirar ese permiso y confirmar que deja de acceder al panel, conservando siempre al menos una persona administradora.
8. Confirmar que al abrir la aplicación no se ejecuta una sincronización de Google; dicha sincronización debe iniciarse únicamente desde Administración.

## Comprobaciones automáticas incluidas

- Las columnas de los informes de Google no incluyen campos sensibles.
- La copia administrativa contiene solo gastos, caja, actuaciones y un manifiesto verificable.
- Una sincronización correcta actualiza el informe y genera la copia prevista.
- Si no hay novedades, no se reescriben informes ni se crea una copia innecesaria.

## Comprobación operativa tras activar Supabase

1. Crear el primer usuario administrador de pruebas.
2. Crear una invitación y registrar una segunda persona.
3. Crear una actuación, emitir un voto y registrar un gasto con ticket.
4. Actualizar la página una vez más.
5. Confirmar que Supabase contiene la información de prueba.
6. Confirmar que aparecen las pestañas `Informe …` en la hoja compartida y que no muestran contraseñas, teléfonos, fechas de nacimiento ni códigos.
7. Confirmar que el ticket aparece en Drive y que existe la subcarpeta `SAFARA_GASTOS_COPIAS`.
8. Simular una interrupción temporal de Google solo si se acuerda explícitamente; la aplicación debe seguir guardando en Supabase y volver a sincronizar en un intento posterior.

## Resultado esperado

Las acciones del grupo se confirman contra Supabase. Una incidencia de Sheets o Drive no debe perder ni bloquear el registro central.
