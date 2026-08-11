import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core import settings
from app.tasks.celery_app import celery_app
from app.utils.templates import get_template

logger = logging.getLogger(__name__)


@celery_app.task
def send_confirmation_email(receiver_address: str, token: str) -> str:
    message = EmailMessage()

    message["From"] = settings.SENDER_EMAIL_ADDRESS
    message["To"] = receiver_address
    message["Subject"] = "Deplocker account activation request"

    confirmation_url = f"{settings.FRONTEND_URL}/account/confirm?email={receiver_address}&token={token}"
    context_data = {"confirmation_url": confirmation_url}
    html_content = get_template(
        "account_confirmation_email.html", context_data=context_data
    )

    message.set_content(html_content, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(settings.SENDER_EMAIL_ADDRESS, settings.EMAIL_HOST_PASSWORD)
            server.send_message(message)

    except Exception as e:
        logger.error(
            "Email confirmation for account activation failed to send!",
            extra={"receiver_address": receiver_address, "error": str(e)},
        )
        raise

    return f"Account confirmation email was successfully sent to {receiver_address}"
