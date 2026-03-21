"""Email formatting utilities for contractor CRM notifications."""

import re
import html
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import base64
import mimetypes


class EmailFormatter:
    """Handles formatting of email content for notifications."""
    
    def __init__(self):
        self.html_template = self._get_html_template()
        self.text_template = self._get_text_template()
    
    def format_lead_summary(self, lead_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Format lead data into readable email content.
        
        Args:
            lead_data: Dictionary containing lead information
            
        Returns:
            Dictionary with 'html' and 'text' formatted content
        """
        # Sanitize input data
        sanitized_data = self._sanitize_lead_data(lead_data)
        
        # Format the content
        html_content = self._format_html_lead_summary(sanitized_data)
        text_content = self._format_text_lead_summary(sanitized_data)
        
        return {
            'html': html_content,
            'text': text_content
        }
    
    def format_notification_email(
        self,
        lead_data: Dict[str, Any],
        notification_type: str = 'new_lead',
        photos: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """
        Format complete notification email with lead data and photos.
        
        Args:
            lead_data: Lead information dictionary
            notification_type: Type of notification ('new_lead', 'lead_update', etc.)
            photos: List of photo dictionaries with 'url' or 'data' keys
            
        Returns:
            Dictionary with formatted email content
        """
        # Get lead summary
        lead_summary = self.format_lead_summary(lead_data)
        
        # Format photos section
        photo_section_html = self._format_photos_html(photos) if photos else ""
        photo_section_text = self._format_photos_text(photos) if photos else ""
        
        # Get notification subject
        subject = self._get_notification_subject(notification_type, lead_data)
        
        # Combine everything
        html_body = self.html_template.format(
            subject=html.escape(subject),
            lead_summary=lead_summary['html'],
            photo_section=photo_section_html,
            timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")
        )
        
        text_body = self.text_template.format(
            subject=subject,
            lead_summary=lead_summary['text'],
            photo_section=photo_section_text,
            timestamp=datetime.now().strftime("%B %d, %Y at %I:%M %p")
        )
        
        return {
            'subject': subject,
            'html': html_body,
            'text': text_body
        }
    
    def sanitize_customer_input(self, text: str, allow_basic_html: bool = False) -> str:
        """
        Sanitize customer input for safe email display.
        
        Args:
            text: Raw text input from customer
            allow_basic_html: Whether to allow basic HTML tags
            
        Returns:
            Sanitized text safe for email display
        """
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        if allow_basic_html:
            # Allow only safe HTML tags
            allowed_tags = ['b', 'i', 'u', 'br', 'p', 'strong', 'em']
            text = self._strip_dangerous_html(text, allowed_tags)
        else:
            # Escape all HTML
            text = html.escape(text)
        
        # Limit length to prevent abuse
        if len(text) > 10000:
            text = text[:10000] + "... (truncated)"
        
        return text.strip()
    
    def format_photo_attachments(self, photos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format photo data for email attachments.
        
        Args:
            photos: List of photo dictionaries
            
        Returns:
            List of formatted attachment dictionaries
        """
        attachments = []
        
        for i, photo in enumerate(photos):
            if 'data' in photo:
                # Handle base64 encoded photo data
                attachment = self._format_base64_attachment(photo, i)
                if attachment:
                    attachments.append(attachment)
            elif 'url' in photo:
                # Handle photo URLs (will be displayed as links in email)
                continue
        
        return attachments
    
    def _sanitize_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string values in lead data."""
        sanitized = {}
        
        for key, value in lead_data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_customer_input(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_lead_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_customer_input(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _format_html_lead_summary(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data as HTML content."""
        html_parts = ['<div class="lead-summary">']
        
        # Customer information
        if any(key in lead_data for key in ['customer_name', 'email', 'phone']):
            html_parts.append('<h3>Customer Information</h3>')
            html_parts.append('<table class="customer-info">')
            
            if 'customer_name' in lead_data and lead_data['customer_name']:
                html_parts.append(f'<tr><td><strong>Name:</strong></td><td>{lead_data["customer_name"]}</td></tr>')
            
            if 'email' in lead_data and lead_data['email']:
                html_parts.append(f'<tr><td><strong>Email:</strong></td><td><a href="mailto:{lead_data["email"]}">{lead_data["email"]}</a></td></tr>')
            
            if 'phone' in lead_data and lead_data['phone']:
                formatted_phone = self._format_phone_number(lead_data['phone'])
                html_parts.append(f'<tr><td><strong>Phone:</strong></td><td><a href="tel:{lead_data["phone"]}">{formatted_phone}</a></td></tr>')
            
            html_parts.append('</table>')
        
        # Service request information
        if any(key in lead_data for key in ['service_type', 'description', 'address', 'preferred_date']):
            html_parts.append('<h3>Service Request</h3>')
            html_parts.append('<table class="service-info">')
            
            if 'service_type' in lead_data and lead_data['service_type']:
                html_parts.append(f'<tr><td><strong>Service Type:</strong></td><td>{lead_data["service_type"]}</td></tr>')
            
            if 'address' in lead_data and lead_data['address']:
                address_link = f"https://maps.google.com/maps?q={lead_data['address'].replace(' ', '+')}"
                html_parts.append(f'<tr><td><strong>Address:</strong></td><td><a href="{address_link}" target="_blank">{lead_data["address"]}</a></td></tr>')
            
            if 'preferred_date' in lead_data and lead_data['preferred_date']:
                html_parts.append(f'<tr><td><strong>Preferred Date:</strong></td><td>{lead_data["preferred_date"]}</td></tr>')
            
            html_parts.append('</table>')
            
            if 'description' in lead_data and lead_data['description']:
                html_parts.append(f'<h4>Description:</h4><div class="description">{lead_data["description"].replace(chr(10), "<br>")}</div>')
        
        # Lead metadata
        if any(key in lead_data for key in ['lead_source', 'lead_id', 'created_at', 'urgency']):
            html_parts.append('<h3>Lead Details</h3>')
            html_parts.append('<table class="lead-details">')
            
            if 'lead_id' in lead_data and lead_data['lead_id']:
                html_parts.append(f'<tr><td><strong>Lead ID:</strong></td><td>{lead_data["lead_id"]}</td></tr>')
            
            if 'lead_source' in lead_data and lead_data['lead_source']:
                html_parts.append(f'<tr><td><strong>Source:</strong></td><td>{lead_data["lead_source"]}</td></tr>')
            
            if 'urgency' in lead_data and lead_data['urgency']:
                urgency_class = f"urgency-{lead_data['urgency'].lower()}"
                html_parts.append(f'<tr><td><strong>Urgency:</strong></td><td><span class="{urgency_class}">{lead_data["urgency"]}</span></td></tr>')
            
            if 'created_at' in lead_data and lead_data['created_at']:
                formatted_date = self._format_datetime(lead_data['created_at'])
                html_parts.append(f'<tr><td><strong>Created:</strong></td><td>{formatted_date}</td></tr>')
            
            html_parts.append('</table>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _format_text_lead_summary(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data as plain text content."""
        text_parts = []
        
        # Customer information
        if any(key in lead_data for key in ['customer_name', 'email', 'phone']):
            text_parts.append('CUSTOMER INFORMATION')
            text_parts.append('=' * 20)
            
            if 'customer_name' in lead_data and lead_data['customer_name']:
                text_parts.append(f'Name: {lead_data["customer_name"]}')
            
            if 'email' in lead_data and lead_data['email']:
                text_parts.append(f'Email: {lead_data["email"]}')
            
            if 'phone' in lead_data and lead_data['phone']:
                formatted_phone = self._format_phone_number(lead_data['phone'])
                text_parts.append(f'Phone: {formatted_phone}')
            
            text_parts.append('')
        
        # Service request information
        if any(key in lead_data for key in ['service_type', 'description', 'address', 'preferred_date']):
            text_parts.append('SERVICE REQUEST')
            text_parts.append('=' * 15)
            
            if 'service_type' in lead_data and lead_data['service_type']:
                text_parts.append(f'Service Type: {lead_data["service_type"]}')
            
            if 'address' in lead_data and lead_data['address']:
                text_parts.append(f'Address: {lead_data["address"]}')
            
            if 'preferred_date' in lead_data and lead_data['preferred_date']:
                text_parts.append(f'Preferred Date: {lead_data["preferred_date"]}')
            
            if 'description' in lead_data and lead_data['description']:
                text_parts.append(f'Description:\n{lead_data["description"]}')
            
            text_parts.append('')
        
        # Lead metadata
        if any(key in lead_data for key in ['lead_source', 'lead_id', 'created_at', 'urgency']):
            text_parts.append('LEAD DETAILS')
            text_parts.append('=' * 12)
            
            if 'lead_id' in lead_data and lead_data['lead_id']:
                text_parts.append(f'Lead ID: {lead_data["lead_id"]}')
            
            if 'lead_source' in lead_data and lead_data['lead_source']:
                text_parts.append(f'Source: {lead_data["lead_source"]}')
            
            if 'urgency' in lead_data and lead_data['urgency']:
                text_parts.append(f'Urgency: {lead_data["urgency"]}')
            
            if 'created_at' in lead_data and lead_data['created_at']:
                formatted_date = self._format_datetime(lead_data['created_at'])
                text_parts.append(f'Created: {formatted_date}')
        
        return '\n'.join(text_parts)
    
    def _format_photos_html(self, photos: List[Dict[str, Any]]) -> str:
        """Format photos section for HTML email."""
        if not photos:
            return ""
        
        html_parts = ['<div class="photos-section">', '<h3>Attached Photos</h3>']
        
        for i, photo in enumerate(photos):
            if 'url' in photo:
                # Photo URL - display as link with thumbnail if possible
                photo_name = photo.get('name', f'Photo {i+1}')
                html_parts.append(f'<div class="photo-item">')
                html_parts.append(f'<a href="{photo["url"]}" target="_blank">{photo_name}</a>')
                if self._is_image_url(photo['url']):
                    html_parts.append(f'<br><img src="{photo["url"]}" alt="{photo_name}" style="max-width: 200px; max-height: 200px; margin-top: 5px;">')
                html_parts.append('</div>')
            elif 'data' in photo:
                # Base64 photo data - reference as attachment
                photo_name = photo.get('name', f'photo_{i+1}.jpg')
                html_parts.append(f'<div class="photo-item">📎 {photo_name} (attached)</div>')
        
        html_parts.extend(['</div>', '<br>'])
        return ''.join(html_parts)
    
    def _format_photos_text(self, photos: List[Dict[str, Any]]) -> str:
        """Format photos section for plain text email."""
        if not photos:
            return ""
        
        text_parts = ['ATTACHED PHOTOS', '=' * 15]
        
        for i, photo in enumerate(photos):
            if 'url' in photo:
                photo_name = photo.get('name', f'Photo {i+1}')
                text_parts.append(f'{photo_name}: {photo["url"]}')
            elif 'data' in photo:
                photo_name = photo.get('name', f'photo_{i+1}.jpg')
                text_parts.append(f'{photo_name} (attached to email)')
        
        text_parts.append('')
        return '\n'.join(text_parts)
    
    def _format_base64_attachment(self, photo: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Format base64 photo data as email attachment."""
        try:
            photo_data = photo.get('data', '')
            if photo_data.startswith('data:'):
                # Extract MIME type and data from data URL
                header, encoded = photo_data.split(',', 1)
                mime_type = header.split(':')[1].split(';')[0]
            else:
                # Assume base64 encoded image data
                encoded = photo_data
                mime_type = photo.get('mime_type', 'image/jpeg')
            
            # Decode base64 data
            decoded_data = base64.b64decode(encoded)
            
            # Generate filename
            extension = mimetypes.guess_extension(mime_type) or '.jpg'
            filename = photo.get('name', f'photo_{index + 1}{extension}')
            
            return {
                'filename': filename,
                'content': decoded_data,
                'content_type': mime_type,
                'disposition': 'attachment'
            }
        
        except Exception:
            return None
    
    def _get_notification_subject(self, notification_type: str, lead_data: Dict[str, Any]) -> str:
        """Generate email subject based on notification type and lead data."""
        customer_name = lead_data.get('customer_name', 'Unknown Customer')
        service_type = lead_data.get('service_type', 'Service Request')
        
        subject_templates = {
            'new_lead': f'New Lead: {service_type} - {customer_name}',
            'lead_update': f'Lead Updated: {service_type} - {customer_name}',
            'urgent_lead': f'URGENT Lead: {service_type} - {customer_name}',
            'lead_assigned': f'Lead Assigned: {service_type} - {customer_name}',
            'lead_completed': f'Lead Completed: {service_type} - {customer_name}'
        }
        
        return subject_templates.get(notification_type, f'Contractor CRM Notification - {customer_name}')
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for display."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) == 10:
            return f'({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}'
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f'+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}'
        else:
            return phone
    
    def _format_datetime(self, dt_value: Any) -> str:
        """Format datetime value for display."""
        if isinstance(dt_value, str):
            try:
                dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                return dt.strftime('%B %d, %Y at %I:%M %p')
            except ValueError:
                return str(dt_value)
        elif isinstance(dt_value, datetime):
            return dt_value.strftime('%B %d, %Y at %I:%M %p')
        else:
            return str(dt_value)
    
    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            return any(path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])
        except Exception:
            return False
    
    def _strip_dangerous_html(self, text: str, allowed_tags: List[str]) -> str:
        """Remove dangerous HTML tags while keeping allowed ones."""
        # This is a simplified implementation - in production, use a library like bleach
        import re
        
        # Remove script and style tags completely
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove dangerous attributes
        text = re.sub(r'<([^>]+)\s+(on\w+|javascript:|data:)[^>]*>', r'<\1>', text, flags=re.IGNORECASE)
        
        # Remove all tags except allowed ones
        allowed_pattern = '|'.join(allowed_tags)
        text = re.sub(f'<(?!/?({allowed_pattern})\b)[^>]*>', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _get_html_template(self) -> str:
        """Get HTML email template."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h3 {{ color: #34495e; margin-top: 25px; margin-bottom: 15px; }}
        h4 {{ color: #7f8c8d; margin-top: 20px; margin-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        td {{ padding: 8px; border-bottom: 1px solid #ecf0f1; vertical-align: top; }}
        td:first-child {{ font-weight: bold; width: 30%; }}
        .description {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 10px 0; }}
        .urgency-high {{ color: #e74c3c; font-weight: bold; }}
        .urgency-medium {{ color: #f39c12; font-weight: bold; }}
        .urgency-low {{ color: #27ae60; }}
        .photos-section {{ margin-top: 20px; }}
        .photo-item {{ margin-bottom: 10px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #bdc3c7; font-size: 14px; color: #7f8c8d; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{subject}</h1>
        
        {lead_summary}
        
        {photo_section}
        
        <div class="footer">
            <p>Generated on {timestamp}</p>
            <p>This is an automated notification from your Contractor CRM system.</p>
        </div>
    </div>
</body>
</html>
'''
    
    def _get_text_template(self) -> str:
        """Get plain text email template."""
        return '''
{subject}
{'=' * 50}

{lead_summary}

{photo_section}

---
Generated on {timestamp}
This is an automated notification from your Contractor CRM system.
'''