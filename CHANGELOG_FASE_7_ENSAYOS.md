# SAFARA GASTOS 1.0 — Fase 7: ciclo semanal de ensayos

Fecha: 18/11/2026

## Incorporado

- Encuesta semanal gobernada por horario de Madrid: abre los lunes a las 08:00 y cierra los viernes a las 19:00.
- La semana del 16/11/2026 corresponde a Zizur; la siguiente corresponde a Barañain. La alternancia continúa automáticamente.
- Un ensayo solo queda confirmado con seis personas o más, al menos un Repenike y al menos una Caja.
- El cierre conserva un historial permanente en Supabase con fecha, ubicación, asistentes, Repenikes, Cajas y resultado.
- Las respuestas de una semana anterior nunca se eliminan ni se mezclan con la encuesta nueva.
- El cierre del viernes se ejecuta dentro de la base de datos, cada pocos minutos durante la franja necesaria, incluso aunque nadie abra la aplicación.

## Seguridad y rendimiento

- El historial solo se consulta desde el servidor de la aplicación; no queda publicado mediante acceso directo.
- El cierre está protegido para que dos personas accediendo simultáneamente no creen resultados distintos.
- No se añadieron servicios de pago ni se modificó `app.py`.
