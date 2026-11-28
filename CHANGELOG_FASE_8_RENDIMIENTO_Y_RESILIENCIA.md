# SAFARA GASTOS 1.0 — Fase 8: rendimiento y resiliencia

Fecha: 18/11/2026

## Mejoras aplicadas

- Las imágenes estáticas se conservan en memoria de forma segura durante la sesión de la aplicación, evitando lecturas repetidas en cada interacción.
- La consulta del historial de ensayos se limita a una vez por minuto y se actualiza de inmediato al cambiar de ciclo semanal.
- Un fallo temporal de red con Supabase ya no deja la aplicación bloqueada hasta el siguiente reinicio; las siguientes acciones pueden recuperar la conexión.
- Las copias administrativas incluyen ahora una huella de integridad de cada archivo incluido.
- Una repetición de una copia diaria sustituye la misma copia de ese día en Drive, en vez de generar duplicados.

## Límites deliberados

- La autorización de Drive sigue pendiente de la cuenta propietaria de Google; no se ha intentado simularla ni sustituirla con credenciales inseguras.
- No se modifica el diseño, `app.py` ni el entorno definitivo.
