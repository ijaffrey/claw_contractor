import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import current_app
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

class NotificationService:
    """Production-ready email notification service for contractor lead management"""
    
    def __init__(self, mail_instance: Mail = None, db_engine=None):
        self.mail = mail_instance
        self.db_engine = db_engine
        
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _create_notification_log_table(self):
        """Create notification_logs table if it doesn't exist"""
        try:
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS notification_logs (
                        id SERIAL PRIMARY KEY,
                        lead_id INTEGER NOT NULL,
                        notification_type VARCHAR(100) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        recipient_email VARCHAR(255),
                        subject VARCHAR(500),
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
        except Exception as e:
            logger.error(f"Error creating notification_logs table: {str(e)}")
    
    def send_contractor_notification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send detailed lead notification to contractor with customer responses and photos
        
        Args:
            lead_data: Dictionary containing lead information including:
                - contractor_email: str
                - customer_name: str
                - customer_email: str
                - customer_phone: str
                - service_type: str
                - project_description: str
                - budget_range: str
                - timeline: str
                - address: str
                - photos: List of file paths
                - responses: Dict of form responses
                - lead_id: int
                
        Returns:
            Dict with 'success' boolean and 'message' string
        """
        try:
            # Validate required fields
            required_fields = ['contractor_email', 'customer_name', 'lead_id']
            for field in required_fields:
                if not lead_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate contractor email
            contractor_email = lead_data['contractor_email']
            if not self._validate_email(contractor_email):
                raise ValueError(f"Invalid contractor email: {contractor_email}")
            
            # Create email message
            msg = Message(
                subject=f"New Lead: {lead_data.get('service_type', 'Service Request')} - {lead_data['customer_name']}",
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=[contractor_email]
            )
            
            # Build email content
            html_content = self._build_contractor_email_html(lead_data)
            text_content = self._build_contractor_email_text(lead_data)
            
            msg.html = html_content
            msg.body = text_content
            
            # Attach photos if provided
            if lead_data.get('photos'):
                self._attach_photos(msg, lead_data['photos'])
            
            # Send email
            self.mail.send(msg)
            
            # Log successful notification
            self.log_notification(
                lead_data['lead_id'],
                'contractor_notification',
                'sent',
                recipient_email=contractor_email,
                subject=msg.subject
            )
            
            logger.info(f"Contractor notification sent successfully to {contractor_email} for lead {lead_data['lead_id']}")
            
            return {
                'success': True,
                'message': f'Notification sent successfully to {contractor_email}'
            }
            
        except ValueError as ve:
            error_msg = f"Validation error: {str(ve)}"
            logger.error(error_msg)
            self._log_error_notification(lead_data.get('lead_id'), 'contractor_notification', error_msg)
            return {'success': False, 'message': error_msg}
            
        except Exception as e:
            error_msg = f"Error sending contractor notification: {str(e)}"
            logger.error(error_msg)
            self._log_error_notification(lead_data.get('lead_id'), 'contractor_notification', error_msg)
            return {'success': False, 'message': 'Failed to send notification'}
    
    def send_customer_handoff(self, customer_email: str, contractor_info: Dict[str, Any], lead_id: int = None) -> Dict[str, Any]:
        """
        Send professional handoff email to customer explaining next steps
        
        Args:
            customer_email: Customer's email address
            contractor_info: Dictionary containing:
                - name: str
                - email: str
                - phone: str
                - company: str (optional)
                - specialties: List[str] (optional)
                - rating: float (optional)
                - response_time: str (optional)
            lead_id: Lead ID for logging purposes
                
        Returns:
            Dict with 'success' boolean and 'message' string
        """
        try:
            # Validate inputs
            if not customer_email or not self._validate_email(customer_email):
                raise ValueError(f"Invalid customer email: {customer_email}")
            
            if not contractor_info.get('name') or not contractor_info.get('email'):
                raise ValueError("Contractor name and email are required")
            
            if not self._validate_email(contractor_info['email']):
                raise ValueError(f"Invalid contractor email: {contractor_info['email']}")
            
            # Create email message
            msg = Message(
                subject="Your Service Request Has Been Matched - Next Steps",
                sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=[customer_email],
                cc=[contractor_info['email']]  # CC contractor for transparency
            )
            
            # Build email content
            html_content = self._build_customer_handoff_html(contractor_info)
            text_content = self._build_customer_handoff_text(contractor_info)
            
            msg.html = html_content
            msg.body = text_content
            
            # Send email
            self.mail.send(msg)
            
            # Log successful notification
            if lead_id:
                self.log_notification(
                    lead_id,
                    'customer_handoff',
                    'sent',
                    recipient_email=customer_email,
                    subject=msg.subject
                )
            
            logger.info(f"Customer handoff email sent successfully to {customer_email}")
            
            return {
                'success': True,
                'message': f'Handoff email sent successfully to {customer_email}'
            }
            
        except ValueError as ve:
            error_msg = f"Validation error: {str(ve)}"
            logger.error(error_msg)
            if lead_id:
                self._log_error_notification(lead_id, 'customer_handoff', error_msg)
            return {'success': False, 'message': error_msg}
            
        except Exception as e:
            error_msg = f"Error sending customer handoff email: {str(e)}"
            logger.error(error_msg)
            if lead_id:
                self._log_error_notification(lead_id, 'customer_handoff', error_msg)
            return {'success': False, 'message': 'Failed to send handoff email'}
    
    def log_notification(self, lead_id: int, notification_type: str, status: str, 
                        recipient_email: str = None, subject: str = None, error_message: str = None) -> bool:
        """
        Log notification attempt to database with timestamp
        
        Args:
            lead_id: ID of the lead
            notification_type: Type of notification (contractor_notification, customer_handoff, etc.)
            status: Status of notification (sent, failed, pending)
            recipient_email: Email address of recipient
            subject: Email subject line
            error_message: Error message if applicable
            
        Returns:
            Boolean indicating success of logging operation
        """
        try:
            if not self.db_engine:
                logger.warning("No database engine configured for notification logging")
                return False
            
            # Ensure table exists
            self._create_notification_log_table()
            
            # Insert notification log
            with self.db_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO notification_logs 
                    (lead_id, notification_type, status, recipient_email, subject, error_message, created_at)
                    VALUES (:lead_id, :notification_type, :status, :recipient_email, :subject, :error_message, :created_at)
                """), {
                    'lead_id': lead_id,
                    'notification_type': notification_type,
                    'status': status,
                    'recipient_email': recipient_email,
                    'subject': subject,
                    'error_message': error_message,
                    'created_at': datetime.utcnow()
                })
                conn.commit()
            
            logger.info(f"Notification logged: lead_id={lead_id}, type={notification_type}, status={status}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error logging notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
            return False
    
    def _log_error_notification(self, lead_id: int, notification_type: str, error_message: str):
        """Helper to log failed notifications"""
        if lead_id:
            self.log_notification(lead_id, notification_type, 'failed', error_message=error_message)
    
    def _attach_photos(self, msg: Message, photos: List[str]):
        """Attach photo files to email message"""
        try:
            for photo_path in photos:
                if os.path.exists(photo_path) and os.path.getsize(photo_path) < 10 * 1024 * 1024:  # 10MB limit
                    filename = secure_filename(os.path.basename(photo_path))
                    with open(photo_path, 'rb') as f:
                        msg.attach(filename, "image/jpeg", f.read())
                else:
                    logger.warning(f"Photo attachment skipped: {photo_path} (file not found or too large)")
        except Exception as e:
            logger.error(f"Error attaching photos: {str(e)}")
    
    def _build_contractor_email_html(self, lead_data: Dict[str, Any]) -> str:
        """Build HTML email content for contractor notification"""
        photos_section = ""
        if lead_data.get('photos'):
            photos_section = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #2c5aa0;">Photos Attached</h3>
                <p>{len(lead_data['photos'])} photo(s) attached to this email</p>
            </div>
            """
        
        responses_section = ""
        if lead_data.get('responses'):
            responses_list = ""
            for key, value in lead_data['responses'].items():
                responses_list += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
            
            responses_section = f"""
            <div style="margin: 20px 0;">
                <h3 style="color: #2c5aa0;">Additional Information</h3>
                <ul style="margin: 10px 0; padding-left: 20px;">
                    {responses_list}
                </ul>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Lead Notification</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h1 style="color: #2c5aa0; margin: 0;">🔥 New Lead Alert!</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">You have received a new service request</p>
            </div>
            
            <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2c5aa0; margin-top: 0;">Lead Details</h2>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #2c5aa0;">Customer Information</h3>
                    <p><strong>Name:</strong> {lead_data.get('customer_name', 'N/A')}</p>
                    <p><strong>Email:</strong> <a href="mailto:{lead_data.get('customer_email', '')}">{lead_data.get('customer_email', 'N/A')}</a></p>
                    <p><strong>Phone:</strong> <a href="tel:{lead_data.get('customer_phone', '')}">{lead_data.get('customer_phone', 'N/A')}</a></p>
                    <p><strong>Address:</strong> {lead_data.get('address', 'N/A')}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #2c5aa0;">Project Information</h3>
                    <p><strong>Service Type:</strong> {lead_data.get('service_type', 'N/A')}</p>
                    <p><strong>Description:</strong> {lead_data.get('project_description', 'N/A')}</p>
                    <p><strong>Budget Range:</strong> {lead_data.get('budget_range', 'N/A')}</p>
                    <p><strong>Timeline:</strong> {lead_data.get('timeline', 'N/A')}</p>
                </div>
                
                {responses_section}
                {photos_section}
                
                <div style="margin: 30px 0; padding: 20px; background: #e7f3ff; border-radius: 6px; border-left: 4px solid #2c5aa0;">
                    <h3 style="color: #2c5aa0; margin-top: 0;">Next Steps</h3>
                    <ol style="margin: 10px 0; padding-left: 20px;">
                        <li>Review the lead details and photos</li>
                        <li>Contact the customer within 24 hours for best results</li>
                        <li>Schedule a consultation or site visit</li>
                        <li>Prepare a detailed quote based on their requirements</li>
                    </ol>
                </div>
                
                <div style="margin: 20px 0; text-align: center;">
                    <p><strong>Lead ID:</strong> #{lead_data.get('lead_id', 'N/A')}</p>
                    <p style="font-size: 12px; color: #666;">This lead was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px; font-size: 12px; color: #666;">
                <p>This is an automated notification from your lead management system. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
    
    def _build_contractor_email_text(self, lead_data: Dict[str, Any]) -> str:
        """Build plain text email content for contractor notification"""
        photos_text = f"\n\nPHOTOS ATTACHED: {len(lead_data.get('photos', []))} photo(s) attached to this email\n" if lead_data.get('photos') else ""
        
        responses_text = ""
        if lead_data.get('responses'):
            responses_text = "\n\nADDITIONAL INFORMATION:\n"
            for key, value in lead_data['responses'].items():
                responses_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return f"""
🔥 NEW LEAD ALERT!

You have received a new service request.

LEAD DETAILS
============

CUSTOMER INFORMATION:
- Name: {lead_data.get('customer_name', 'N/A')}
- Email: {lead_data.get('customer_email', 'N/A')}
- Phone: {lead_data.get('customer_phone', 'N/A')}
- Address: {lead_data.get('address', 'N/A')}

PROJECT INFORMATION:
- Service Type: {lead_data.get('service_type', 'N/A')}
- Description: {lead_data.get('project_description', 'N/A')}
- Budget Range: {lead_data.get('budget_range', 'N/A')}
- Timeline: {lead_data.get('timeline', 'N/A')}
{responses_text}{photos_text}

NEXT STEPS:
1. Review the lead details and photos
2. Contact the customer within 24 hours for best results
3. Schedule a consultation or site visit
4. Prepare a detailed quote based on their requirements

Lead ID: #{lead_data.get('lead_id', 'N/A')}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

This is an automated notification. Please do not reply to this email.
        """
    
    def _build_customer_handoff_html(self, contractor_info: Dict[str, Any]) -> str:
        """Build HTML email content for customer handoff"""
        company_info = f" at {contractor_info['company']}" if contractor_info.get('company') else ""
        rating_info = f"⭐ {contractor_info['rating']}/5.0 rating" if contractor_info.get('rating') else ""
        specialties_info = ""
        if contractor_info.get('specialties'):
            specialties_list = ", ".join(contractor_info['specialties'])
            specialties_info = f"<p><strong>Specialties:</strong> {specialties_list}</p>"
        
        response_time = contractor_info.get('response_time', 'within 24 hours')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Service Request Has Been Matched</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #28a745; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <h1 style="margin: 0;">✅ Great News!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Your service request has been matched with a qualified contractor</p>
            </div>
            
            <div style="background: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2c5aa0; margin-top: 0;">Your Matched Contractor</h2>
                
                <div style="margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #28a745;">
                    <h3 style="color: #28a745; margin-top: 0;">{contractor_info['name']}{company_info}</h3>
                    <p><strong>Email:</strong> <a href="mailto:{contractor_info['email']}">{contractor_info['email']}</a></p>
                    <p><strong>Phone:</strong> <a href="tel:{contractor_info.get('phone', '')}">{contractor_info.get('phone', 'Contact via email')}</a></p>
                    {specialties_info}
                    {f'<p style="color: #28a745; font-weight: bold;">{rating_info}</p>' if rating_info else ''}
                </div>
                
                <div style="margin: 30px 0;">
                    <h3 style="color: #2c5aa0;">What Happens Next?</h3>
                    <ol style="margin: 10px 0; padding-left: 20px; font-size: 16px;">
                        <li style="margin-bottom: 10px;"><strong>Contractor Contact:</strong> {contractor_info['name']} will reach out to you {response_time} to discuss your project in detail.</li>
                        <li style="margin-bottom: 10px;"><strong>Initial Consultation:</strong> They will schedule a convenient time to review your requirements and may arrange a site visit if needed.</li>
                        <li style="margin-bottom: 10px;"><strong>Detailed Quote:</strong> After the consultation, you'll receive a comprehensive quote with project timeline and costs.</li>
                        <li style="margin-bottom: 10px;"><strong>Project Planning:</strong> Once you approve the quote, you can begin planning the project details and schedule.</li>
                    </ol>
                </div>
                
                <div style="margin: 30px 0; padding: 20px; background: #fff3cd; border-radius: 6px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-top: 0;">💡 Tips for Success</h4>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Be prepared to discuss your project timeline and budget range</li>
                        <li>Have any additional photos or documents ready to share</li>
                        <li>Ask about licenses, insurance, and references</li>
                        <li>Get all agreements in writing before work begins</li>
                    </ul>
                </div>
                
                <div style="margin: 30px 0; padding: 20px; background: #d1ecf1; border-radius: 6px; border-left: 4px solid #17a2b8;">
                    <h4 style="color: #0c5460; margin-top: 0;">Need Help?</h4>
                    <p>If you don't hear from {contractor_info['name']} within 48 hours, or if you have any concerns, please don't hesitate to contact our support team.</p>
                    <p>You can also reach out to {contractor_info['name']} directly using the contact information provided above.</p>
                </div>
            </div>
            
            <div style="margin-top: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>Thank you for using our service matching platform!</p>
                <p>This email was sent to confirm your contractor match. Both you and {contractor_info['name']} have received this information.</p>
            </div>
        </body>
        </html>
        """
    
    def _build_customer_handoff_text(self, contractor_info: Dict[str, Any]) -> str:
        """Build plain text email content for customer handoff"""
        company_info = f" at {contractor_info['company']}" if contractor_info.get('company') else ""
        rating_info = f"Rating: {contractor_info['rating']}/5.0 stars" if contractor_info.get('rating') else ""
        specialties_info = ""
        if contractor_info.get('specialties'):
            specialties_list = ", ".join(contractor_info['specialties'])
            specialties_info = f"Specialties: {specialties_list}\n"
        
        response_time = contractor_info.get('response_time', 'within 24 hours')
        
        return f"""
✅ GREAT NEWS!

Your service request has been matched with a qualified contractor.

YOUR MATCHED CONTRACTOR
======================

{contractor_info['name']}{company_info}
Email: {contractor_info['email']}
Phone: {contractor_info.get('phone', 'Contact via email')}
{specialties_info}{rating_info}

WHAT HAPPENS NEXT?
==================

1. CONTRACTOR CONTACT: {contractor_info['name']} will reach out to you {response_time} to discuss your project in detail.

2. INITIAL CONSULTATION: They will schedule a convenient time to review your requirements and may arrange a site visit if needed.

3. DETAILED QUOTE: After the consultation, you'll receive a comprehensive quote with project timeline and costs.

4. PROJECT PLANNING: Once you approve the quote, you can begin planning the project details and schedule.

TIPS FOR SUCCESS
================

- Be prepared to discuss your project timeline and budget range
- Have any additional photos or documents ready to share
- Ask about licenses, insurance, and references
- Get all agreements in writing before work begins

NEED HELP?
==========

If you don't hear from {contractor_info['name']} within 48 hours, or if you have any concerns, please don't hesitate to contact our support team.

You can also reach out to {contractor_info['name']} directly using the contact information provided above.

Thank you for using our service matching platform!

This email was sent to confirm your contractor match. Both you and {contractor_info['name']} have received this information.
        """

# Global notification service instance
notification_service = None

def init_notification_service(mail_instance: Mail, db_engine=None):
    """Initialize the global notification service instance"""
    global notification_service
    notification_service = NotificationService(mail_instance, db_engine)
    return notification_service

def send_contractor_notification(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send detailed lead summary to contractor with customer responses and photos
    
    Args:
        lead_data: Dictionary containing complete lead information
        
    Returns:
        Dict with 'success' boolean and 'message' string
    """
    if not notification_service:
        logger.error("Notification service not initialized")
        return {'success': False, 'message': 'Notification service not available'}
    
    return notification_service.send_contractor_notification(lead_data)

def send_customer_handoff(customer_email: str, contractor_info: Dict[str, Any], lead_id: int = None) -> Dict[str, Any]:
    """
    Send professional handoff email to customer explaining next steps
    
    Args:
        customer_email: Customer's email address
        contractor_info: Dictionary with contractor details
        lead_id: Optional lead ID for logging
        
    Returns:
        Dict with 'success' boolean and 'message' string
    """
    if not notification_service:
        logger.error("Notification service not initialized")
        return {'success': False, 'message': 'Notification service not available'}
    
    return notification_service.send_customer_handoff(customer_email, contractor_info, lead_id)

def log_notification(lead_id: int, notification_type: str, status: str, 
                    recipient_email: str = None, subject: str = None, error_message: str = None) -> bool:
    """
    Log notification attempt to database with timestamp
    
    Args:
        lead_id: ID of the lead
        notification_type: Type of notification
        status: Status of notification (sent, failed, pending)
        recipient_email: Optional recipient email
        subject: Optional email subject
        error_message: Optional error message
        
    Returns:
        Boolean indicating success of logging operation
    """
    if not notification_service:
        logger.error("Notification service not initialized")
        return False
    
    return notification_service.log_notification(
        lead_id, notification_type, status, recipient_email, subject, error_message
    )