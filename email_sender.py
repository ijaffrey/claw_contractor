import smtplib
import ssl
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import os
from dataclasses import dataclass


@dataclass
class EmailConfig:
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    sender_name: str = "Lead Management System"
    max_retries: int = 3
    retry_delay: int = 2


@dataclass
class LeadData:
    customer_name: str
    customer_email: str
    customer_phone: str
    service_type: str
    description: str
    location: str
    budget: str
    urgency: str
    lead_id: str
    created_at: datetime


class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def configure_smtp(self, sender_email: str, app_password: str, sender_name: str = None) -> bool:
        """
        Configure SMTP settings for Gmail using app passwords.
        
        Args:
            sender_email: Gmail address
            app_password: Gmail app password (not regular password)
            sender_name: Optional sender display name
            
        Returns:
            bool: True if configuration is successful
        """
        try:
            self.config.sender_email = sender_email
            self.config.sender_password = app_password
            if sender_name:
                self.config.sender_name = sender_name
                
            # Test connection
            return self._test_smtp_connection()
            
        except Exception as e:
            self.logger.error(f"SMTP configuration failed: {str(e)}")
            return False
    
    def _test_smtp_connection(self) -> bool:
        """Test SMTP connection without sending email."""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.sender_email, self.config.sender_password)
                return True
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {str(e)}")
            return False
    
    def validate_email_addresses(self, emails: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate email addresses using regex pattern.
        
        Args:
            emails: List of email addresses to validate
            
        Returns:
            Tuple of (valid_emails, invalid_emails)
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if email and re.match(email_pattern, email.strip()):
                valid_emails.append(email.strip().lower())
            else:
                invalid_emails.append(email)
                
        return valid_emails, invalid_emails
    
    def format_email_html(self, template_type: str, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Format professional HTML email templates with fallback plain text.
        
        Args:
            template_type: Type of email template ('contractor_notification', 'customer_handoff')
            data: Dictionary containing template data
            
        Returns:
            Tuple of (html_content, plain_text_content)
        """
        if template_type == 'contractor_notification':
            return self._format_contractor_notification_html(data)
        elif template_type == 'customer_handoff':
            return self._format_customer_handoff_html(data)
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def _format_contractor_notification_html(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Format contractor notification email template."""
        lead = data.get('lead')
        contractor_name = data.get('contractor_name', 'Contractor')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .lead-info {{ background: white; padding: 20px; border-radius: 6px; margin: 20px 0; 
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .info-row {{ display: flex; margin-bottom: 15px; }}
                .info-label {{ font-weight: bold; width: 140px; color: #555; }}
                .info-value {{ flex: 1; }}
                .urgency-high {{ color: #dc3545; font-weight: bold; }}
                .urgency-medium {{ color: #fd7e14; font-weight: bold; }}
                .urgency-low {{ color: #28a745; font-weight: bold; }}
                .cta-button {{ display: inline-block; background: #28a745; color: white; 
                             padding: 12px 25px; text-decoration: none; border-radius: 5px; 
                             margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 New Lead Alert</h1>
                    <p>A new lead has been assigned to you</p>
                </div>
                
                <div class="content">
                    <p>Hello <strong>{contractor_name}</strong>,</p>
                    
                    <p>You have received a new lead opportunity. Please review the details below and respond promptly:</p>
                    
                    <div class="lead-info">
                        <h3>Lead Details</h3>
                        <div class="info-row">
                            <span class="info-label">Lead ID:</span>
                            <span class="info-value">{lead.lead_id}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Customer:</span>
                            <span class="info-value">{lead.customer_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Phone:</span>
                            <span class="info-value">{lead.customer_phone}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Email:</span>
                            <span class="info-value">{lead.customer_email}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Service Type:</span>
                            <span class="info-value">{lead.service_type}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Location:</span>
                            <span class="info-value">{lead.location}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Budget:</span>
                            <span class="info-value">{lead.budget}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Urgency:</span>
                            <span class="info-value urgency-{lead.urgency.lower()}">{lead.urgency}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Description:</span>
                            <span class="info-value">{lead.description}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Created:</span>
                            <span class="info-value">{lead.created_at.strftime('%B %d, %Y at %I:%M %p')}</span>
                        </div>
                    </div>
                    
                    <p><strong>Next Steps:</strong></p>
                    <ul>
                        <li>Contact the customer within 2 hours for high urgency leads</li>
                        <li>Schedule an appointment or consultation</li>
                        <li>Update lead status in your dashboard</li>
                        <li>Provide accurate timeline and pricing estimates</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="#" class="cta-button">View Full Lead Details</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from the Lead Management System</p>
                    <p>Please do not reply to this email</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        NEW LEAD ALERT
        
        Hello {contractor_name},
        
        You have received a new lead opportunity:
        
        LEAD DETAILS:
        Lead ID: {lead.lead_id}
        Customer: {lead.customer_name}
        Phone: {lead.customer_phone}
        Email: {lead.customer_email}
        Service Type: {lead.service_type}
        Location: {lead.location}
        Budget: {lead.budget}
        Urgency: {lead.urgency}
        Description: {lead.description}
        Created: {lead.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        NEXT STEPS:
        - Contact the customer within 2 hours for high urgency leads
        - Schedule an appointment or consultation
        - Update lead status in your dashboard
        - Provide accurate timeline and pricing estimates
        
        This is an automated notification. Please do not reply to this email.
        """
        
        return html_content, plain_text
    
    def _format_customer_handoff_html(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Format customer handoff email template."""
        lead = data.get('lead')
        contractor_info = data.get('contractor_info', {})
        estimated_contact_time = data.get('estimated_contact_time', '2-4 hours')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .contractor-info {{ background: white; padding: 20px; border-radius: 6px; margin: 20px 0; 
                                  box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .timeline {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3; margin: 20px 0; }}
                .important {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; 
                            color: #856404; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Your Request Has Been Received</h1>
                    <p>We're connecting you with a qualified contractor</p>
                </div>
                
                <div class="content">
                    <p>Dear <strong>{lead.customer_name}</strong>,</p>
                    
                    <p>Thank you for submitting your service request. We've successfully received your information and are excited to help you with your <strong>{lead.service_type}</strong> project.</p>
                    
                    <div class="timeline">
                        <h3>📋 Your Request Summary</h3>
                        <p><strong>Service:</strong> {lead.service_type}</p>
                        <p><strong>Location:</strong> {lead.location}</p>
                        <p><strong>Budget Range:</strong> {lead.budget}</p>
                        <p><strong>Project Description:</strong> {lead.description}</p>
                        <p><strong>Request ID:</strong> {lead.lead_id}</p>
                    </div>
                    
                    <div class="contractor-info">
                        <h3>🔧 What Happens Next</h3>
                        <ul>
                            <li><strong>Contractor Assignment:</strong> We've matched you with a qualified contractor in your area</li>
                            <li><strong>Expected Contact:</strong> You should receive a call within <strong>{estimated_contact_time}</strong></li>
                            <li><strong>Initial Consultation:</strong> The contractor will discuss your project details and schedule a visit if needed</li>
                            <li><strong>Quote & Timeline:</strong> You'll receive a detailed estimate and project timeline</li>
                        </ul>
                    </div>
                    
                    <div class="important">
                        <h4>📱 Important Contact Information</h4>
                        <p>Please keep your phone <strong>{lead.customer_phone}</strong> available as our contractor will be calling you soon.</p>
                        <p>If you need to update your contact information or have questions, please contact our support team.</p>
                    </div>
                    
                    <h3>💡 Tips for Your Consultation</h3>
                    <ul>
                        <li>Prepare a list of specific questions about your project</li>
                        <li>Have photos ready if you discussed the project over phone</li>
                        <li>Be clear about your timeline and budget expectations</li>
                        <li>Ask about licensing, insurance, and references</li>
                        <li>Get detailed written estimates before work begins</li>
                    </ul>
                    
                    <div class="timeline">
                        <h4>⏰ Timeline Expectations</h4>
                        <p><strong>Contractor Contact:</strong> Within {estimated_contact_time}</p>
                        <p><strong>Initial Consultation:</strong> Within 24-48 hours</p>
                        <p><strong>Written Estimate:</strong> Within 2-3 business days</p>
                        <p><strong>Project Start:</strong> Based on your agreement with the contractor</p>
                    </div>
                    
                    <p>We're committed to connecting you with reliable, professional contractors. If you don't hear from anyone within the expected timeframe, please contact our support team immediately.</p>
                    
                    <p>Thank you for choosing our service!</p>
                    
                    <p>Best regards,<br>
                    <strong>The Lead Management Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>This confirmation was sent to {lead.customer_email}</p>
                    <p>Request ID: {lead.lead_id} | Submitted: {lead.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        YOUR REQUEST HAS BEEN RECEIVED
        
        Dear {lead.customer_name},
        
        Thank you for submitting your service request. We've successfully received your information and are excited to help you with your {lead.service_type} project.
        
        YOUR REQUEST SUMMARY:
        Service: {lead.service_type}
        Location: {lead.location}
        Budget Range: {lead.budget}
        Project Description: {lead.description}
        Request ID: {lead.lead_id}
        
        WHAT HAPPENS NEXT:
        - Contractor Assignment: We've matched you with a qualified contractor in your area
        - Expected Contact: You should receive a call within {estimated_contact_time}
        - Initial Consultation: The contractor will discuss your project details and schedule a visit if needed
        - Quote & Timeline: You'll receive a detailed estimate and project timeline
        
        IMPORTANT CONTACT INFORMATION:
        Please keep your phone {lead.customer_phone} available as our contractor will be calling you soon.
        If you need to update your contact information or have questions, please contact our support team.
        
        TIPS FOR YOUR CONSULTATION:
        - Prepare a list of specific questions about your project
        - Have photos ready if you discussed the project over phone
        - Be clear about your timeline and budget expectations
        - Ask about licensing, insurance, and references
        - Get detailed written estimates before work begins
        
        TIMELINE EXPECTATIONS:
        Contractor Contact: Within {estimated_contact_time}
        Initial Consultation: Within 24-48 hours
        Written Estimate: Within 2-3 business days
        Project Start: Based on your agreement with the contractor
        
        We're committed to connecting you with reliable, professional contractors. If you don't hear from anyone within the expected timeframe, please contact our support team immediately.
        
        Thank you for choosing our service!
        
        Best regards,
        The Lead Management Team
        
        This confirmation was sent to {lead.customer_email}
        Request ID: {lead.lead_id} | Submitted: {lead.created_at.strftime('%B %d, %Y at %I:%M %p')}
        """
        
        return html_content, plain_text
    
    def handle_email_errors(self, func, *args, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Handle email errors with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (success, error_message)
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                result = func(*args, **kwargs)
                return True, None
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = f"SMTP Authentication failed: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
                
            except smtplib.SMTPRecipientsRefused as e:
                error_msg = f"Recipients refused: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
                
            except smtplib.SMTPException as e:
                error_msg = f"SMTP error: {str(e)}"
                self.logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                last_error = error_msg
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
        
        return False, f"All {self.config.max_retries} attempts failed. Last error: {last_error}"
    
    def _send_email(self, to_emails: List[str], subject: str, html_content: str, plain_text: str) -> bool:
        """Internal method to send email with both HTML and plain text content."""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.config.sender_email, self.config.sender_password)
            
            for recipient in to_emails:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{self.config.sender_name} <{self.config.sender_email}>"
                msg["To"] = recipient
                
                # Add plain text and HTML parts
                text_part = MIMEText(plain_text, "plain")
                html_part = MIMEText(html_content, "html")
                
                msg.attach(text_part)
                msg.attach(html_part)
                
                server.send_message(msg)
                
        return True
    
    def send_contractor_notification(self, contractor_email: str, contractor_name: str, lead_data: LeadData) -> Tuple[bool, Optional[str]]:
        """
        Send formatted lead summary to contractors via email.
        
        Args:
            contractor_email: Contractor's email address
            contractor_name: Contractor's name
            lead_data: Lead information
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate email
            valid_emails, invalid_emails = self.validate_email_addresses([contractor_email])
            if invalid_emails:
                return False, f"Invalid email address: {contractor_email}"
            
            # Format email content
            template_data = {
                'lead': lead_data,
                'contractor_name': contractor_name
            }
            html_content, plain_text = self.format_email_html('contractor_notification', template_data)
            
            # Create subject
            urgency_prefix = "🚨 URGENT" if lead_data.urgency.upper() == "HIGH" else "📋"
            subject = f"{urgency_prefix} New Lead: {lead_data.service_type} - {lead_data.location}"
            
            # Send email with error handling
            success, error = self.handle_email_errors(
                self._send_email,
                valid_emails,
                subject,
                html_content,
                plain_text
            )
            
            if success:
                self.logger.info(f"Contractor notification sent successfully to {contractor_email} for lead {lead_data.lead_id}")
            else:
                self.logger.error(f"Failed to send contractor notification to {contractor_email}: {error}")
                
            return success, error
            
        except Exception as e:
            error_msg = f"Error sending contractor notification: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def send_customer_handoff(self, customer_email: str, customer_name: str, lead_data: LeadData, contractor_info: Dict[str, Any] = None, estimated_contact_time: str = "2-4 hours") -> Tuple[bool, Optional[str]]:
        """
        Send handoff message to customers explaining next steps.
        
        Args:
            customer_email: Customer's email address
            customer_name: Customer's name
            lead_data: Lead information
            contractor_info: Optional contractor information
            estimated_contact_time: Expected contact timeframe
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate email
            valid_emails, invalid_emails = self.validate_email_addresses([customer_email])
            if invalid_emails:
                return False, f"Invalid email address: {customer_email}"
            
            # Format email content
            template_data = {
                'lead': lead_data,
                'contractor_info': contractor_info or {},
                'estimated_contact_time': estimated_contact_time
            }
            html_content, plain_text = self.format_email_html('customer_handoff', template_data)
            
            # Create subject
            subject = f"✅ Confirmation: Your {lead_data.service_type} Request (#{lead_data.lead_id})"
            
            # Send email with error handling
            success, error = self.handle_email_errors(
                self._send_email,
                valid_emails,
                subject,
                html_content,
                plain_text
            )
            
            if success:
                self.logger.info(f"Customer handoff email sent successfully to {customer_email} for lead {lead_data.lead_id}")
            else:
                self.logger.error(f"Failed to send customer handoff email to {customer_email}: {error}")
                
            return success, error
            
        except Exception as e:
            error_msg = f"Error sending customer handoff email: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg


# Usage example and configuration
def create_email_sender_from_env() -> EmailSender:
    """Create EmailSender instance from environment variables."""
    config = EmailConfig(
        sender_email=os.getenv('GMAIL_ADDRESS', ''),
        sender_password=os.getenv('GMAIL_APP_PASSWORD', ''),
        sender_name=os.getenv('SENDER_NAME', 'Lead Management System')
    )
    return EmailSender(config)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create email sender
    email_sender = create_email_sender_from_env()
    
    # Example lead data
    sample_lead = LeadData(
        customer_name="John Smith",
        customer_email="john.smith@example.com",
        customer_phone="(555) 123-4567",
        service_type="Kitchen Remodeling",
        description="Complete kitchen renovation including cabinets, countertops, and appliances",
        location="Los Angeles, CA",
        budget="$15,000 - $25,000",
        urgency="High",
        lead_id="LEAD-2024-001",
        created_at=datetime.now()
    )
    
    # Send contractor notification
    success, error = email_sender.send_contractor_notification(
        contractor_email="contractor@example.com",
        contractor_name="Mike Johnson",
        lead_data=sample_lead
    )
    
    if success:
        print("Contractor notification sent successfully")
    else:
        print(f"Failed to send contractor notification: {error}")
    
    # Send customer handoff
    success, error = email_sender.send_customer_handoff(
        customer_email=sample_lead.customer_email,
        customer_name=sample_lead.customer_name,
        lead_data=sample_lead,
        estimated_contact_time="2-3 hours"
    )
    
    if success:
        print("Customer handoff email sent successfully")
    else:
        print(f"Failed to send customer handoff email: {error}")