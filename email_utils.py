import os

import requests


RESEND_API_URL = "https://api.resend.com/emails"


def send_resend_email(to_email, subject, text_content, html_content=None):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Resend email skipped: RESEND_API_KEY is not set.")
        return False

    from_email = os.environ.get(
        "RESEND_FROM_EMAIL",
        "BIKIzz Classes <onboarding@resend.dev>"
    )

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": text_content,
    }

    if html_content:
        payload["html"] = html_content

    try:
        response = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code in {200, 201, 202}:
            return True

        print("Resend email error:", response.status_code, response.text)
        return False
    except Exception as exc:
        print("Resend email connection error:", str(exc))
        return False
