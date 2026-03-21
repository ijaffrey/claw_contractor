import os
import smtplib
import logging
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.image import MimeImage
from email.mime.base import MimeBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import base64
import mimetypes

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling contractor notifications and email communications."""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.email_user)
        self.contractor_email = os.getenv('CONTRACTOR_EMAIL')
        self.company_name = os.getenv('COMPANY_NAME', 'CLAW Contractor Services')
        
        if not all([self.email_user, self.email_password, self.contractor_email]):
            logger.error("Missing required email configuration")
            raise ValueError("Email configuration incomplete")
    
    def send_contractor_notification(self, lead_data: Dict[str, Any]) -> bool:
        """
        Send notification to contractor with lead details and attachments.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = self.contractor_email
            msg['Subject'] = self._generate_subject(lead_data)
            
            # Generate email content
            html_content = self._generate_html_template(lead_data)
            text_content = self._generate_text_template(lead_data)
            
            # Attach content
            msg.attach(MimeText(text_content, 'plain'))
            msg.attach(MimeText(html_content, 'html'))
            
            # Handle photo attachments
            if 'photos' in lead_data and lead_data['photos']:
                self._attach_photos(msg, lead_data['photos'])
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Notification sent successfully for lead: {lead_data.get('customer_name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send contractor notification: {str(e)}")
            return False
    
    def format_lead_summary(self, lead: Dict[str, Any]) -> str:
        """
        Format lead data into a comprehensive summary string.
        
        Args:
            lead: Dictionary containing lead information
            
        Returns:
            str: Formatted lead summary
        """
        summary_parts = []
        
        # Customer Information
        if lead.get('customer_name'):
            summary_parts.append(f"Customer: {lead['customer_name']}")
        
        if lead.get('phone'):
            summary_parts.append(f"Phone: {lead['phone']}")
        
        if lead.get('email'):
            summary_parts.append(f"Email: {lead['email']}")
        
        # Property Information
        if lead.get('address'):
            summary_parts.append(f"Address: {lead['address']}")
        
        if lead.get('property_type'):
            summary_parts.append(f"Property Type: {lead['property_type']}")
        
        # Service Details
        if lead.get('service_type'):
            summary_parts.append(f"Service: {lead['service_type']}")
        
        if lead.get('urgency'):
            summary_parts.append(f"Urgency: {lead['urgency']}")
        
        if lead.get('budget_range'):
            summary_parts.append(f"Budget: {lead['budget_range']}")
        
        # Problem Description
        if lead.get('description'):
            summary_parts.append(f"Description: {lead['description']}")
        
        # Timeline
        if lead.get('preferred_timeline'):
            summary_parts.append(f"Timeline: {lead['preferred_timeline']}")
        
        # Contact Preferences
        if lead.get('contact_preference'):
            summary_parts.append(f"Preferred Contact: {lead['contact_preference']}")
        
        if lead.get('best_time_to_call'):
            summary_parts.append(f"Best Time to Call: {lead['best_time_to_call']}")
        
        # Additional Information
        if lead.get('additional_notes'):
            summary_parts.append(f"Notes: {lead['additional_notes']}")
        
        # Lead Source and Timestamp
        if lead.get('source'):
            summary_parts.append(f"Source: {lead['source']}")
        
        if lead.get('timestamp'):
            summary_parts.append(f"Received: {self._format_timestamp(lead['timestamp'])}")
        
        # Photos
        if lead.get('photos'):
            photo_count = len(lead['photos'])
            summary_parts.append(f"Photos: {photo_count} attached")
        
        return "\n".join(summary_parts)
    
    def generate_handoff_message(self, customer_name: str, next_steps: str) -> str:
        """
        Generate a handoff message for customer communication.
        
        Args:
            customer_name: Name of the customer
            next_steps: Description of next steps
            
        Returns:
            str: Formatted handoff message
        """
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        message = f"""
Hello {customer_name},

Thank you for contacting {self.company_name}. We have received your request and our team is reviewing your information.

NEXT STEPS:
{next_steps}

Our contractor will be in touch with you shortly to discuss your project in detail and schedule a consultation if needed.

If you have any immediate questions or concerns, please don't hesitate to reach out.

Best regards,
{self.company_name} Team

---
This message was generated on {timestamp}
        """.strip()
        
        return message
    
    def _generate_subject(self, lead_data: Dict[str, Any]) -> str:
        """Generate email subject line based on lead data."""
        customer_name = lead_data.get('customer_name', 'New Customer')
        service_type = lead_data.get('service_type', 'Service Request')
        urgency = lead_data.get('urgency', '').upper()
        
        if urgency in ['URGENT', 'EMERGENCY']:
            priority_prefix = f"[{urgency}] "
        else:
            priority_prefix = ""
        
        return f"{priority_prefix}New Lead: {customer_name} - {service_type}"
    
    def _generate_html_template(self, lead_data: Dict[str, Any]) -> str:
        """Generate HTML email template."""
        lead_summary = self.format_lead_summary(lead_data)
        handoff_message = ""
        
        if lead_data.get('customer_name'):
            handoff_message = self.generate_handoff_message(
                lead_data['customer_name'],
                "Please review the lead details and contact the customer within 24 hours."
            )
        
        urgency_color = self._get_urgency_color(lead_data.get('urgency'))
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background-color: #2c3e50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .urgency {{ background-color: {urgency_color}; color: white; padding: 5px 10px; border-radius: 3px; display: inline-block; margin-bottom: 10px; }}
        .section {{ margin-bottom: 20px; }}
        .section h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }}
        .info-item {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; }}
        .info-label {{ font-weight: bold; color: #34495e; }}
        .description {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
        .handoff {{ background-color: #e8f6f3; padding: 15px; border-radius: 5px; border: 1px solid #16a085; margin-top: 20px; }}
        .footer {{ text-align: center; margin-top: 20px; padding: 15px; background-color: #95a5a6; color: white; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔨 New Lead Alert - {self.company_name}</h1>
            <p>Lead received: {self._format_timestamp(lead_data.get('timestamp', datetime.now()))}</p>
        </div>
        
        {f'<div class="urgency">Priority: {lead_data.get("urgency", "Normal").upper()}</div>' if lead_data.get('urgency') else ''}
        
        <div class="section">
            <h3>📋 Lead Summary</h3>
            <pre style="white-space: pre-wrap; font-family: inherit;">{lead_summary}</pre>
        </div>
        
        {self._generate_customer_section_html(lead_data)}
        {self._generate_service_section_html(lead_data)}
        {self._generate_contact_section_html(lead_data)}
        
        {f'<div class="handoff"><h3>💬 Customer Handoff Message</h3><pre style="white-space: pre-wrap; font-family: inherit;">{handoff_message}</pre></div>' if handoff_message else ''}
        
        <div class="footer">
            <p>This is an automated notification from {self.company_name} Lead Management System</p>
            <p>Please respond to this lead promptly to maintain customer satisfaction</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return html_template
    
    def _generate_text_template(self, lead_data: Dict[str, Any]) -> str:
        """Generate plain text email template."""
        lead_summary = self.format_lead_summary(lead_data)
        handoff_message = ""
        
        if lead_data.get('customer_name'):
            handoff_message = self.generate_handoff_message(
                lead_data['customer_name'],
                "Please review the lead details and contact the customer within 24 hours."
            )
        
        text_template = f"""
🔨 NEW LEAD ALERT - {self.company_name}
{'=' * 50}

Lead Received: {self._format_timestamp(lead_data.get('timestamp', datetime.now()))}
{f"Priority: {lead_data.get('urgency', 'Normal').upper()}" if lead_data.get('urgency') else ''}

📋 LEAD SUMMARY
{'-' * 20}
{lead_summary}

💬 CUSTOMER HANDOFF MESSAGE
{'-' * 30}
{handoff_message if handoff_message else 'Please contact the customer promptly.'}

---
This is an automated notification from {self.company_name} Lead Management System
Please respond to this lead promptly to maintain customer satisfaction
        """.strip()
        
        return text_template
    
    def _generate_customer_section_html(self, lead_data: Dict[str, Any]) -> str:
        """Generate customer information section for HTML email."""
        customer_info = []
        
        if lead_data.get('customer_name'):
            customer_info.append(f'<div class="info-item"><span class="info-label">Name:</span> {lead_data["customer_name"]}</div>')
        
        if lead_data.get('phone'):
            customer_info.append(f'<div class="info-item"><span class="info-label">Phone:</span> <a href="tel:{lead_data["phone"]}">{lead_data["phone"]}</a></div>')
        
        if lead_data.get('email'):
            customer_info.append(f'<div class="info-item"><span class="info-label">Email:</span> <a href="mailto:{lead_data["email"]}">{lead_data["email"]}</a></div>')
        
        if lead_data.get('address'):
            customer_info.append(f'<div class="info-item"><span class="info-label">Address:</span> {lead_data["address"]}</div>')
        
        if customer_info:
            return f"""
            <div class="section">
                <h3>👤 Customer Information</h3>
                <div class="info-grid">
                    {''.join(customer_info)}
                </div>
            </div>
            """
        return ""
    
    def _generate_service_section_html(self, lead_data: Dict[str, Any]) -> str:
        """Generate service information section for HTML email."""
        service_info = []
        
        if lead_data.get('service_type'):
            service_info.append(f'<div class="info-item"><span class="info-label">Service:</span> {lead_data["service_type"]}</div>')
        
        if lead_data.get('property_type'):
            service_info.append(f'<div class="info-item"><span class="info-label">Property:</span> {lead_data["property_type"]}</div>')
        
        if lead_data.get('budget_range'):
            service_info.append(f'<div class="info-item"><span class="info-label">Budget:</span> {lead_data["budget_range"]}</div>')
        
        if lead_data.get('preferred_timeline'):
            service_info.append(f'<div class="info-item"><span class="info-label">Timeline:</span> {lead_data["preferred_timeline"]}</div>')
        
        description_section = ""
        if lead_data.get('description'):
            description_section = f'<div class="description"><strong>Description:</strong><br>{lead_data["description"]}</div>'
        
        if service_info or description_section:
            info_grid = f'<div class="info-grid">{"".join(service_info)}</div>' if service_info else ""
            return f"""
            <div class="section">
                <h3>🔧 Service Details</h3>
                {info_grid}
                {description_section}
            </div>
            """
        return ""
    
    def _generate_contact_section_html(self, lead_data: Dict[str, Any]) -> str:
        """Generate contact preferences section for HTML email."""
        contact_info = []
        
        if lead_data.get('contact_preference'):
            contact_info.append(f'<div class="info-item"><span class="info-label">Preferred Contact:</span> {lead_data["contact_preference"]}</div>')
        
        if lead_data.get('best_time_to_call'):
            contact_info.append(f'<div class="info-item"><span class="info-label">Best Time:</span> {lead_data["best_time_to_call"]}</div>')
        
        if lead_data.get('additional_notes'):
            contact_info.append(f'<div class="info-item" style="grid-column: 1 / -1;"><span class="info-label">Notes:</span> {lead_data["additional_notes"]}</div>')
        
        if contact_info:
            return f"""
            <div class="section">
                <h3>📞 Contact Preferences</h3>
                <div class="info-grid">
                    {''.join(contact_info)}
                </div>
            </div>
            """
        return ""
    
    def _attach_photos(self, msg: MimeMultipart, photos: List[Dict[str, Any]]):
        """Attach photos to email message."""
        for i, photo in enumerate(photos[:10]):  # Limit to 10 photos
            try:
                if 'data' in photo:
                    # Handle base64 encoded images
                    image_data = base64.b64decode(photo['data'])
                    filename = photo.get('filename', f'photo_{i+1}.jpg')
                    
                    # Determine MIME type
                    mime_type = photo.get('mime_type')
                    if not mime_type:
                        mime_type, _ = mimetypes.guess_type(filename)
                        if not mime_type or not mime_type.startswith('image/'):
                            mime_type = 'image/jpeg'
                    
                    # Create image attachment
                    img = MimeImage(image_data)
                    img.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(img)
                    
                elif 'url' in photo:
                    # Handle image URLs (add as reference in email body)
                    pass
                    
            except Exception as e:
                logger.error(f"Failed to attach photo {i+1}: {str(e)}")
    
    def _get_urgency_color(self, urgency: Optional[str]) -> str:
        """Get color code for urgency level."""
        if not urgency:
            return "#3498db"
        
        urgency = urgency.upper()
        color_map = {
            'EMERGENCY': '#e74c3c',
            'URGENT': '#e67e22',
            'HIGH': '#f39c12',
            'NORMAL': '#3498db',
            'LOW': '#27ae60'
        }
        return color_map.get(urgency, "#3498db")
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """Format timestamp for display."""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return timestamp
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            dt = datetime.now()
        
        return dt.strftime("%B %d, %Y at %I:%M %p")