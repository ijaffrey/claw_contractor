"""
Contractor notification module for sending qualified lead notifications to contractors.
Handles email template formatting, contractor contact management, and notification delivery.
"""

import logging
import smtplib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import json
import sqlite3
import os
from dataclasses import dataclass, asdict

from email_sender import EmailSender, EmailConfig
from database_manager import DatabaseManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LeadData:
    """Data class for lead information."""
    lead_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    service_type: str
    project_description: str
    budget_range: str
    timeline: str
    urgency: str
    lead_score: float
    qualification_date: str
    lead_source: str
    additional_notes: str = ""


@dataclass
class ContractorInfo:
    """Data class for contractor information."""
    contractor_id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    specialties: List[str]
    service_areas: List[str]
    rating: float
    active: bool
    notification_preferences: Dict[str, Any]


class ContractorNotifier:
    """Handles contractor notifications for qualified leads."""
    
    def __init__(self, db_manager: DatabaseManager, email_sender: EmailSender):
        """
        Initialize the contractor notifier.
        
        Args:
            db_manager: Database manager instance
            email_sender: Email sender instance
        """
        self.db_manager = db_manager
        self.email_sender = email_sender
        self.email_templates = self._load_email_templates()
        
    def _load_email_templates(self) -> Dict[str, str]:
        """Load email templates from configuration or files."""
        templates = {
            'qualified_lead': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>New Qualified Lead</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .lead-details {{ background-color: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .detail-row {{ margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; color: #2c3e50; display: inline-block; width: 150px; }}
                    .value {{ color: #555; }}
                    .priority-high {{ color: #e74c3c; font-weight: bold; }}
                    .priority-medium {{ color: #f39c12; font-weight: bold; }}
                    .priority-low {{ color: #27ae60; font-weight: bold; }}
                    .score-badge {{ 
                        background-color: #3498db; 
                        color: white; 
                        padding: 5px 10px; 
                        border-radius: 15px; 
                        font-size: 14px; 
                        font-weight: bold;
                    }}
                    .action-buttons {{ text-align: center; margin: 20px 0; }}
                    .btn {{ 
                        display: inline-block; 
                        padding: 12px 25px; 
                        margin: 10px; 
                        text-decoration: none; 
                        border-radius: 5px; 
                        font-weight: bold;
                        transition: background-color 0.3s;
                    }}
                    .btn-primary {{ background-color: #3498db; color: white; }}
                    .btn-primary:hover {{ background-color: #2980b9; }}
                    .btn-secondary {{ background-color: #95a5a6; color: white; }}
                    .btn-secondary:hover {{ background-color: #7f8c8d; }}
                    .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>New Qualified Lead Alert</h1>
                        <p>High-quality lead matching your services</p>
                    </div>
                    
                    <div class="content">
                        <div class="lead-details">
                            <h2>Lead Information</h2>
                            <div class="detail-row">
                                <span class="label">Lead Score:</span>
                                <span class="score-badge">{lead_score}/100</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Name:</span>
                                <span class="value">{first_name} {last_name}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Email:</span>
                                <span class="value">{email}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Phone:</span>
                                <span class="value">{phone}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Location:</span>
                                <span class="value">{address}, {city}, {state} {zip_code}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Service Type:</span>
                                <span class="value">{service_type}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Budget Range:</span>
                                <span class="value">{budget_range}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Timeline:</span>
                                <span class="value">{timeline}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Urgency:</span>
                                <span class="value {urgency_class}">{urgency}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Lead Source:</span>
                                <span class="value">{lead_source}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Qualification Date:</span>
                                <span class="value">{qualification_date}</span>
                            </div>
                        </div>
                        
                        <div class="lead-details">
                            <h3>Project Description</h3>
                            <p>{project_description}</p>
                            
                            {additional_notes_section}
                        </div>
                        
                        <div class="action-buttons">
                            <a href="mailto:{email}?subject=Re: Your {service_type} Project" class="btn btn-primary">
                                Contact Lead
                            </a>
                            <a href="tel:{phone}" class="btn btn-secondary">
                                Call Now
                            </a>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>This lead was automatically qualified based on your service preferences.</p>
                        <p>Lead ID: {lead_id} | Sent: {notification_time}</p>
                        <p>To update your notification preferences, please contact support.</p>
                    </div>
                </div>
            </body>
            </html>
            ''',
            
            'lead_summary': '''
            Subject: New Qualified Lead - {service_type} Project ({lead_score}/100 Score)
            
            Dear {contractor_name},
            
            We have a new qualified lead that matches your service offerings:
            
            LEAD SUMMARY:
            - Name: {first_name} {last_name}
            - Contact: {email} | {phone}
            - Location: {city}, {state}
            - Service: {service_type}
            - Budget: {budget_range}
            - Timeline: {timeline}
            - Urgency: {urgency}
            - Lead Score: {lead_score}/100
            
            PROJECT DETAILS:
            {project_description}
            
            This lead was qualified on {qualification_date} and matches your:
            - Service specialties
            - Geographic service area
            - Minimum lead score requirements
            
            NEXT STEPS:
            1. Contact the lead within 2 hours for best results
            2. Reference Lead ID: {lead_id} in your communications
            3. Update lead status in your dashboard after contact
            
            Best regards,
            Lead Management System
            '''
        }
        return templates
    
    def get_matching_contractors(self, lead_data: LeadData) -> List[ContractorInfo]:
        """
        Get contractors that match the lead requirements.
        
        Args:
            lead_data: Lead information
            
        Returns:
            List of matching contractor information
        """
        try:
            query = '''
            SELECT 
                c.contractor_id,
                c.company_name,
                c.contact_name,
                c.email,
                c.phone,
                c.specialties,
                c.service_areas,
                c.rating,
                c.active,
                c.notification_preferences
            FROM contractors c
            WHERE c.active = 1
            AND (
                c.specialties LIKE ? OR 
                c.specialties LIKE '%all%' OR
                c.specialties LIKE '%general%'
            )
            AND (
                c.service_areas LIKE ? OR
                c.service_areas LIKE ? OR
                c.service_areas LIKE '%nationwide%'
            )
            ORDER BY c.rating DESC, c.contractor_id ASC
            '''
            
            # Prepare search parameters
            service_pattern = f'%{lead_data.service_type.lower()}%'
            city_pattern = f'%{lead_data.city.lower()}%'
            state_pattern = f'%{lead_data.state.lower()}%'
            
            results = self.db_manager.fetch_all(
                query, 
                (service_pattern, city_pattern, state_pattern)
            )
            
            contractors = []
            for row in results:
                try:
                    # Parse JSON fields
                    specialties = json.loads(row[5]) if row[5] else []
                    service_areas = json.loads(row[6]) if row[6] else []
                    notification_prefs = json.loads(row[9]) if row[9] else {}
                    
                    contractor = ContractorInfo(
                        contractor_id=row[0],
                        company_name=row[1],
                        contact_name=row[2],
                        email=row[3],
                        phone=row[4],
                        specialties=specialties,
                        service_areas=service_areas,
                        rating=float(row[7]),
                        active=bool(row[8]),
                        notification_preferences=notification_prefs
                    )
                    contractors.append(contractor)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Error parsing contractor data for ID {row[0]}: {e}")
                    continue
            
            logger.info(f"Found {len(contractors)} matching contractors for lead {lead_data.lead_id}")
            return contractors
            
        except Exception as e:
            logger.error(f"Error getting matching contractors: {e}")
            return []
    
    def format_lead_email(self, lead_data: LeadData, contractor_info: ContractorInfo, 
                         template_type: str = 'qualified_lead') -> Tuple[str, str]:
        """
        Format lead data into professional contractor email.
        
        Args:
            lead_data: Lead information
            contractor_info: Contractor information
            template_type: Type of email template to use
            
        Returns:
            Tuple of (subject, formatted_email_body)
        """
        try:
            template = self.email_templates.get(template_type, self.email_templates['qualified_lead'])
            
            # Determine urgency CSS class
            urgency_class_map = {
                'high': 'priority-high',
                'medium': 'priority-medium', 
                'low': 'priority-low'
            }
            urgency_class = urgency_class_map.get(lead_data.urgency.lower(), '')
            
            # Format additional notes section
            additional_notes_section = ""
            if lead_data.additional_notes.strip():
                additional_notes_section = f'''
                <h3>Additional Notes</h3>
                <p>{lead_data.additional_notes}</p>
                '''
            
            # Format the email body
            formatted_body = template.format(
                lead_id=lead_data.lead_id,
                first_name=lead_data.first_name,
                last_name=lead_data.last_name,
                email=lead_data.email,
                phone=lead_data.phone,
                address=lead_data.address,
                city=lead_data.city,
                state=lead_data.state,
                zip_code=lead_data.zip_code,
                service_type=lead_data.service_type,
                project_description=lead_data.project_description,
                budget_range=lead_data.budget_range,
                timeline=lead_data.timeline,
                urgency=lead_data.urgency.title(),
                urgency_class=urgency_class,
                lead_score=int(lead_data.lead_score),
                qualification_date=lead_data.qualification_date,
                lead_source=lead_data.lead_source,
                additional_notes_section=additional_notes_section,
                contractor_name=contractor_info.contact_name,
                notification_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Create subject line
            subject = f"New Qualified Lead - {lead_data.service_type} Project ({int(lead_data.lead_score)}/100 Score)"
            
            return subject, formatted_body
            
        except Exception as e:
            logger.error(f"Error formatting lead email: {e}")
            # Return basic fallback email
            subject = f"New Lead Alert - {lead_data.service_type}"
            body = f"""
            New lead available:
            Name: {lead_data.first_name} {lead_data.last_name}
            Service: {lead_data.service_type}
            Location: {lead_data.city}, {lead_data.state}
            Score: {lead_data.lead_score}/100
            
            Please check the system for full details.
            Lead ID: {lead_data.lead_id}
            """
            return subject, body
    
    def send_contractor_notification(self, lead_data: LeadData, 
                                   contractor_info: ContractorInfo) -> bool:
        """
        Send notification email to a specific contractor.
        
        Args:
            lead_data: Lead information
            contractor_info: Contractor information
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Check if contractor wants this type of notification
            notification_prefs = contractor_info.notification_preferences
            if not notification_prefs.get('email_notifications', True):
                logger.info(f"Skipping notification for contractor {contractor_info.contractor_id} - disabled")
                return True
            
            # Check minimum lead score requirement
            min_score = notification_prefs.get('minimum_lead_score', 0)
            if lead_data.lead_score < min_score:
                logger.info(f"Lead score {lead_data.lead_score} below minimum {min_score} for contractor {contractor_info.contractor_id}")
                return True
            
            # Format the email
            subject, body = self.format_lead_email(lead_data, contractor_info)
            
            # Send the email
            success = self.email_sender.send_email(
                to_email=contractor_info.email,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if success:
                self._log_notification(lead_data.lead_id, contractor_info.contractor_id, 'sent')
                logger.info(f"Notification sent to contractor {contractor_info.contractor_id}")
            else:
                self._log_notification(lead_data.lead_id, contractor_info.contractor_id, 'failed')
                logger.error(f"Failed to send notification to contractor {contractor_info.contractor_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending contractor notification: {e}")
            self._log_notification(lead_data.lead_id, contractor_info.contractor_id, 'error', str(e))
            return False
    
    def notify_qualified_lead(self, lead_data: LeadData) -> Dict[str, Any]:
        """
        Send notifications to all matching contractors for a qualified lead.
        
        Args:
            lead_data: Qualified lead information
            
        Returns:
            Dictionary with notification results
        """
        try:
            logger.info(f"Processing notifications for qualified lead {lead_data.lead_id}")
            
            # Get matching contractors
            contractors = self.get_matching_contractors(lead_data)
            
            if not contractors:
                logger.warning(f"No matching contractors found for lead {lead_data.lead_id}")
                return {
                    'success': False,
                    'total_contractors': 0,
                    'notifications_sent': 0,
                    'notifications_failed': 0,
                    'errors': ['No matching contractors found']
                }
            
            # Send notifications
            notifications_sent = 0
            notifications_failed = 0
            errors = []
            
            for contractor in contractors:
                try:
                    success = self.send_contractor_notification(lead_data, contractor)
                    if success:
                        notifications_sent += 1
                    else:
                        notifications_failed += 1
                        errors.append(f"Failed to notify contractor {contractor.contractor_id}")
                        
                except Exception as e:
                    notifications_failed += 1
                    error_msg = f"Error notifying contractor {contractor.contractor_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update lead notification status
            self._update_lead_notification_status(
                lead_data.lead_id, 
                notifications_sent, 
                notifications_failed
            )
            
            result = {
                'success': notifications_sent > 0,
                'total_contractors': len(contractors),
                'notifications_sent': notifications_sent,
                'notifications_failed': notifications_failed,
                'errors': errors
            }
            
            logger.info(f"Lead {lead_data.lead_id} notifications completed: {notifications_sent} sent, {notifications_failed} failed")
            return result
            
        except Exception as e:
            logger.error(f"Error in notify_qualified_lead: {e}")
            return {
                'success': False,
                'total_contractors': 0,
                'notifications_sent': 0,
                'notifications_failed': 0,
                'errors': [f"System error: {str(e)}"]
            }
    
    def _log_notification(self, lead_id: str, contractor_id: str, 
                         status: str, error_message: str = None):
        """
        Log notification attempt to database.
        
        Args:
            lead_id: Lead identifier
            contractor_id: Contractor identifier
            status: Notification status (sent, failed, error)
            error_message: Error message if applicable
        """
        try:
            query = '''
            INSERT INTO notification_log (
                lead_id, contractor_id, notification_type, status, 
                sent_at, error_message
            ) VALUES (?, ?, 'email', ?, ?, ?)
            '''
            
            self.db_manager.execute_query(
                query,
                (lead_id, contractor_id, status, datetime.now().isoformat(), error_message)
            )
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    def _update_lead_notification_status(self, lead_id: str, 
                                       sent_count: int, failed_count: int):
        """
        Update lead record with notification statistics.
        
        Args:
            lead_id: Lead identifier
            sent_count: Number of successful notifications
            failed_count: Number of failed notifications
        """
        try:
            query = '''
            UPDATE leads SET 
                notifications_sent = ?,
                notifications_failed = ?,
                last_notification_date = ?,
                notification_status = ?
            WHERE lead_id = ?
            '''
            
            status = 'completed' if sent_count > 0 else 'failed'
            
            self.db_manager.execute_query(
                query,
                (sent_count, failed_count, datetime.now().isoformat(), status, lead_id)
            )
            
        except Exception as e:
            logger.error(f"Error updating lead notification status: {e}")
    
    def get_contractor_by_id(self, contractor_id: str) -> Optional[ContractorInfo]:
        """
        Get contractor information by ID.
        
        Args:
            contractor_id: Contractor identifier
            
        Returns:
            ContractorInfo object or None if not found
        """
        try:
            query = '''
            SELECT 
                contractor_id, company_name, contact_name, email, phone,
                specialties, service_areas, rating, active, notification_preferences
            FROM contractors 
            WHERE contractor_id = ?
            '''
            
            result = self.db_manager.fetch_one(query, (contractor_id,))
            
            if not result:
                return None
            
            return ContractorInfo(
                contractor_id=result[0],
                company_name=result[1],
                contact_name=result[2],
                email=result[3],
                phone=result[4],
                specialties=json.loads(result[5]) if result[5] else [],
                service_areas=json.loads(result[6]) if result[6] else [],
                rating=float(result[7]),
                active=bool(result[8]),
                notification_preferences=json.loads(result[9]) if result[9] else {}
            )
            
        except Exception as e:
            logger.error(f"Error getting contractor by ID {contractor_id}: {e}")
            return None
    
    def update_contractor_notification_preferences(self, contractor_id: str, 
                                                 preferences: Dict[str, Any]) -> bool:
        """
        Update contractor notification preferences.
        
        Args:
            contractor_id: Contractor identifier
            preferences: Notification preferences dictionary
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            query = '''
            UPDATE contractors 
            SET notification_preferences = ?, updated_at = ?
            WHERE contractor_id = ?
            '''
            
            preferences_json = json.dumps(preferences)
            
            self.db_manager.execute_query(
                query,
                (preferences_json, datetime.now().isoformat(), contractor_id)
            )
            
            logger.info(f"Updated notification preferences for contractor {contractor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating contractor notification preferences: {e}")
            return False
    
    def get_notification_history(self, lead_id: str = None, 
                               contractor_id: str = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get notification history.
        
        Args:
            lead_id: Optional lead ID filter
            contractor_id: Optional contractor ID filter
            limit: Maximum number of records to return
            
        Returns:
            List of notification history records
        """
        try:
            query = '''
            SELECT 
                nl.id, nl.lead_id, nl.contractor_id, nl.notification_type,
                nl.status, nl.sent_at, nl.error_message,
                l.service_type, l.first_name, l.last_name,
                c.company_name, c.contact_name
            FROM notification_log nl
            LEFT JOIN leads l ON nl.lead_id = l.lead_id
            LEFT JOIN contractors c ON nl.contractor_id = c.contractor_id
            WHERE 1=1
            '''
            
            params = []
            
            if lead_id:
                query += " AND nl.lead_id = ?"
                params.append(lead_id)
            
            if contractor_id:
                query += " AND nl.contractor_id = ?"
                params.append(contractor_id)
            
            query += " ORDER BY nl.sent_at DESC LIMIT ?"
            params.append(limit)
            
            results = self.db_manager.fetch_all(query, tuple(params))
            
            history = []
            for row in results:
                history.append({
                    'id': row[0],
                    'lead_id': row[1],
                    'contractor_id': row[2],
                    'notification_type': row[3],
                    'status': row[4],
                    'sent_at': row[5],
                    'error_message': row[6],
                    'service_type': row[7],
                    'lead_name': f"{row[8]} {row[9]}" if row[8] else None,
                    'company_name': row[10],
                    'contact_name': row[11]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []
    
    def test_contractor_notification(self, contractor_id: str, test_lead_data: Dict[str, Any]) -> bool:
        """
        Send a test notification to a contractor.
        
        Args:
            contractor_id: Contractor identifier
            test_lead_data: Test lead data
            
        Returns:
            True if test notification sent successfully, False otherwise
        """
        try:
            contractor = self.get_contractor_by_id(contractor_id)
            if not contractor:
                logger.error(f"Contractor {contractor_id} not found")
                return False
            
            # Create test lead data
            lead_data = LeadData(
                lead_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                first_name=test_lead_data.get('first_name', 'John'),
                last_name=test_lead_data.get('last_name', 'Doe'),
                email=test_lead_data.get('email', 'john.doe@example.com'),
                phone=test_lead_data.get('phone', '(555) 123-4567'),
                address=test_lead_data.get('address', '123 Main St'),
                city=test_lead_data.get('city', 'Sample City'),
                state=test_lead_data.get('state', 'ST'),
                zip_code=test_lead_data.get('zip_code', '12345'),
                service_type=test_lead_data.get('service_type', 'General Contracting'),
                project_description=test_lead_data.get('project_description', 'This is a test lead for notification testing purposes.'),
                budget_range=test_lead_data.get('budget_range', '$5,000 - $10,000'),
                timeline=test_lead_data.get('timeline', '1-2 months'),
                urgency=test_lead_data.get('urgency', 'medium'),
                lead_score=float(test_lead_data.get('lead_score', 85)),
                qualification_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                lead_source=test_lead_data.get('lead_source', 'Test System'),
                additional_notes="This is a TEST notification. Please do not contact this lead."
            )
            
            # Format and send test email
            subject, body = self.format_lead_email(lead_data, contractor)
            subject = f"[TEST] {subject}"
            
            success = self.email_sender.send_email(
                to_email=contractor.email,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if success:
                logger.info(f"Test notification sent to contractor {contractor_id}")
            else:
                logger.error(f"Failed to send test notification to contractor {contractor_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending test contractor notification: {e}")
            return False


def create_contractor_notifier(db_path: str, email_config: EmailConfig) -> ContractorNotifier:
    """
    Factory function to create a ContractorNotifier instance.
    
    Args:
        db_path: Path to SQLite database
        email_config: Email configuration
        
    Returns:
        ContractorNotifier instance
    """
    db_manager = DatabaseManager(db_path)
    email_sender = EmailSender(email_config)
    return ContractorNotifier(db_manager, email_sender)


# Example usage and testing
if __name__ == "__main__":
    # Configuration
    DB_PATH = "leads_database.db"
    
    email_config = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your-email@gmail.com",
        password="your-app-password",
        use_tls=True
    )
    
    # Create notifier
    notifier = create_contractor_notifier(DB_PATH, email_config)
    
    # Example lead data for testing
    test_lead = LeadData(
        lead_id="LEAD-20240101-001",
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone="(555) 123-4567",
        address="123 Main Street",
        city="Springfield",
        state="IL",
        zip_code="62701",
        service_type="Kitchen Renovation",
        project_description="Complete kitchen remodel including new cabinets, countertops, and appliances.",
        budget_range="$25,000 - $35,000",
        timeline="3-4 months",
        urgency="medium",
        lead_score=87.5,
        qualification_date="2024-01-01 10:30:00",
        lead_source="Website Form",
        