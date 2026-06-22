import httpx
from app.config import get_settings


async def send_newsletter(subject: str, body_html: str, recipient_list: dict) -> None:
    settings = get_settings()
    emails = recipient_list.get("emails", [])
    if not emails:
        return

    if settings.sendgrid_api_key:
        await _send_via_sendgrid(subject, body_html, emails, settings)
    elif settings.mailgun_api_key:
        await _send_via_mailgun(subject, body_html, emails, settings)
    else:
        raise RuntimeError("No email delivery provider configured")


async def _send_via_sendgrid(subject: str, body_html: str, emails: list[str], settings) -> None:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, To

    sg = SendGridAPIClient(settings.sendgrid_api_key)
    message = Mail(
        from_email=(settings.sendgrid_from_email, settings.sendgrid_from_name),
        subject=subject,
        html_content=body_html,
    )
    message.to = [To(email) for email in emails]

    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: sg.send(message))


async def _send_via_mailgun(subject: str, body_html: str, emails: list[str], settings) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.mailgun.net/v3/{settings.mailgun_domain}/messages",
            auth=("api", settings.mailgun_api_key),
            data={
                "from": f"{settings.sendgrid_from_name} <mailgun@{settings.mailgun_domain}>",
                "to": emails,
                "subject": subject,
                "html": body_html,
            },
        )
