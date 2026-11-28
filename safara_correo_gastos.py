"""Envía avisos de gastos registrados al buzón de tesorería."""

import logging
import smtplib
import ssl
import uuid
from dataclasses import dataclass, field
from email.message import EmailMessage

logger = logging.getLogger(__name__)
DESTINO_SAFARA = "safarapercussion@gmail.com"


@dataclass(frozen=True)
class CorreoGastosConfig:
    remitente: str
    contrasena_aplicacion: str = field(repr=False)

    @classmethod
    def from_secrets(cls, secrets):
        values = secrets.get("safara_correo_gastos", {})
        remitente = str(values.get("remitente", "")).strip()
        password = "".join(str(values.get("contrasena_aplicacion", "")).split())
        if not remitente.endswith("@gmail.com") or len(password) != 16:
            return None
        return cls(remitente, password)


def crear_aviso_gasto(remitente, gasto):
    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = DESTINO_SAFARA
    mensaje["Subject"] = f"SAFARA · Gasto pendiente de abono · {gasto['referencia']}"
    fecha = gasto["fecha"].strftime("%d/%m/%Y")
    importe = f"{gasto['importe']:.2f}".replace(".", ",")
    mensaje.set_content(
        f"Registrado por: {gasto['usuario']}\n"
        f"Referencia: {gasto['referencia']}\n"
        f"Fecha del gasto: {fecha}\n"
        f"Concepto: {gasto['concepto']}\n"
        f"Importe: {importe} €\n\n"
        "El justificante está disponible en el Historial de Gastos de la app.\n"
    )
    return mensaje


def enviar_aviso_gasto(database, config, gasto_id):
    """Procesa un gasto guardado y conserva el estado aunque falle Gmail."""
    intento = str(uuid.uuid4())
    try:
        gasto = database.reservar_aviso_gasto(gasto_id, intento)
        if gasto is None:
            return False
        enviado = False
        try:
            mensaje = crear_aviso_gasto(config.remitente, gasto)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10,
                                  context=ssl.create_default_context()) as smtp:
                smtp.login(config.remitente, config.contrasena_aplicacion)
                smtp.send_message(mensaje)
                enviado = True
        except (OSError, smtplib.SMTPException):
            if not enviado:
                logger.warning("Gmail no confirmó el aviso del gasto %s", gasto_id)
        finally:
            database.cerrar_aviso_gasto(gasto_id, intento, enviado)
        return enviado
    except Exception:
        logger.warning("No se pudo completar el aviso del gasto %s", gasto_id)
        return False
