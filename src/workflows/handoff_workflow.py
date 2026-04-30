import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from src.core.exceptions import (
    WorkflowError,
    QualificationError,
    NotificationError,
    DatabaseError,
    ValidationError,
)
from src.services.qualification_service import QualificationService
from src.services.notification_service import NotificationService
from src.services.lead_service import LeadService
from src.models.lead import Lead, LeadStatus
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class HandoffResult:
    """Result object for handoff workflow execution."""

    success: bool
    lead_id: str
    previous_status: Optional[LeadStatus] = None
    qualification_detected: bool = False
    contractor_notified: bool = False
    customer_notified: bool = False
    status_updated: bool = False
    notifications_logged: bool = False
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class HandoffWorkflow:
    """Orchestrates the complete handoff workflow for qualified leads."""

    def __init__(
        self,
        qualification_service: QualificationService,
        notification_service: NotificationService,
        lead_service: LeadService,
    ):
        """Initialize the handoff workflow with required services."""
        self.qualification_service = qualification_service
        self.notification_service = notification_service
        self.lead_service = lead_service
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def execute_complete_handoff(self, lead_id: str) -> HandoffResult:
        """
        Execute complete handoff workflow for a lead.

        Args:
            lead_id: The ID of the lead to process

        Returns:
            HandoffResult: Complete result of the handoff workflow

        Raises:
            WorkflowError: If the workflow fails at any step
            ValidationError: If lead_id is invalid
        """
        start_time = datetime.utcnow()
        result = HandoffResult(success=False, lead_id=lead_id)

        try:
            self._validate_lead_id(lead_id)

            self.logger.info(f"Starting handoff workflow for lead {lead_id}")

            # Step 1: Get and validate lead
            lead = self._get_and_validate_lead(lead_id, result)
            if not lead:
                return result

            result.previous_status = lead.status

            # Step 2: Detect qualification
            if not self._detect_qualification(lead, result):
                return result

            # Step 3: Send contractor notification
            if not self._send_contractor_notification(lead, result):
                return result

            # Step 4: Send customer handoff message
            if not self._send_customer_handoff_message(lead, result):
                return result

            # Step 5: Update lead status
            if not self._update_lead_status(lead, result):
                return result

            # Step 6: Log notifications
            if not self._log_notifications(lead, result):
                return result

            # Workflow completed successfully
            result.success = True
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time

            self.logger.info(
                f"Handoff workflow completed successfully for lead {lead_id} "
                f"in {execution_time:.2f} seconds"
            )

            return result

        except Exception as e:
            self.logger.error(f"Handoff workflow failed for lead {lead_id}: {str(e)}")
            result.error_message = str(e)

            # Attempt rollback
            self._rollback_changes(lead_id, result)

            if isinstance(e, (WorkflowError, ValidationError)):
                raise
            else:
                raise WorkflowError(f"Handoff workflow failed: {str(e)}") from e

    def _validate_lead_id(self, lead_id: str) -> None:
        """Validate the lead ID format and presence."""
        if not lead_id:
            raise ValidationError("Lead ID cannot be empty")

        if not isinstance(lead_id, str):
            raise ValidationError("Lead ID must be a string")

        if len(lead_id.strip()) == 0:
            raise ValidationError("Lead ID cannot be whitespace only")

    def _get_and_validate_lead(
        self, lead_id: str, result: HandoffResult
    ) -> Optional[Lead]:
        """Get lead from database and validate it's eligible for handoff."""
        try:
            self.logger.debug(f"Retrieving lead {lead_id}")
            lead = self.lead_service.get_lead_by_id(lead_id)

            if not lead:
                error_msg = f"Lead {lead_id} not found"
                self.logger.error(error_msg)
                result.error_message = error_msg
                return None

            # Validate lead is in correct state for handoff
            if lead.status == LeadStatus.COMPLETED:
                error_msg = f"Lead {lead_id} is already completed"
                self.logger.warning(error_msg)
                result.error_message = error_msg
                return None

            if lead.status == LeadStatus.CANCELLED:
                error_msg = f"Lead {lead_id} is cancelled and cannot be handed off"
                self.logger.warning(error_msg)
                result.error_message = error_msg
                return None

            self.logger.debug(
                f"Lead {lead_id} retrieved successfully, status: {lead.status}"
            )
            return lead

        except DatabaseError as e:
            error_msg = f"Database error retrieving lead {lead_id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            raise WorkflowError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error retrieving lead {lead_id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            raise WorkflowError(error_msg) from e

    def _detect_qualification(self, lead: Lead, result: HandoffResult) -> bool:
        """Detect if lead is qualified for handoff."""
        try:
            self.logger.debug(f"Checking qualification for lead {lead.id}")

            is_qualified = self.qualification_service.is_lead_qualified(lead)
            result.qualification_detected = is_qualified

            if not is_qualified:
                error_msg = f"Lead {lead.id} is not qualified for handoff"
                self.logger.warning(error_msg)
                result.error_message = error_msg
                return False

            self.logger.info(f"Lead {lead.id} qualification confirmed")
            return True

        except QualificationError as e:
            error_msg = f"Qualification check failed for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False
        except Exception as e:
            error_msg = f"Unexpected error during qualification check for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False

    def _send_contractor_notification(self, lead: Lead, result: HandoffResult) -> bool:
        """Send notification to contractor about the qualified lead."""
        try:
            self.logger.debug(f"Sending contractor notification for lead {lead.id}")

            notification_data = {
                "lead_id": lead.id,
                "customer_name": lead.customer_name,
                "customer_phone": lead.customer_phone,
                "customer_email": lead.customer_email,
                "service_type": lead.service_type,
                "location": lead.location,
                "urgency": lead.urgency,
                "estimated_value": lead.estimated_value,
                "qualification_score": getattr(lead, "qualification_score", None),
                "notes": lead.notes,
            }

            success = self.notification_service.send_contractor_notification(
                lead.assigned_contractor_id, "qualified_lead_handoff", notification_data
            )

            result.contractor_notified = success

            if not success:
                error_msg = f"Failed to send contractor notification for lead {lead.id}"
                self.logger.error(error_msg)
                result.error_message = error_msg
                return False

            self.logger.info(
                f"Contractor notification sent successfully for lead {lead.id}"
            )
            return True

        except NotificationError as e:
            error_msg = f"Contractor notification failed for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False
        except Exception as e:
            error_msg = f"Unexpected error sending contractor notification for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False

    def _send_customer_handoff_message(self, lead: Lead, result: HandoffResult) -> bool:
        """Send handoff confirmation message to customer."""
        try:
            self.logger.debug(f"Sending customer handoff message for lead {lead.id}")

            contractor_info = self._get_contractor_info(lead.assigned_contractor_id)
            if not contractor_info:
                error_msg = f"Could not retrieve contractor info for lead {lead.id}"
                self.logger.error(error_msg)
                result.error_message = error_msg
                return False

            message_data = {
                "customer_name": lead.customer_name,
                "contractor_name": contractor_info.get("name"),
                "contractor_phone": contractor_info.get("phone"),
                "contractor_email": contractor_info.get("email"),
                "service_type": lead.service_type,
                "estimated_response_time": contractor_info.get(
                    "response_time", "24 hours"
                ),
            }

            # Send via preferred communication method
            success = False
            if lead.preferred_contact_method == "email" and lead.customer_email:
                success = self.notification_service.send_customer_email(
                    lead.customer_email, "handoff_confirmation", message_data
                )
            elif lead.preferred_contact_method == "sms" and lead.customer_phone:
                success = self.notification_service.send_customer_sms(
                    lead.customer_phone, "handoff_confirmation", message_data
                )
            else:
                # Fallback to email if available, otherwise SMS
                if lead.customer_email:
                    success = self.notification_service.send_customer_email(
                        lead.customer_email, "handoff_confirmation", message_data
                    )
                elif lead.customer_phone:
                    success = self.notification_service.send_customer_sms(
                        lead.customer_phone, "handoff_confirmation", message_data
                    )

            result.customer_notified = success

            if not success:
                error_msg = (
                    f"Failed to send customer handoff message for lead {lead.id}"
                )
                self.logger.error(error_msg)
                result.error_message = error_msg
                return False

            self.logger.info(
                f"Customer handoff message sent successfully for lead {lead.id}"
            )
            return True

        except NotificationError as e:
            error_msg = f"Customer handoff message failed for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False
        except Exception as e:
            error_msg = f"Unexpected error sending customer handoff message for lead {lead.id}: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False

    def _update_lead_status(self, lead: Lead, result: HandoffResult) -> bool:
        """Update lead status to completed."""
        try:
            self.logger.debug(f"Updating lead {lead.id} status to completed")

            update_data = {
                "status": LeadStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "handoff_completed_by": "system",  # Could be parameterized
                "last_modified": datetime.utcnow(),
            }

            success = self.lead_service.update_lead_status(lead.id, update_data)
            result.status_updated = success

            if not success:
                error_msg = f"Failed to update lead {lead.id} status to completed"
                self.logger.error(error_msg)
                result.error_message = error_msg
                return False

            self.logger.info(f"Lead {lead.id} status updated to completed")
            return True

        except DatabaseError as e:
            error_msg = f"Database error updating lead {lead.id} status: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False
        except Exception as e:
            error_msg = f"Unexpected error updating lead {lead.id} status: {str(e)}"
            self.logger.error(error_msg)
            result.error_message = error_msg
            return False

    def _log_notifications(self, lead: Lead, result: HandoffResult) -> bool:
        """Log all notifications sent during the handoff process."""
        try:
            self.logger.debug(f"Logging notifications for lead {lead.id}")

            notification_log_data = {
                "lead_id": lead.id,
                "workflow_type": "handoff",
                "contractor_notified": result.contractor_notified,
                "customer_notified": result.customer_notified,
                "contractor_id": lead.assigned_contractor_id,
                "customer_contact_method": lead.preferred_contact_method,
                "timestamp": datetime.utcnow(),
                "status": "completed",
            }

            success = self.notification_service.log_workflow_notifications(
                notification_log_data
            )
            result.notifications_logged = success

            if not success:
                error_msg = f"Failed to log notifications for lead {lead.id}"
                self.logger.warning(error_msg)  # Warning since this is not critical
                # Don't return False as this shouldn't fail the entire workflow

            self.logger.info(f"Notifications logged successfully for lead {lead.id}")
            return True

        except Exception as e:
            error_msg = f"Error logging notifications for lead {lead.id}: {str(e)}"
            self.logger.warning(error_msg)  # Warning since this is not critical
            # Don't fail the workflow due to logging issues
            return True

    def _get_contractor_info(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """Get contractor information for handoff message."""
        try:
            if not contractor_id:
                return None

            # This would typically call a contractor service
            contractor_info = self.lead_service.get_contractor_info(contractor_id)
            return contractor_info

        except Exception as e:
            self.logger.error(
                f"Error retrieving contractor info for {contractor_id}: {str(e)}"
            )
            return None

    def _rollback_changes(self, lead_id: str, result: HandoffResult) -> None:
        """Attempt to rollback any changes made during failed workflow execution."""
        self.logger.info(f"Attempting rollback for lead {lead_id}")

        try:
            # Rollback status update if it was successful
            if result.status_updated and result.previous_status:
                self.logger.debug(f"Rolling back status for lead {lead_id}")
                rollback_data = {
                    "status": result.previous_status,
                    "completed_at": None,
                    "handoff_completed_by": None,
                    "last_modified": datetime.utcnow(),
                }

                rollback_success = self.lead_service.update_lead_status(
                    lead_id, rollback_data
                )
                if rollback_success:
                    self.logger.info(f"Status rollback successful for lead {lead_id}")
                else:
                    self.logger.error(f"Status rollback failed for lead {lead_id}")

            # Log the rollback attempt
            if result.notifications_logged:
                rollback_log_data = {
                    "lead_id": lead_id,
                    "workflow_type": "handoff_rollback",
                    "rollback_reason": result.error_message,
                    "timestamp": datetime.utcnow(),
                    "status": "rolled_back",
                }

                self.notification_service.log_workflow_notifications(rollback_log_data)

        except Exception as e:
            self.logger.error(f"Rollback failed for lead {lead_id}: {str(e)}")
