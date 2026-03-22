import base64
import logging
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuration for email sender."""
    sender_email: str
    sender_name: str


class EmailSender:
    """Gmail API-based email sender."""
    
    def __init__(self, config: EmailConfig, credentials: Credentials):
        """Initialize EmailSender with configuration and OAuth credentials.
        
        Args:
            config: EmailConfig instance with sender details
            credentials: Google OAuth2 credentials for Gmail API access
        """
        self.config = config
        self.credentials = credentials
        self.service = None
        
    def _get_service(self):
        """Get or create Gmail API service instance."""
        if not self.service:
            try:
                self.service = build('gmail', 'v1', credentials=self.credentials)
            except Exception as e:
                logger.error(f"Failed to create Gmail service: {e}")
                raise
        return self.service
    
    def _create_message(self, to_email: str, subject: str, body: str, 
                       body_type: str = 'plain', cc: Optional[List[str]] = None,
                       bcc: Optional[List[str]] = None) -> dict:
        """Create a message for an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: 'plain' or 'html'
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            Dictionary containing the base64 encoded email message
        """
        try:
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = f"{self.config.sender_name} <{self.config.sender_email}>"
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            msg = MIMEText(body, body_type)
            message.attach(msg)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            return {'raw': raw_message}
            
        except Exception as e:
            logger.error(f"Failed to create email message: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, body: str,
                   body_type: str = 'plain', cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> bool:
        """Send an email using Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: 'plain' or 'html'
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Refresh credentials if needed
            if self.credentials.expired:
                self.credentials.refresh(Request())
            
            service = self._get_service()
            message = self._create_message(
                to_email=to_email,
                subject=subject,
                body=body,
                body_type=body_type,
                cc=cc,
                bcc=bcc
            )
            
            result = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error occurred: {error}")
            return False
        except Exception as error:
            logger.error(f"An error occurred while sending email: {error}")
            return False
    
    def send_html_email(self, to_email: str, subject: str, html_body: str,
                       cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> bool:
        """Send an HTML email using Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=html_body,
            body_type='html',
            cc=cc,
            bcc=bcc
        )