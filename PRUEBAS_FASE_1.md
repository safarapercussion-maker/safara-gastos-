# Pruebas manuales — Fase 1

## Preparación local o en Streamlit de pruebas

1. Instala las dependencias de `requirements.txt`.
2. Genera un valor aleatorio de al menos 32 caracteres.
3. Configúralo como `bootstrap_admin_token` en los Secrets de la aplicación de
   pruebas. No lo añadas a ningún fichero versionado.
4. Ejecuta `streamlit run app_safara_test.py` desde este directorio.

## Comprobaciones de aceptación

1. Sin `usuarios_safara_v2.xlsx`, la lista de acceso no muestra usuarios y el
   formulario anuncia la primera alta administrativa.
2. Intenta la primera alta con un secreto incorrecto: no debe crearse ningún
   usuario ni fichero de usuarios válido.
3. Registra el administrador con el secreto correcto y una contraseña de al
   menos 12 caracteres que contenga letras y números.
4. Comprueba en `usuarios_safara_v2.xlsx` que no figura la contraseña en texto
   ni columnas de PIN; solo `password_salt` y `password_hash`.
5. Inicia sesión con una contraseña incorrecta cinco veces: debe bloquear el
   intento durante un minuto. Después, verifica el acceso con la correcta.
6. Registra una segunda persona. Debe obtener rol `usuario` y no entrar al
   panel de administración.
7. Como administrador, comprueba que el listado y su CSV no incluyen hashes,
   sales, contraseñas ni PINs. Intenta borrar al único administrador: debe
   rechazarse.
8. Cierra sesión y abre una URL como
   `?user=Admin&action=v_ens_si&voter=Admin`: no debe iniciar sesión ni votar.
9. Vota desde la interfaz autenticada; el voto debe quedar asociado únicamente
   al usuario de la sesión.
10. Recorre agenda, gastos y administración con una cuenta de cada rol. No
    configures credenciales de Google ni publiques cambios durante esta prueba.

## Pruebas automatizadas realizadas

Se han ejecutado correctamente cuatro pruebas unitarias de `safara_security.py`:
hash y verificación de contraseña, política de longitud, secreto inicial y
validación de nombres. También se ha comprobado la sintaxis de los archivos
Python y la ausencia de los mecanismos retirados mediante búsqueda estática.

## Rollback

Si una comprobación falla antes de publicar, revierte el commit de esta fase en
la rama de pruebas. `app.py` no necesita ninguna acción porque no forma parte de
la entrega. El fichero `usuarios_safara_v2.xlsx` queda separado del registro
anterior; consérvalo como evidencia de prueba o elimínalo manualmente solo si
quieres reiniciar de nuevo el alta inicial.
