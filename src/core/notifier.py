import os
import smtplib
from typing import List
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER   = os.getenv("SMTP_SERVER")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL")
RECIPIENTS    = [addr.strip() for addr in os.getenv("MAIL_RECIPIENTS", "").split(",") if addr.strip()]

def send_order_email(
    order_data: dict,
    attachment_bytes: bytes = None,
    attachment_name: str = None,
    additional_bytes_list: List[bytes] = None,
    additional_names_list: List[str] = None
) -> None:
    """
    Verschickt eine E-Mail mit allen Auftragsdaten.
    Hängt die Haupt-3D-Datei an und bis zu 5 optionale Anhänge.
    """
    msg = EmailMessage()
    subject = f"Neuer Auftrag: {order_data.get('auftragstyp', 'Unbekannt')}"
    if order_data.get('firma'):
        subject += f" von {order_data['firma']}"
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENTS

    # Body aus order_data
    lines = [f"{k}: {v}" for k, v in order_data.items()]
    msg.set_content("\n".join(lines))

    # 1) Haupt-Anhang
    if attachment_bytes and attachment_name:
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="octet-stream",
            filename=attachment_name
        )

    # 2) Zusätzliche Anhänge
    if additional_bytes_list and additional_names_list:
        for data, name in zip(additional_bytes_list, additional_names_list):
            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=name
            )

    # SMTP-Versand mit explizitem Connect und EHLO/STARTTLS
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.connect(SMTP_SERVER, SMTP_PORT)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)
