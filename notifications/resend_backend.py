import requests

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = getattr(settings, "RESEND_API_KEY", "")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")

        if not api_key:
            if self.fail_silently:
                return 0
            raise ValueError("RESEND_API_KEY is missing.")

        sent_count = 0

        for message in email_messages:
            payload = {
                "from": from_email,
                "to": message.to,
                "subject": message.subject,
                "text": message.body,
            }

            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )

            if 200 <= response.status_code < 300:
                sent_count += 1
                continue

            if not self.fail_silently:
                raise Exception(
                    f"Resend email failed: {response.status_code} {response.text}"
                )

        return sent_count