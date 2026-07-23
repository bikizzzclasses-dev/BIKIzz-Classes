import os

import requests


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_brevo_email(to_email, subject, text_content, html_content=None):
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        print("Brevo email skipped: BREVO_API_KEY is not set.")
        return False

    payload = {
        "sender": {
            "email": os.environ.get("BREVO_FROM_EMAIL", "bikizzzclasses@gmail.com"),
            "name": os.environ.get("BREVO_FROM_NAME", "BIKIzz Classes"),
        },
        "to": [to_email],
        "subject": subject,
        "textContent": text_content,
    }

    if html_content:
        payload["htmlContent"] = html_content

    try:
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code in {200, 201, 202}:
            return True

        print("Brevo email error:", response.status_code, response.text)
        return False
    except Exception as exc:
        print("Brevo email connection error:", str(exc))
        return False
