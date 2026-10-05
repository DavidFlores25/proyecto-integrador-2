import smtplib
import ssl
from email.message import EmailMessage

import config


def correo_configurado():
    return bool(config.CORREO_REMITENTE.strip()) and bool(config.CLAVE_APLICACION.strip())


def enviar_correo_reserva_aceptada(destino, nombre, dia, inicio, fin, mesas, personas):
    """Envía la confirmación al cliente. Devuelve (ok, mensaje). Nunca lanza excepciones."""
    if not correo_configurado():
        return False, "El correo del restaurante aún no está configurado (archivo config.py)."

    mesas_str = ", ".join(map(str, mesas))

    msg = EmailMessage()
    msg["Subject"] = f"Reserva confirmada - {config.NOMBRE_RESTAURANTE}"
    msg["From"] = f"{config.NOMBRE_RESTAURANTE} <{config.CORREO_REMITENTE.strip()}>"
    msg["To"] = destino
    msg.set_content(
        f"Hola {nombre},\n\n"
        f"Tu reserva en {config.NOMBRE_RESTAURANTE} fue ACEPTADA.\n\n"
        f"Detalles de tu reserva:\n"
        f"  - Día: {dia}\n"
        f"  - Horario: {inicio} a {fin}\n"
        f"  - Personas: {personas}\n"
        f"  - Mesas: {mesas_str}\n\n"
        f"¡Te esperamos!\n"
        f"{config.NOMBRE_RESTAURANTE}\n"
    )

    clave = config.CLAVE_APLICACION.replace(" ", "")
    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SERVIDOR_SMTP, config.PUERTO_SMTP, context=contexto, timeout=20) as servidor:
            servidor.login(config.CORREO_REMITENTE.strip(), clave)
            servidor.send_message(msg)
        return True, "Correo enviado."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail rechazó el correo o la clave de aplicación. Revise el archivo config.py."
    except smtplib.SMTPRecipientsRefused:
        return False, "La dirección de correo del cliente no es válida."
    except (smtplib.SMTPException, OSError):
        return False, "No se pudo conectar con Gmail. Revise la conexión a internet."