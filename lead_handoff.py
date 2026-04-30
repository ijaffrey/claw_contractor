import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json

from database import DatabaseManager
from email_sender import EmailSender
from notification_manager import NotificationManager


class LeadStatus(Enum):
    """Lead status enumeration."""

    NEW = "new"
    QUALIFIED = "qualified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class NotificationType(Enum):
    """Notification type enumeration."""

    CONTRACTOR_NOTIFICATION = "contractor_notification"
    CUSTOMER_HANDOFF = "customer_handoff"
    STATUS_UPDATE = "status_update"
    LEAD_QUALIFIED = "lead_qualified"


@dataclass
class LeadData:
    """Data structure for lead information."""

    lead_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    service_type: str
    location: str
    description: str
    budget: Optional[float]
    urgency: str
    created_at: datetime
    status: str
    qualification_score: Optional[float] = None
    contact_preference: str = "email"
    availability: Optional[str] = None


@dataclass
class ContractorInfo:
    """Data structure for contractor information."""

    contractor_id: str
    name: str
    email: str
    phone: str
    specialties: List[str]
    service_areas: List[str]
    rating: float
    availability_status: str
    notification_preferences: Dict[str, Any]


class LeadHandoffManager:
    """Comprehensive lead handoff management system."""

    def __init__(self):
        """Initialize the lead handoff manager."""
        self.db = DatabaseManager()
        self.email_sender = EmailSender()
        self.notification_manager = NotificationManager()
        self.logger = logging.getLogger(__name__)

        # Qualification criteria thresholds
        self.qualification_thresholds = {
            "min_score": 70.0,
            "required_fields": [
                "customer_name",
                "customer_email",
                "service_type",
                "location",
            ],
            "budget_threshold": 500.0,
            "urgency_weights": {"urgent": 30, "high": 20, "medium": 10, "low": 5},
        }

    def detect_qualified_lead(
        self, lead_data: Dict[str, Any]
    ) -> Tuple[bool, float, List[str]]:
        """
        Detect if a lead is qualified based on comprehensive criteria.

        Args:
            lead_data: Dictionary containing lead information

        Returns:
            Tuple of (is_qualified, qualification_score, qualification_reasons)
        """
        try:
            score = 0.0
            reasons = []
            max_score = 100.0

            # Check required fields (30 points)
            required_fields = self.qualification_thresholds["required_fields"]
            missing_fields = [
                field for field in required_fields if not lead_data.get(field)
            ]

            if not missing_fields:
                score += 30
                reasons.append("All required fields provided")
            else:
                penalty = len(missing_fields) * 7.5
                score += max(0, 30 - penalty)
                reasons.append(f"Missing required fields: {', '.join(missing_fields)}")

            # Budget assessment (25 points)
            budget = lead_data.get("budget", 0)
            if budget and budget >= self.qualification_thresholds["budget_threshold"]:
                score += 25
                reasons.append(f"Budget meets threshold: ${budget:,.2f}")
            elif budget:
                # Partial points for lower budgets
                ratio = budget / self.qualification_thresholds["budget_threshold"]
                partial_score = 25 * min(ratio, 1.0)
                score += partial_score
                reasons.append(f"Budget below threshold but acceptable: ${budget:,.2f}")
            else:
                reasons.append("No budget information provided")

            # Urgency assessment (20 points)
            urgency = lead_data.get("urgency", "low").lower()
            urgency_score = self.qualification_thresholds["urgency_weights"].get(
                urgency, 5
            )
            score += urgency_score
            reasons.append(f"Urgency level: {urgency} ({urgency_score} points)")

            # Service type specificity (10 points)
            service_type = lead_data.get("service_type", "")
            if service_type and len(service_type.strip()) > 10:
                score += 10
                reasons.append("Detailed service type provided")
            elif service_type:
                score += 5
                reasons.append("Basic service type provided")
            else:
                reasons.append("No service type specified")

            # Description quality (10 points)
            description = lead_data.get("description", "")
            if description and len(description.strip()) > 50:
                score += 10
                reasons.append("Detailed description provided")
            elif description and len(description.strip()) > 20:
                score += 5
                reasons.append("Basic description provided")
            else:
                reasons.append("Insufficient description")

            # Contact information quality (5 points)
            has_phone = bool(lead_data.get("customer_phone"))
            has_email = bool(lead_data.get("customer_email"))

            if has_phone and has_email:
                score += 5
                reasons.append("Multiple contact methods available")
            elif has_phone or has_email:
                score += 3
                reasons.append("Single contact method available")

            # Normalize score to percentage
            final_score = (score / max_score) * 100
            is_qualified = final_score >= self.qualification_thresholds["min_score"]

            self.logger.info(
                f"Lead {lead_data.get('lead_id', 'unknown')} qualification: "
                f"Score={final_score:.1f}%, Qualified={is_qualified}"
            )

            return is_qualified, final_score, reasons

        except Exception as e:
            self.logger.error(f"Error in lead qualification detection: {str(e)}")
            return False, 0.0, [f"Error during qualification: {str(e)}"]

    def send_contractor_notification(
        self, lead_data: Dict[str, Any], contractor_info: Dict[str, Any]
    ) -> bool:
        """
        Send notification to contractor about new qualified lead.

        Args:
            lead_data: Lead information
            contractor_info: Contractor information

        Returns:
            Success status
        """
        try:
            lead_obj = self._dict_to_lead_data(lead_data)
            contractor_obj = self._dict_to_contractor_info(contractor_info)

            # Prepare email content
            subject = (
                f"New Qualified Lead: {lead_obj.service_type} in {lead_obj.location}"
            )

            email_body = self._generate_contractor_email_body(lead_obj, contractor_obj)

            # Send email notification
            email_success = self.email_sender.send_email(
                to_email=contractor_obj.email,
                subject=subject,
                body=email_body,
                is_html=True,
            )

            # Send additional notifications based on preferences
            notification_success = True
            if contractor_obj.notification_preferences.get("sms_enabled", False):
                sms_message = self._generate_contractor_sms(lead_obj)
                notification_success = self.notification_manager.send_sms(
                    phone_number=contractor_obj.phone, message=sms_message
                )

            # Log notification attempt
            status = "success" if (email_success and notification_success) else "failed"
            self.log_notification(
                notification_type=NotificationType.CONTRACTOR_NOTIFICATION.value,
                lead_id=lead_obj.lead_id,
                status=status,
            )

            # Update database with notification record
            self.db.execute_query(
                """
                INSERT INTO contractor_notifications 
                (lead_id, contractor_id, notification_type, sent_at, status, email_sent, sms_sent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    lead_obj.lead_id,
                    contractor_obj.contractor_id,
                    "lead_assignment",
                    datetime.now(timezone.utc),
                    status,
                    email_success,
                    notification_success,
                ),
            )

            self.logger.info(
                f"Contractor notification sent to {contractor_obj.name} "
                f"for lead {lead_obj.lead_id}: {status}"
            )

            return email_success and notification_success

        except Exception as e:
            self.logger.error(f"Error sending contractor notification: {str(e)}")
            self.log_notification(
                notification_type=NotificationType.CONTRACTOR_NOTIFICATION.value,
                lead_id=lead_data.get("lead_id", "unknown"),
                status="error",
            )
            return False

    def format_lead_summary(self, lead_data: Dict[str, Any]) -> str:
        """
        Format lead information into a comprehensive summary.

        Args:
            lead_data: Lead information dictionary

        Returns:
            Formatted lead summary string
        """
        try:
            lead_obj = self._dict_to_lead_data(lead_data)

            summary_parts = [
                f"Lead ID: {lead_obj.lead_id}",
                f"Customer: {lead_obj.customer_name}",
                f"Service: {lead_obj.service_type}",
                f"Location: {lead_obj.location}",
                f"Status: {lead_obj.status.upper()}",
                f"Created: {lead_obj.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            ]

            if lead_obj.budget:
                summary_parts.append(f"Budget: ${lead_obj.budget:,.2f}")

            if lead_obj.urgency:
                summary_parts.append(f"Urgency: {lead_obj.urgency.upper()}")

            if lead_obj.qualification_score:
                summary_parts.append(
                    f"Qualification Score: {lead_obj.qualification_score:.1f}%"
                )

            # Contact information
            contact_info = []
            if lead_obj.customer_email:
                contact_info.append(f"Email: {lead_obj.customer_email}")
            if lead_obj.customer_phone:
                contact_info.append(f"Phone: {lead_obj.customer_phone}")

            if contact_info:
                summary_parts.append("Contact: " + " | ".join(contact_info))

            if lead_obj.description and lead_obj.description.strip():
                # Truncate long descriptions
                description = lead_obj.description.strip()
                if len(description) > 200:
                    description = description[:200] + "..."
                summary_parts.append(f"Description: {description}")

            if lead_obj.availability:
                summary_parts.append(f"Availability: {lead_obj.availability}")

            return "\n".join(summary_parts)

        except Exception as e:
            self.logger.error(f"Error formatting lead summary: {str(e)}")
            return f"Error formatting lead summary for ID: {lead_data.get('lead_id', 'unknown')}"

    def send_customer_handoff_message(self, lead_data: Dict[str, Any]) -> bool:
        """
        Send handoff message to customer confirming lead processing.

        Args:
            lead_data: Lead information dictionary

        Returns:
            Success status
        """
        try:
            lead_obj = self._dict_to_lead_data(lead_data)

            # Prepare customer notification
            subject = f"Your Service Request Received - {lead_obj.service_type}"

            email_body = self._generate_customer_handoff_email(lead_obj)

            # Send email notification
            success = self.email_sender.send_email(
                to_email=lead_obj.customer_email,
                subject=subject,
                body=email_body,
                is_html=True,
            )

            # Log notification
            status = "success" if success else "failed"
            self.log_notification(
                notification_type=NotificationType.CUSTOMER_HANDOFF.value,
                lead_id=lead_obj.lead_id,
                status=status,
            )

            # Update database with customer notification record
            self.db.execute_query(
                """
                INSERT INTO customer_notifications 
                (lead_id, notification_type, sent_at, status, email_sent)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (
                    lead_obj.lead_id,
                    "handoff_confirmation",
                    datetime.now(timezone.utc),
                    status,
                    success,
                ),
            )

            self.logger.info(
                f"Customer handoff message sent to {lead_obj.customer_email} "
                f"for lead {lead_obj.lead_id}: {status}"
            )

            return success

        except Exception as e:
            self.logger.error(f"Error sending customer handoff message: {str(e)}")
            self.log_notification(
                notification_type=NotificationType.CUSTOMER_HANDOFF.value,
                lead_id=lead_data.get("lead_id", "unknown"),
                status="error",
            )
            return False

    def update_lead_status_to_completed(self, lead_id: str) -> bool:
        """
        Update lead status to completed and perform cleanup tasks.

        Args:
            lead_id: Lead identifier

        Returns:
            Success status
        """
        try:
            # Update lead status
            rows_affected = self.db.execute_query(
                """
                UPDATE leads 
                SET status = %s, completed_at = %s, updated_at = %s
                WHERE lead_id = %s AND status != %s
            """,
                (
                    LeadStatus.COMPLETED.value,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    lead_id,
                    LeadStatus.COMPLETED.value,
                ),
            )

            if rows_affected == 0:
                self.logger.warning(
                    f"No lead found with ID {lead_id} or already completed"
                )
                return False

            # Log status update
            self.log_notification(
                notification_type=NotificationType.STATUS_UPDATE.value,
                lead_id=lead_id,
                status="completed",
            )

            # Update lead analytics
            self.db.execute_query(
                """
                INSERT INTO lead_analytics 
                (lead_id, event_type, event_timestamp, event_data)
                VALUES (%s, %s, %s, %s)
            """,
                (
                    lead_id,
                    "status_change",
                    datetime.now(timezone.utc),
                    json.dumps(
                        {"old_status": "in_progress", "new_status": "completed"}
                    ),
                ),
            )

            self.logger.info(f"Lead {lead_id} status updated to completed")
            return True

        except Exception as e:
            self.logger.error(f"Error updating lead status to completed: {str(e)}")
            return False

    def log_notification(
        self, notification_type: str, lead_id: str, status: str
    ) -> None:
        """
        Log notification events for tracking and analytics.

        Args:
            notification_type: Type of notification sent
            lead_id: Associated lead identifier
            status: Status of the notification (success/failed/error)
        """
        try:
            log_data = {
                "notification_type": notification_type,
                "lead_id": lead_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "module": "lead_handoff",
            }

            # Insert into notification logs table
            self.db.execute_query(
                """
                INSERT INTO notification_logs 
                (lead_id, notification_type, status, timestamp, log_data)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (
                    lead_id,
                    notification_type,
                    status,
                    datetime.now(timezone.utc),
                    json.dumps(log_data),
                ),
            )

            # Log to application logger
            log_message = f"Notification logged - Type: {notification_type}, Lead: {lead_id}, Status: {status}"

            if status == "success":
                self.logger.info(log_message)
            elif status == "failed":
                self.logger.warning(log_message)
            else:
                self.logger.error(log_message)

        except Exception as e:
            self.logger.error(f"Error logging notification: {str(e)}")

    def process_lead_handoff(
        self,
        lead_data: Dict[str, Any],
        contractor_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Complete lead handoff process including qualification, notification, and status updates.

        Args:
            lead_data: Lead information
            contractor_info: Optional contractor information for assignment

        Returns:
            Dictionary with handoff results
        """
        try:
            results = {
                "lead_id": lead_data.get("lead_id"),
                "qualified": False,
                "qualification_score": 0.0,
                "contractor_notified": False,
                "customer_notified": False,
                "status_updated": False,
                "errors": [],
            }

            # Step 1: Detect qualification
            is_qualified, score, reasons = self.detect_qualified_lead(lead_data)
            results["qualified"] = is_qualified
            results["qualification_score"] = score
            results["qualification_reasons"] = reasons

            if not is_qualified:
                results["errors"].append("Lead did not meet qualification criteria")
                return results

            # Step 2: Update lead with qualification score
            self.db.execute_query(
                """
                UPDATE leads 
                SET qualification_score = %s, status = %s, updated_at = %s
                WHERE lead_id = %s
            """,
                (
                    score,
                    LeadStatus.QUALIFIED.value,
                    datetime.now(timezone.utc),
                    lead_data["lead_id"],
                ),
            )

            # Step 3: Send customer handoff message
            customer_success = self.send_customer_handoff_message(lead_data)
            results["customer_notified"] = customer_success

            if not customer_success:
                results["errors"].append("Failed to send customer handoff message")

            # Step 4: Send contractor notification if contractor provided
            if contractor_info:
                contractor_success = self.send_contractor_notification(
                    lead_data, contractor_info
                )
                results["contractor_notified"] = contractor_success

                if not contractor_success:
                    results["errors"].append("Failed to send contractor notification")
                else:
                    # Update lead status to assigned
                    self.db.execute_query(
                        """
                        UPDATE leads 
                        SET status = %s, assigned_contractor_id = %s, assigned_at = %s
                        WHERE lead_id = %s
                    """,
                        (
                            LeadStatus.ASSIGNED.value,
                            contractor_info["contractor_id"],
                            datetime.now(timezone.utc),
                            lead_data["lead_id"],
                        ),
                    )
                    results["status_updated"] = True

            self.logger.info(
                f"Lead handoff completed for {lead_data['lead_id']}: {results}"
            )
            return results

        except Exception as e:
            self.logger.error(f"Error in complete lead handoff process: {str(e)}")
            return {
                "lead_id": lead_data.get("lead_id"),
                "qualified": False,
                "errors": [f"Processing error: {str(e)}"],
            }

    def _dict_to_lead_data(self, data: Dict[str, Any]) -> LeadData:
        """Convert dictionary to LeadData object."""
        return LeadData(
            lead_id=data["lead_id"],
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            customer_phone=data.get("customer_phone", ""),
            service_type=data["service_type"],
            location=data["location"],
            description=data.get("description", ""),
            budget=data.get("budget"),
            urgency=data.get("urgency", "medium"),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            status=data.get("status", LeadStatus.NEW.value),
            qualification_score=data.get("qualification_score"),
            contact_preference=data.get("contact_preference", "email"),
            availability=data.get("availability"),
        )

    def _dict_to_contractor_info(self, data: Dict[str, Any]) -> ContractorInfo:
        """Convert dictionary to ContractorInfo object."""
        return ContractorInfo(
            contractor_id=data["contractor_id"],
            name=data["name"],
            email=data["email"],
            phone=data.get("phone", ""),
            specialties=data.get("specialties", []),
            service_areas=data.get("service_areas", []),
            rating=data.get("rating", 0.0),
            availability_status=data.get("availability_status", "available"),
            notification_preferences=data.get("notification_preferences", {}),
        )

    def _generate_contractor_email_body(
        self, lead: LeadData, contractor: ContractorInfo
    ) -> str:
        """Generate HTML email body for contractor notification."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .lead-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .highlight {{ color: #e74c3c; font-weight: bold; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>New Qualified Lead Assignment</h1>
            </div>
            <div class="content">
                <p>Hello {contractor.name},</p>
                <p>You have been assigned a new qualified lead that matches your expertise.</p>
                
                <div class="lead-details">
                    <h3>Lead Details</h3>
                    <p><strong>Customer:</strong> {lead.customer_name}</p>
                    <p><strong>Service Type:</strong> {lead.service_type}</p>
                    <p><strong>Location:</strong> {lead.location}</p>
                    <p><strong>Urgency:</strong> <span class="highlight">{lead.urgency.upper()}</span></p>
                    {f'<p><strong>Budget:</strong> ${lead.budget:,.2f}</p>' if lead.budget else ''}
                    <p><strong>Qualification Score:</strong> {lead.qualification_score:.1f}%</p>
                    <p><strong>Description:</strong> {lead.description}</p>
                </div>
                
                <div class="lead-details">
                    <h3>Customer Contact Information</h3>
                    <p><strong>Email:</strong> {lead.customer_email}</p>
                    {f'<p><strong>Phone:</strong> {lead.customer_phone}</p>' if lead.customer_phone else ''}
                    <p><strong>Preferred Contact:</strong> {lead.contact_preference}</p>
                    {f'<p><strong>Availability:</strong> {lead.availability}</p>' if lead.availability else ''}
                </div>
                
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Contact the customer within 2 hours for urgent requests</li>
                    <li>Provide a detailed quote within 24 hours</li>
                    <li>Update the lead status in your contractor portal</li>
                </ul>
                
                <p>Thank you for your prompt attention to this lead.</p>
            </div>
            <div class="footer">
                <p>This is an automated notification from the Lead Management System</p>
            </div>
        </body>
        </html>
        """

    def _generate_contractor_sms(self, lead: LeadData) -> str:
        """Generate SMS message for contractor notification."""
        return (
            f"New lead assigned: {lead.service_type} in {lead.location}. "
            f"Customer: {lead.customer_name}. Urgency: {lead.urgency}. "
            f"Contact: {lead.customer_email}. Lead ID: {lead.lead_id}"
        )

    def _generate_customer_handoff_email(self, lead: LeadData) -> str:
        """Generate HTML email body for customer handoff message."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .request-summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .next-steps {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ background-color: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Service Request Confirmed</h1>
            </div>
            <div class="content">
                <p>Dear {lead.customer_name},</p>
                <p>Thank you for your service request. We have received and processed your inquiry.</p>
                
                <div class="request-summary">
                    <h3>Your Request Summary</h3>
                    <p><strong>Service Type:</strong> {lead.service_type}</p>
                    <p><strong>Location:</strong> {lead.location}</p>
                    <p><strong>Request ID:</strong> {lead.lead_id}</p>
                    <p><strong>Submitted:</strong> {lead.created_at.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                    {f'<p><strong>Budget Range:</strong> ${lead.budget:,.2f}</p>' if lead.budget else ''}
                </div>
                
                <div class="next-steps">
                    <h3>What Happens Next?</h3>
                    <ol>
                        <li>We are matching you with qualified contractors in your area</li>
                        <li>Selected contractors will contact you within 24 hours</li>
                        <li>You'll receive detailed quotes for your project</li>
                        <li>Choose the contractor that best fits your needs</li>
                    </ol>
                </div>
                
                <p><strong>Important:</strong> Please keep your contact information available as contractors may reach out soon.</p>
                
                <p>If you have any questions or need to update your request, please contact our support team.</p>
                
                <p>Thank you for choosing our service!</p>
            </div>
            <div class="footer">
                <p>This confirmation was sent to {lead.customer_email}</p>
                <p>Lead Management System - Connecting customers with quality contractors</p>
            </div>
        </body>
        </html>
        """
