# Pruebas manuales — Fase 2

## Antes de empezar

- Mantén `app.py` sin cambios.
- Usa solo la aplicación de pruebas y las cuentas ficticias existentes.
- No introduzcas datos personales ni adjuntes tickets reales.

## Alta mediante invitación

1. Accede como `Prueba Safara`, la persona administradora creada en Fase 1.
2. En Administración, crea un código de alta con validez de un día y cópialo.
3. Cierra sesión. En `UNIRSE AL GRUPO`, comprueba que se pide el código de
   invitación.
4. Intenta registrar una cuenta ficticia sin código: debe rechazarse.
5. Registra `Prueba Tres` con el código creado: debe permitir el alta.
6. Intenta usar el mismo código para otra cuenta: debe rechazarse.

## Tickets

1. Prueba a adjuntar un archivo de texto con extensión `.pdf`: debe rechazarse.
2. Prueba un PDF, PNG o JPG real de prueba inferior a 10 MB: debe aceptarse.
3. No adjuntes justificantes reales ni documentos con datos personales.

## Contenido mostrado

1. Como administrador, crea una actuación de prueba cuyo título incluya
   caracteres como `<` y `>`.
2. Comprueba que se muestra como texto y no altera la página.

## Resultado esperado

La alta pública libre queda cerrada, los códigos son de un solo uso y las
cargas inválidas no llegan al directorio de recibos.
