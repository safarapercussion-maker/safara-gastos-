# Fase 9 — Respuesta inmediata y encuestas vivas

Fecha: 21 de noviembre de 2026

## Objetivo

Reducir esperas perceptibles en acceso y votaciones sin relajar la persistencia
segura de Supabase ni bloquear a las personas usuarias mientras se actualiza la
información compartida.

## Cambios aplicados en pruebas

- Caché breve y segura de personas registradas y resultados de encuestas.
- Las encuestas se refrescan cada ocho segundos dentro de su propio bloque, sin
  recargar el resto de la aplicación.
- Cada voto se confirma en Supabase antes de aparecer como guardado y se hace
  visible inmediatamente tras esa confirmación.
- El guardado de un voto resuelve la persona y actualiza su respuesta en una
  única operación de base de datos.
- La consulta del plan semanal de ensayo se reutiliza brevemente por sesión;
  los cambios de Administración invalidan esa copia al instante.
- La encuesta semanal permanente **¿Hoy se cena después del ensayo?** queda
  separada de la encuesta de disponibilidad y visible en Nuestras Movidas.

## Límites conscientes

El primer acceso tras una hibernación de Streamlit Community Cloud puede seguir
requerir el arranque del servicio. El uso normal mientras la aplicación está
activa no repite ese arranque y se beneficia de las mejoras anteriores.
