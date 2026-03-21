import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional, List
import os
import json
import traceback
from jinja2 import Template, Environment, FileSystemLoader
from dataclasses import dataclass

@dataclass
class NotificationConfig:
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True

class NotificationService:
    """
    Comprehensive notification service for handling contractor emails,
    customer handoff messages, and notification logging.
    """
    
    def __init__(self, config: NotificationConfig):
        """
        Initialize the notification service with configuration.
        
        Args:
            config: NotificationConfig object containing email settings
        """
        self.config = config
        self.logger = self._setup_logger()
        self.template_env = self._setup_template_environment()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the notification service."""
        logger = logging.getLogger('NotificationService')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _setup_template_environment(self) -> Environment:
        """Set up Jinja2 template environment."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email')
        if os.path.exists(template_dir):
            return Environment(loader=FileSystemLoader(template_dir))
        else:
            return Environment(loader=FileSystemLoader('.'))
    
    def send_contractor_notification(self, lead_data: Dict[str, Any]) -> bool:
        """
        Send notification email to contractors about new leads.
        
        Args:
            lead_data: Dictionary containing lead information
                Required keys: contractor_email, lead_id, customer_name,
                             service_type, urgency, location, contact_info
                
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Validate required fields
            required_fields = [
                'contractor_email', 'lead_id', 'customer_name',
                'service_type', 'urgency', 'location', 'contact_info'
            ]
            
            missing_fields = [field for field in required_fields if field not in lead_data]
            if missing_fields:
                self.logger.error(f"Missing required fields: {missing_fields}")
                self.log_notification(
                    notification_type='contractor_notification',
                    recipient=lead_data.get('contractor_email', 'unknown'),
                    status='failed',
                    timestamp=datetime.now(),
                    error_message=f"Missing required fields: {missing_fields}"
                )
                return False
            
            # Prepare email content
            subject = f"New Lead Assignment - {lead_data['service_type']} ({lead_data['urgency']} Priority)"
            
            # Load and render email template
            html_content = self._render_contractor_template(lead_data)
            text_content = self._create_contractor_text_content(lead_data)
            
            # Send email
            success = self._send_email(
                to_email=lead_data['contractor_email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log notification
            self.log_notification(
                notification_type='contractor_notification',
                recipient=lead_data['contractor_email'],
                status='success' if success else 'failed',
                timestamp=datetime.now(),
                lead_id=lead_data['lead_id']
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending contractor notification: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.log_notification(
                notification_type='contractor_notification',
                recipient=lead_data.get('contractor_email', 'unknown'),
                status='error',
                timestamp=datetime.now(),
                error_message=str(e)
            )
            return False
    
    def send_customer_handoff_message(self, customer_data: Dict[str, Any]) -> bool:
        """
        Send handoff message to customers with contractor information.
        
        Args:
            customer_data: Dictionary containing customer and contractor information
                Required keys: customer_email, customer_name, contractor_name,
                             contractor_phone, contractor_email, service_type,
                             estimated_arrival, special_instructions
                
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Validate required fields
            required_fields = [
                'customer_email', 'customer_name', 'contractor_name',
                'contractor_phone', 'contractor_email', 'service_type'
            ]
            
            missing_fields = [field for field in required_fields if field not in customer_data]
            if missing_fields:
                self.logger.error(f"Missing required fields for customer handoff: {missing_fields}")
                self.log_notification(
                    notification_type='customer_handoff',
                    recipient=customer_data.get('customer_email', 'unknown'),
                    status='failed',
                    timestamp=datetime.now(),
                    error_message=f"Missing required fields: {missing_fields}"
                )
                return False
            
            # Prepare email content
            subject = f"Your {customer_data['service_type']} Service - Contractor Assignment"
            
            # Load and render email template
            html_content = self._render_customer_template(customer_data)
            text_content = self._create_customer_text_content(customer_data)
            
            # Send email
            success = self._send_email(
                to_email=customer_data['customer_email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Log notification
            self.log_notification(
                notification_type='customer_handoff',
                recipient=customer_data['customer_email'],
                status='success' if success else 'failed',
                timestamp=datetime.now(),
                contractor_name=customer_data['contractor_name']
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending customer handoff message: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.log_notification(
                notification_type='customer_handoff',
                recipient=customer_data.get('customer_email', 'unknown'),
                status='error',
                timestamp=datetime.now(),
                error_message=str(e)
            )
            return False
    
    def log_notification(
        self, 
        notification_type: str, 
        recipient: str, 
        status: str, 
        timestamp: datetime,
        **kwargs
    ) -> None:
        """
        Log notification attempts with details.
        
        Args:
            notification_type: Type of notification (contractor_notification, customer_handoff, etc.)
            recipient: Email address of recipient
            status: Status of notification (success, failed, error)
            timestamp: When the notification was attempted
            **kwargs: Additional data to log
        """
        try:
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'type': notification_type,
                'recipient': recipient,
                'status': status,
                **kwargs
            }
            
            # Log to application logger
            log_message = f"Notification {status}: {notification_type} to {recipient}"
            if status == 'success':
                self.logger.info(log_message)
            elif status == 'failed':
                self.logger.warning(log_message)
            else:
                self.logger.error(log_message)
            
            # Save to notification log file
            self._save_notification_log(log_entry)
            
        except Exception as e:
            self.logger.error(f"Error logging notification: {str(e)}")
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using SMTP configuration.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email content
            text_content: Plain text version of email content
            attachments: Optional list of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        self._add_attachment(msg, file_path)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                
                server.login(self.config.username, self.config.password)
                server.send_message(msg)
                
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """Add file attachment to email message."""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            msg.attach(part)
            
        except Exception as e:
            self.logger.error(f"Error adding attachment {file_path}: {str(e)}")
    
    def _render_contractor_template(self, lead_data: Dict[str, Any]) -> str:
        """Render contractor notification email template."""
        try:
            template = self.template_env.get_template('contractor_notification.html')
            return template.render(**lead_data)
        except Exception as e:
            self.logger.warning(f"Error loading contractor template: {str(e)}")
            return self._get_default_contractor_template().render(**lead_data)
    
    def _render_customer_template(self, customer_data: Dict[str, Any]) -> str:
        """Render customer handoff email template."""
        try:
            template = self.template_env.get_template('customer_handoff.html')
            return template.render(**customer_data)
        except Exception as e:
            self.logger.warning(f"Error loading customer template: {str(e)}")
            return self._get_default_customer_template().render(**customer_data)
    
    def _get_default_contractor_template(self) -> Template:
        """Get default contractor notification template."""
        template_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>New Lead Assignment</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { margin: 20px 0; }
                .urgency-high { color: #dc3545; font-weight: bold; }
                .urgency-medium { color: #ffc107; font-weight: bold; }
                .urgency-low { color: #28a745; font-weight: bold; }
                .contact-info { background-color: #e9ecef; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>New Lead Assignment</h2>
                <p>Lead ID: {{ lead_id }}</p>
            </div>
            
            <div class="content">
                <h3>Customer Information</h3>
                <p><strong>Name:</strong> {{ customer_name }}</p>
                <p><strong>Service Type:</strong> {{ service_type }}</p>
                <p><strong>Urgency:</strong> <span class="urgency-{{ urgency.lower() }}">{{ urgency }}</span></p>
                <p><strong>Location:</strong> {{ location }}</p>
                
                <div class="contact-info">
                    <h4>Contact Information</h4>
                    <p>{{ contact_info }}</p>
                </div>
                
                {% if special_notes %}
                <h4>Special Notes</h4>
                <p>{{ special_notes }}</p>
                {% endif %}
                
                <p><em>Please contact the customer as soon as possible to schedule service.</em></p>
            </div>
        </body>
        </html>
        """
        return Template(template_content)
    
    def _get_default_customer_template(self) -> Template:
        """Get default customer handoff template."""
        template_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contractor Assignment</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
                .content { margin: 20px 0; }
                .contractor-info { background-color: #e9ecef; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Your Service Request Update</h2>
                <p>Hello {{ customer_name }},</p>
            </div>
            
            <div class="content">
                <p>We're pleased to inform you that a contractor has been assigned to your {{ service_type }} request.</p>
                
                <div class="contractor-info">
                    <h3>Your Assigned Contractor</h3>
                    <p><strong>Name:</strong> {{ contractor_name }}</p>
                    <p><strong>Phone:</strong> {{ contractor_phone }}</p>
                    <p><strong>Email:</strong> {{ contractor_email }}</p>
                    
                    {% if estimated_arrival %}
                    <p><strong>Estimated Arrival:</strong> {{ estimated_arrival }}</p>
                    {% endif %}
                </div>
                
                {% if special_instructions %}
                <h4>Special Instructions</h4>
                <p>{{ special_instructions }}</p>
                {% endif %}
                
                <p>Your contractor will be contacting you shortly to confirm the appointment details.</p>
                <p>If you have any questions, please don't hesitate to reach out.</p>
                
                <p>Thank you for choosing our service!</p>
            </div>
        </body>
        </html>
        """
        return Template(template_content)
    
    def _create_contractor_text_content(self, lead_data: Dict[str, Any]) -> str:
        """Create plain text version of contractor notification."""
        content = f"""
NEW LEAD ASSIGNMENT

Lead ID: {lead_data['lead_id']}

Customer Information:
- Name: {lead_data['customer_name']}
- Service Type: {lead_data['service_type']}
- Urgency: {lead_data['urgency']}
- Location: {lead_data['location']}

Contact Information:
{lead_data['contact_info']}
"""
        
        if lead_data.get('special_notes'):
            content += f"\nSpecial Notes:\n{lead_data['special_notes']}\n"
            
        content += "\nPlease contact the customer as soon as possible to schedule service."
        
        return content
    
    def _create_customer_text_content(self, customer_data: Dict[str, Any]) -> str:
        """Create plain text version of customer handoff message."""
        content = f"""
YOUR SERVICE REQUEST UPDATE

Hello {customer_data['customer_name']},

We're pleased to inform you that a contractor has been assigned to your {customer_data['service_type']} request.

Your Assigned Contractor:
- Name: {customer_data['contractor_name']}
- Phone: {customer_data['contractor_phone']}
- Email: {customer_data['contractor_email']}
"""
        
        if customer_data.get('estimated_arrival'):
            content += f"- Estimated Arrival: {customer_data['estimated_arrival']}\n"
            
        if customer_data.get('special_instructions'):
            content += f"\nSpecial Instructions:\n{customer_data['special_instructions']}\n"
            
        content += """
Your contractor will be contacting you shortly to confirm the appointment details.

If you have any questions, please don't hesitate to reach out.

Thank you for choosing our service!
"""
        
        return content
    
    def _save_notification_log(self, log_entry: Dict[str, Any]) -> None:
        """Save notification log entry to file."""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'notifications.jsonl')
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error saving notification log: {str(e)}")
    
    def get_notification_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get notification statistics for the specified number of days.
        
        Args:
            days: Number of days to look back for statistics
            
        Returns:
            Dictionary containing notification statistics
        """
        try:
            log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'notifications.jsonl')
            
            if not os.path.exists(log_file):
                return {
                    'total_notifications': 0,
                    'successful_notifications': 0,
                    'failed_notifications': 0,
                    'success_rate': 0.0,
                    'notification_types': {}
                }
            
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            stats = {
                'total_notifications': 0,
                'successful_notifications': 0,
                'failed_notifications': 0,
                'notification_types': {}
            }
            
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                        
                        if entry_time >= cutoff_date:
                            stats['total_notifications'] += 1
                            
                            if entry['status'] == 'success':
                                stats['successful_notifications'] += 1
                            else:
                                stats['failed_notifications'] += 1
                            
                            notification_type = entry['type']
                            if notification_type not in stats['notification_types']:
                                stats['notification_types'][notification_type] = {
                                    'total': 0, 'successful': 0, 'failed': 0
                                }
                            
                            stats['notification_types'][notification_type]['total'] += 1
                            if entry['status'] == 'success':
                                stats['notification_types'][notification_type]['successful'] += 1
                            else:
                                stats['notification_types'][notification_type]['failed'] += 1
                                
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            # Calculate success rate
            if stats['total_notifications'] > 0:
                stats['success_rate'] = (
                    stats['successful_notifications'] / stats['total_notifications']
                ) * 100
            else:
                stats['success_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting notification stats: {str(e)}")
            return {
                'error': str(e),
                'total_notifications': 0,
                'successful_notifications': 0,
                'failed_notifications': 0,
                'success_rate': 0.0,
                'notification_types': {}
            }