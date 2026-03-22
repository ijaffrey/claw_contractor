from dataclasses import dataclass

@dataclass
class EmailConfig:
    sender_email: str
    sender_name: str

class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config

    def send_email(self, to_email, subject, body, is_html=False):
        try:
            from gmail_listener import get_gmail_service, send_email_via_gmail
            service = get_gmail_service()
            return send_email_via_gmail(service, to_email, subject, body)
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    def send_email_simple(self, to_email, subject, body):
        return self.send_email(to_email, subject, body)
