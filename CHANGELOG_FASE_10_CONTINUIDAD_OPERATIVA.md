# Fase 10 — Continuidad operativa automática

Fecha: 21 de noviembre de 2026

## Mejora aplicada

La comprobación automática de la aplicación de pruebas se ejecuta ahora cuatro
veces al día, cada seis horas. Con ello:

- se reduce el riesgo de que Streamlit entre en reposo por inactividad;
- se mantiene actividad regular frente a la base segura de pruebas;
- cualquier incidencia de disponibilidad queda visible en la ejecución
  automática, antes de una jornada de uso del grupo.

## Garantía realista

Es una medida preventiva y sin coste adicional, no un servicio de disponibilidad
garantizada. Una interrupción del proveedor o un retraso excepcional del
planificador puede seguir requerir el arranque normal de la aplicación.
