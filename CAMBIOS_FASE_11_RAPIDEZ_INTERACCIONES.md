# Fase 11 — Rapidez de interacciones

Este ajuste mantiene la seguridad y persistencia en Supabase, pero evita que
una acción pequeña reconstruya toda la aplicación.

- Las respuestas de encuestas de ensayo, cena y bolos se actualizan dentro de
  su propio bloque. Al votar no se vuelve a cargar la portada completa.
- Los resultados compartidos se consultan como máximo una vez cada quince
  segundos por instancia. El voto de quien pulsa se refleja de inmediato en su
  pantalla y se confirma primero en Supabase.
- El ajuste de saldo de caja se ejecuta en un bloque independiente: la
  confirmación no vuelve a construir todo el panel de administración.
- La lista de acceso se reutiliza durante cinco minutos; una alta, baja o
  cambio de rol la invalida de inmediato para que nunca se muestre un dato
  antiguo.
- La planificación semanal de ensayo queda en memoria un minuto y se invalida
  de inmediato al modificarla desde Administración.

## Límite del alojamiento de pruebas

La primera carga después de que Streamlit Community Cloud suspenda la app
depende del propio alojamiento. No se puede eliminar por código. Las acciones
posteriores y las interacciones normales sí se han aislado para ser ágiles.
La aplicación definitiva deberá utilizar alojamiento siempre activo para que
no exista ese tiempo de reactivación.
