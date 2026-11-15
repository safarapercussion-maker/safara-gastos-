# SAFARA GASTOS 1.0 — Fase 2 técnica

Fecha: 15 de noviembre de 2026

## Alcance

Esta fase no cambia `app.py` ni rediseña la interfaz. Se entrega únicamente
para `app_safara_test.py` y sus auxiliares de seguridad.

## Mejoras

- Tras la primera administración, las altas ya no quedan abiertas al público.
  Una persona administradora crea códigos individuales, de un solo uso y con
  caducidad de 1, 7 o 30 días.
- Los códigos se guardan únicamente como hash en
  `invitaciones_safara_v2.xlsx`; el código legible se muestra una vez a quien
  lo crea.
- Las cargas de tickets se limitan a 10 MB y se comprueba que el contenido
  coincide con PNG, JPG/JPEG o PDF antes de guardarlo.
- Se escapan textos controlados por usuarios antes de insertarlos en bloques
  HTML: mensajes, gastos, saludo, agenda y ticker.
- Se añaden pruebas automáticas de invitaciones y validación de ficheros.

## Pendientes conocidos

- Los ficheros Excel locales siguen sin resolver concurrencia ni copias de
  seguridad compartidas. Eso se tratará antes de una puesta en producción.
- Los secretos heredados de la aplicación de pruebas que apuntan al proyecto
  Supabase eliminado se retirarán en una limpieza de configuración; no se crea
  ni se reconecta ningún proyecto Supabase.
