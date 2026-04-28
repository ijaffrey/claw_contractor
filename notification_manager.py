import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import os
from dataclasses import dataclass
from database_manager import DatabaseManager


@dataclass
class LeadData:
    lead_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    problem_description: str
    budget_range: str
    location: str
    photos: List[Dict]
    responses: Dict
    qualification_score: float
    created_at: datetime
    updated_at: datetime


class NotificationManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.company_email = os.getenv("COMPANY_EMAIL", "leads@yourcompany.com")
        self.company_name = os.getenv("COMPANY_NAME", "Your Contractor Service")

    def detect_qualified_lead(self, lead_id: str) -> Tuple[bool, List[str]]:
        """
        Checks if a lead has all required qualification data.

        Args:
            lead_id: The unique identifier for the lead

        Returns:
            Tuple of (is_qualified: bool, missing_requirements: List[str])
        """
        try:
            lead_data = self.db_manager.get_lead_by_id(lead_id)
            if not lead_data:
                return False, ["Lead not found"]

            missing_requirements = []

            # Check contact information
            if (
                not lead_data.get("customer_name")
                or not lead_data["customer_name"].strip()
            ):
                missing_requirements.append("Customer name")

            if not lead_data.get("customer_email") or not self._is_valid_email(
                lead_data["customer_email"]
            ):
                missing_requirements.append("Valid customer email")

            if (
                not lead_data.get("customer_phone")
                or not lead_data["customer_phone"].strip()
            ):
                missing_requirements.append("Customer phone number")

            # Check problem description
            if (
                not lead_data.get("problem_description")
                or len(lead_data["problem_description"].strip()) < 20
            ):
                missing_requirements.append(
                    "Detailed problem description (minimum 20 characters)"
                )

            # Check photos analyzed
            photos = lead_data.get("photos", [])
            if not photos or len(photos) == 0:
                missing_requirements.append("At least one photo")
            else:
                analyzed_photos = [p for p in photos if p.get("analyzed", False)]
                if len(analyzed_photos) == 0:
                    missing_requirements.append("Photos must be analyzed")

            # Check budget confirmation
            if (
                not lead_data.get("budget_range")
                or lead_data["budget_range"] == "not_specified"
            ):
                missing_requirements.append("Budget confirmation")

            # Check location information
            if not lead_data.get("location") or not lead_data["location"].strip():
                missing_requirements.append("Service location")

            # Check qualification score threshold
            qualification_score = lead_data.get("qualification_score", 0)
            if qualification_score < 70:  # Minimum 70% qualification score
                missing_requirements.append(
                    f"Qualification score too low ({qualification_score}% - minimum 70% required)"
                )

            is_qualified = len(missing_requirements) == 0

            self.logger.info(
                f"Lead {lead_id} qualification check: {'QUALIFIED' if is_qualified else 'NOT QUALIFIED'}"
            )
            if missing_requirements:
                self.logger.info(
                    f"Missing requirements: {', '.join(missing_requirements)}"
                )

            return is_qualified, missing_requirements

        except Exception as e:
            self.logger.error(
                f"Error checking lead qualification for {lead_id}: {str(e)}"
            )
            return False, ["Error checking qualification status"]

    def generate_contractor_notification_email(
        self, lead_id: str, contractor_email: str
    ) -> Dict[str, str]:
        """
        Creates detailed email for contractor notification with complete lead information.

        Args:
            lead_id: The unique identifier for the lead
            contractor_email: Email address of the contractor to notify

        Returns:
            Dictionary containing email subject, body, and metadata
        """
        try:
            lead_data = self.db_manager.get_lead_by_id(lead_id)
            if not lead_data:
                raise ValueError(f"Lead {lead_id} not found")

            # Check if lead is qualified
            is_qualified, missing_requirements = self.detect_qualified_lead(lead_id)
            if not is_qualified:
                self.logger.warning(
                    f"Attempting to notify contractor for unqualified lead {lead_id}"
                )

            lead_summary = self.format_lead_summary(lead_data)

            # Generate email subject
            subject = f"New Qualified Lead #{lead_id} - {lead_data.get('problem_type', 'Service Request')} in {lead_data.get('location', 'Unknown Location')}"

            # Generate email body
            body = self._create_contractor_email_body(
                lead_data, lead_summary, is_qualified
            )

            email_data = {
                "subject": subject,
                "body": body,
                "recipient": contractor_email,
                "lead_id": lead_id,
                "type": "contractor_notification",
                "qualified": is_qualified,
                "created_at": datetime.now().isoformat(),
            }

            self.logger.info(
                f"Generated contractor notification email for lead {lead_id}"
            )
            return email_data

        except Exception as e:
            self.logger.error(
                f"Error generating contractor notification email for {lead_id}: {str(e)}"
            )
            raise

    def generate_customer_handoff_message(
        self, lead_id: str, contractor_info: Dict
    ) -> Dict[str, str]:
        """
        Creates professional message explaining next steps and contractor contact process.

        Args:
            lead_id: The unique identifier for the lead
            contractor_info: Dictionary containing contractor contact information

        Returns:
            Dictionary containing message content and metadata
        """
        try:
            lead_data = self.db_manager.get_lead_by_id(lead_id)
            if not lead_data:
                raise ValueError(f"Lead {lead_id} not found")

            customer_name = lead_data.get("customer_name", "Valued Customer")
            contractor_name = contractor_info.get("name", "Your assigned contractor")
            contractor_phone = contractor_info.get("phone", "")
            contractor_email = contractor_info.get("email", "")
            estimated_contact_time = contractor_info.get(
                "estimated_contact_time", "24 hours"
            )

            message_body = f"""Dear {customer_name},

Thank you for using {self.company_name} for your service needs. We're pleased to inform you that we've successfully matched you with a qualified contractor for your project.

**Your Project Details:**
- Request ID: #{lead_id}
- Service Type: {lead_data.get('problem_type', 'Service Request')}
- Location: {lead_data.get('location', 'As specified')}
- Budget Range: {self._format_budget_range(lead_data.get('budget_range', 'To be discussed'))}

**Your Assigned Contractor:**
- Name: {contractor_name}
- Phone: {contractor_phone}
- Email: {contractor_email}
- Estimated Contact Time: Within {estimated_contact_time}

**What Happens Next:**
1. Your assigned contractor will contact you directly within {estimated_contact_time}
2. They will discuss your specific needs and provide a detailed assessment
3. You'll receive a customized quote based on your requirements
4. If you're satisfied with the proposal, you can schedule the work directly with the contractor

**Important Information:**
- All work arrangements, pricing, and scheduling will be handled directly between you and the contractor
- We recommend getting a written estimate before any work begins
- The contractor is licensed, insured, and has been pre-screened by our team
- You can contact us at {self.company_email} if you have any questions about this handoff process

**Quality Assurance:**
We may follow up with you after the project completion to ensure you received excellent service. Your feedback helps us maintain the highest standards for all our contractor partners.

Thank you for choosing {self.company_name}. We're confident you'll be satisfied with the professional service you receive.

Best regards,
The {self.company_name} Team
{self.company_email}

---
This is an automated message regarding your service request #{lead_id}.
"""

            message_data = {
                "subject": f"Your Contractor Assignment - Request #{lead_id}",
                "body": message_body,
                "recipient": lead_data.get("customer_email"),
                "lead_id": lead_id,
                "contractor_id": contractor_info.get("id"),
                "type": "customer_handoff",
                "created_at": datetime.now().isoformat(),
            }

            self.logger.info(f"Generated customer handoff message for lead {lead_id}")
            return message_data

        except Exception as e:
            self.logger.error(
                f"Error generating customer handoff message for {lead_id}: {str(e)}"
            )
            raise

    def format_lead_summary(self, lead_data: Dict) -> Dict[str, any]:
        """
        Compiles all customer data into structured format for easy consumption.

        Args:
            lead_data: Raw lead data from database

        Returns:
            Formatted and structured lead summary
        """
        try:
            # Basic lead information
            summary = {
                "lead_id": lead_data.get("lead_id"),
                "created_at": lead_data.get("created_at"),
                "updated_at": lead_data.get("updated_at", datetime.now()),
                "qualification_score": lead_data.get("qualification_score", 0),
            }

            # Customer information
            summary["customer"] = {
                "name": lead_data.get("customer_name", ""),
                "email": lead_data.get("customer_email", ""),
                "phone": lead_data.get("customer_phone", ""),
                "preferred_contact_method": lead_data.get(
                    "preferred_contact_method", "phone"
                ),
            }

            # Project details
            summary["project"] = {
                "problem_type": lead_data.get("problem_type", ""),
                "problem_description": lead_data.get("problem_description", ""),
                "location": lead_data.get("location", ""),
                "urgency": lead_data.get("urgency", "normal"),
                "property_type": lead_data.get("property_type", ""),
                "access_requirements": lead_data.get("access_requirements", ""),
            }

            # Budget information
            summary["budget"] = {
                "range": lead_data.get("budget_range", ""),
                "flexibility": lead_data.get("budget_flexibility", ""),
                "timeline": lead_data.get("preferred_timeline", ""),
                "payment_method": lead_data.get("payment_method", ""),
            }

            # Photos and media
            photos = lead_data.get("photos", [])
            summary["media"] = {
                "total_photos": len(photos),
                "analyzed_photos": len([p for p in photos if p.get("analyzed", False)]),
                "photo_details": [
                    {
                        "id": photo.get("id"),
                        "filename": photo.get("filename"),
                        "description": photo.get("description", ""),
                        "analysis": photo.get("analysis", {}),
                        "analyzed": photo.get("analyzed", False),
                        "upload_date": photo.get("upload_date"),
                    }
                    for photo in photos
                ],
            }

            # Customer responses and interactions
            responses = lead_data.get("responses", {})
            summary["interactions"] = {
                "total_responses": len(responses),
                "response_details": responses,
                "chatbot_sessions": lead_data.get("chatbot_sessions", []),
                "follow_up_required": lead_data.get("follow_up_required", False),
            }

            # Lead qualification details
            summary["qualification"] = {
                "score": lead_data.get("qualification_score", 0),
                "factors": lead_data.get("qualification_factors", {}),
                "verified_contact": lead_data.get("contact_verified", False),
                "budget_confirmed": lead_data.get("budget_confirmed", False),
                "location_verified": lead_data.get("location_verified", False),
                "requirements_complete": lead_data.get("requirements_complete", False),
            }

            # Additional metadata
            summary["metadata"] = {
                "source": lead_data.get("source", "website"),
                "referral_code": lead_data.get("referral_code", ""),
                "campaign_id": lead_data.get("campaign_id", ""),
                "device_type": lead_data.get("device_type", ""),
                "session_duration": lead_data.get("session_duration", 0),
                "pages_visited": lead_data.get("pages_visited", []),
            }

            self.logger.info(
                f"Formatted lead summary for lead {lead_data.get('lead_id')}"
            )
            return summary

        except Exception as e:
            self.logger.error(f"Error formatting lead summary: {str(e)}")
            raise

    def log_notification(self, notification_data: Dict) -> str:
        """
        Records all notifications with timestamps in database.

        Args:
            notification_data: Dictionary containing notification details

        Returns:
            Notification log ID
        """
        try:
            log_entry = {
                "notification_id": f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{notification_data.get('lead_id', 'unknown')}",
                "lead_id": notification_data.get("lead_id"),
                "type": notification_data.get("type"),
                "recipient": notification_data.get("recipient"),
                "subject": notification_data.get("subject", ""),
                "status": "pending",
                "created_at": datetime.now(),
                "metadata": {
                    "contractor_id": notification_data.get("contractor_id"),
                    "qualified": notification_data.get("qualified", False),
                    "body_length": len(notification_data.get("body", "")),
                    "attachments": notification_data.get("attachments", []),
                },
            }

            # Store in database
            notification_id = self.db_manager.create_notification_log(log_entry)

            self.logger.info(
                f"Logged notification {notification_id} for lead {notification_data.get('lead_id')}"
            )
            return notification_id

        except Exception as e:
            self.logger.error(f"Error logging notification: {str(e)}")
            raise

    def update_lead_status(
        self, lead_id: str, new_status: str = "completed", contractor_id: str = None
    ) -> bool:
        """
        Changes lead status and records the transition.

        Args:
            lead_id: The unique identifier for the lead
            new_status: New status to set (default: 'completed')
            contractor_id: ID of assigned contractor (if applicable)

        Returns:
            True if update was successful
        """
        try:
            current_lead = self.db_manager.get_lead_by_id(lead_id)
            if not current_lead:
                raise ValueError(f"Lead {lead_id} not found")

            old_status = current_lead.get("status", "unknown")

            # Prepare update data
            update_data = {
                "status": new_status,
                "status_updated_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            if contractor_id:
                update_data["assigned_contractor_id"] = contractor_id
                update_data["assignment_date"] = datetime.now()

            if new_status == "completed":
                update_data["completed_at"] = datetime.now()
                update_data["completion_method"] = "contractor_handoff"

            # Update lead status
            success = self.db_manager.update_lead_status(lead_id, update_data)

            if success:
                # Log status change
                status_log = {
                    "lead_id": lead_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "changed_by": "notification_manager",
                    "changed_at": datetime.now(),
                    "contractor_id": contractor_id,
                    "notes": f"Status updated via notification manager - handoff to contractor",
                }

                self.db_manager.log_status_change(status_log)
                self.logger.info(
                    f"Updated lead {lead_id} status from '{old_status}' to '{new_status}'"
                )
                return True
            else:
                self.logger.error(f"Failed to update lead {lead_id} status")
                return False

        except Exception as e:
            self.logger.error(f"Error updating lead status for {lead_id}: {str(e)}")
            return False

    def send_notification(
        self, notification_data: Dict, attachments: List[str] = None
    ) -> bool:
        """
        Sends the actual email notification via SMTP.

        Args:
            notification_data: Dictionary containing email details
            attachments: List of file paths to attach (optional)

        Returns:
            True if email was sent successfully
        """
        try:
            msg = MimeMultipart()
            msg["From"] = self.company_email
            msg["To"] = notification_data["recipient"]
            msg["Subject"] = notification_data["subject"]

            # Attach body
            msg.attach(MimeText(notification_data["body"], "plain"))

            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MimeBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename= {os.path.basename(file_path)}",
                            )
                            msg.attach(part)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)

            text = msg.as_string()
            server.sendmail(self.company_email, notification_data["recipient"], text)
            server.quit()

            # Update notification status
            self.db_manager.update_notification_status(
                notification_data.get("notification_id"), "sent"
            )

            self.logger.info(
                f"Successfully sent notification to {notification_data['recipient']}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            # Update notification status to failed
            if notification_data.get("notification_id"):
                self.db_manager.update_notification_status(
                    notification_data["notification_id"], "failed", str(e)
                )
            return False

    def process_lead_handoff(
        self, lead_id: str, contractor_info: Dict
    ) -> Dict[str, any]:
        """
        Complete process for handling lead handoff to contractor.

        Args:
            lead_id: The unique identifier for the lead
            contractor_info: Dictionary containing contractor information

        Returns:
            Dictionary containing handoff results and status
        """
        try:
            # Check if lead is qualified
            is_qualified, missing_requirements = self.detect_qualified_lead(lead_id)
            if not is_qualified:
                return {
                    "success": False,
                    "error": "Lead not qualified for handoff",
                    "missing_requirements": missing_requirements,
                }

            # Generate contractor notification
            contractor_email_data = self.generate_contractor_notification_email(
                lead_id, contractor_info["email"]
            )

            # Log contractor notification
            contractor_notification_id = self.log_notification(contractor_email_data)
            contractor_email_data["notification_id"] = contractor_notification_id

            # Generate customer handoff message
            customer_message_data = self.generate_customer_handoff_message(
                lead_id, contractor_info
            )

            # Log customer notification
            customer_notification_id = self.log_notification(customer_message_data)
            customer_message_data["notification_id"] = customer_notification_id

            # Send notifications
            contractor_sent = self.send_notification(contractor_email_data)
            customer_sent = self.send_notification(customer_message_data)

            # Update lead status if both notifications sent successfully
            status_updated = False
            if contractor_sent and customer_sent:
                status_updated = self.update_lead_status(
                    lead_id, "completed", contractor_info.get("id")
                )

            return {
                "success": contractor_sent and customer_sent and status_updated,
                "lead_id": lead_id,
                "contractor_notification_sent": contractor_sent,
                "customer_notification_sent": customer_sent,
                "status_updated": status_updated,
                "contractor_notification_id": contractor_notification_id,
                "customer_notification_id": customer_notification_id,
                "contractor_info": contractor_info,
                "processed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error processing lead handoff for {lead_id}: {str(e)}")
            return {"success": False, "error": str(e), "lead_id": lead_id}

    # Private helper methods

    def _is_valid_email(self, email: str) -> bool:
        """Validates email format."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _format_budget_range(self, budget_range: str) -> str:
        """Formats budget range for display."""
        budget_mappings = {
            "under_500": "Under $500",
            "500_1000": "$500 - $1,000",
            "1000_2500": "$1,000 - $2,500",
            "2500_5000": "$2,500 - $5,000",
            "5000_10000": "$5,000 - $10,000",
            "over_10000": "Over $10,000",
            "not_specified": "To be discussed",
        }
        return budget_mappings.get(budget_range, budget_range)

    def _create_contractor_email_body(
        self, lead_data: Dict, lead_summary: Dict, is_qualified: bool
    ) -> str:
        """Creates formatted contractor email body."""

        qualification_status = (
            "✅ QUALIFIED LEAD" if is_qualified else "⚠️ NEEDS REVIEW"
        )

        body = f"""
{qualification_status}

Dear Contractor,

You have received a new lead through {self.company_name}. Please review the details below and contact the customer as soon as possible.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEAD SUMMARY - #{lead_data.get('lead_id')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CUSTOMER INFORMATION:
• Name: {lead_data.get('customer_name', 'Not provided')}
• Email: {lead_data.get('customer_email', 'Not provided')}
• Phone: {lead_data.get('customer_phone', 'Not provided')}
• Preferred Contact: {lead_data.get('preferred_contact_method', 'Phone')}

PROJECT DETAILS:
• Service Type: {lead_data.get('problem_type', 'Not specified')}
• Location: {lead_data.get('location', 'Not provided')}
• Urgency: {lead_data.get('urgency', 'Normal').title()}
• Property Type: {lead_data.get('property_type', 'Not specified')}

PROBLEM DESCRIPTION:
{lead_data.get('problem_description', 'No description provided')}

BUDGET INFORMATION:
• Budget Range: {self._format_budget_range(lead_data.get('budget_range', 'not_specified'))}
• Timeline: {lead_data.get('preferred_timeline', 'Not specified')}
• Budget Flexibility: {lead_data.get('budget_flexibility', 'Not specified')}

PHOTOS & DOCUMENTATION:
• Total Photos: {len(lead_data.get('photos', []))}
• Analyzed Photos: {len([p for p in lead_data.get('photos', []) if p.get('analyzed', False)])}
"""

        # Add photo details if available
        photos = lead_data.get("photos", [])
        if photos:
            body += "\n• Photo Details:\n"
            for i, photo in enumerate(photos, 1):
                body += f"  {i}. {photo.get('filename', f'Photo_{i}')}"
                if photo.get("description"):
                    body += f" - {photo['description']}"
                if photo.get("analysis"):
                    body += (
                        f" (Analysis: {photo['analysis'].get('summary', 'Available')})"
                    )
                body += "\n"

        body += f"""
QUALIFICATION SCORE: {lead_data.get('qualification_score', 0)}%

CUSTOMER RESPONSES:
"""

        # Add customer responses
        responses = lead_data.get("responses", {})
        if responses:
            for question, answer in responses.items():
                body += f"• {question}: {answer}\n"
        else:
            body += "• No additional responses recorded\n"

        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Contact the customer within 24 hours using their preferred method
2. Review any attached photos before the call
3. Provide a professional assessment and estimate
4. Schedule service if the customer agrees to proceed
5. Update lead status in your contractor portal

IMPORTANT REMINDERS:
• This lead has been pre-qualified by our system
• Customer is expecting your contact
• Provide professional, courteous service
• Submit your quote through our contractor portal
• Contact us at {self.company_email} if you have questions

Lead Generated: {lead_data.get('created_at', 'Unknown')}
Lead ID: #{lead_data.get('lead_id')}

Best regards,
The {self.company_name} Team
{self.company_email}

---
This is an automated lead notification. Please do not reply to this email.
For support, contact: {self.company_email}
"""

        return body
