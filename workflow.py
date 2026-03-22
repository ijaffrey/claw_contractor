import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import json

from database import DatabaseManager, get_db_connection
from notifications import NotificationService
from messaging import MessageService
from audit import AuditLogger


class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionType(Enum):
    STATUS_UPDATE = "status_update"
    NOTIFICATION_SENT = "notification_sent"
    MESSAGE_SENT = "message_sent"
    AUDIT_LOG = "audit_log"


@dataclass
class WorkflowAction:
    action_type: ActionType
    timestamp: datetime
    details: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class WorkflowResult:
    workflow_id: str
    lead_id: str
    status: WorkflowStatus
    actions_performed: List[WorkflowAction] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    error_details: Optional[str] = None


class WorkflowError(Exception):
    """Base exception for workflow errors"""
    pass


class LeadNotFoundError(WorkflowError):
    """Raised when lead is not found"""
    pass


class InvalidLeadStatusError(WorkflowError):
    """Raised when lead status is invalid for the operation"""
    pass


class NotificationError(WorkflowError):
    """Raised when notification fails"""
    pass


class MessageError(WorkflowError):
    """Raised when message sending fails"""
    pass


class DatabaseError(WorkflowError):
    """Raised when database operation fails"""
    pass


class LeadHandoffWorkflow:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.notification_service = NotificationService()
        self.message_service = MessageService()
        self.audit_logger = AuditLogger()
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def transaction_context(self):
        """Database transaction context manager with rollback capability"""
        conn = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _validate_lead_for_completion(self, lead_data: Dict[str, Any]) -> None:
        """Validate lead can be completed"""
        if not lead_data:
            raise LeadNotFoundError("Lead not found")
        
        current_status = lead_data.get('status')
        if current_status == 'completed':
            raise InvalidLeadStatusError("Lead is already completed")
        
        if current_status not in ['qualified', 'in_progress']:
            raise InvalidLeadStatusError(
                f"Lead status '{current_status}' is not eligible for completion"
            )
        
        required_fields = ['customer_id', 'contractor_id', 'service_type']
        missing_fields = [field for field in required_fields if not lead_data.get(field)]
        if missing_fields:
            raise InvalidLeadStatusError(
                f"Lead missing required fields: {', '.join(missing_fields)}"
            )
    
    def _get_lead_details(self, lead_id: str, conn) -> Dict[str, Any]:
        """Retrieve detailed lead information"""
        try:
            query = """
                SELECT 
                    l.id, l.customer_id, l.contractor_id, l.service_type,
                    l.status, l.created_at, l.requirements, l.budget,
                    c.name as customer_name, c.email as customer_email,
                    c.phone as customer_phone, c.address as customer_address,
                    con.name as contractor_name, con.email as contractor_email,
                    con.phone as contractor_phone, con.company_name
                FROM leads l
                JOIN customers c ON l.customer_id = c.id
                JOIN contractors con ON l.contractor_id = con.id
                WHERE l.id = %s
            """
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (lead_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if not result:
                raise LeadNotFoundError(f"Lead {lead_id} not found")
            
            return result
        except Exception as e:
            self.logger.error(f"Error retrieving lead details: {str(e)}")
            raise DatabaseError(f"Failed to retrieve lead details: {str(e)}")
    
    def _update_lead_status(self, lead_id: str, status: str, conn) -> WorkflowAction:
        """Update lead status in database"""
        try:
            query = """
                UPDATE leads 
                SET status = %s, updated_at = %s, completed_at = %s
                WHERE id = %s
            """
            completed_at = datetime.utcnow() if status == 'completed' else None
            
            cursor = conn.cursor()
            cursor.execute(query, (status, datetime.utcnow(), completed_at, lead_id))
            
            if cursor.rowcount == 0:
                raise DatabaseError(f"No lead updated for ID: {lead_id}")
            
            cursor.close()
            
            return WorkflowAction(
                action_type=ActionType.STATUS_UPDATE,
                timestamp=datetime.utcnow(),
                details={
                    'lead_id': lead_id,
                    'new_status': status,
                    'completed_at': completed_at.isoformat() if completed_at else None
                }
            )
        except Exception as e:
            self.logger.error(f"Error updating lead status: {str(e)}")
            raise DatabaseError(f"Failed to update lead status: {str(e)}")
    
    def _send_contractor_notification(self, lead_data: Dict[str, Any]) -> WorkflowAction:
        """Send notification to contractor about lead completion"""
        try:
            notification_data = {
                'recipient_id': lead_data['contractor_id'],
                'recipient_email': lead_data['contractor_email'],
                'recipient_name': lead_data['contractor_name'],
                'type': 'lead_handoff',
                'subject': f"New Lead Assignment - {lead_data['service_type']}",
                'message': self._generate_contractor_message(lead_data),
                'lead_id': lead_data['id'],
                'priority': 'high'
            }
            
            notification_id = self.notification_service.send_notification(notification_data)
            
            return WorkflowAction(
                action_type=ActionType.NOTIFICATION_SENT,
                timestamp=datetime.utcnow(),
                details={
                    'notification_id': notification_id,
                    'recipient': lead_data['contractor_email'],
                    'notification_type': 'contractor_handoff'
                }
            )
        except Exception as e:
            self.logger.error(f"Error sending contractor notification: {str(e)}")
            raise NotificationError(f"Failed to send contractor notification: {str(e)}")
    
    def _send_customer_handoff_message(self, lead_data: Dict[str, Any]) -> WorkflowAction:
        """Send handoff message to customer"""
        try:
            message_data = {
                'recipient_id': lead_data['customer_id'],
                'recipient_email': lead_data['customer_email'],
                'recipient_phone': lead_data['customer_phone'],
                'recipient_name': lead_data['customer_name'],
                'type': 'customer_handoff',
                'subject': f"Your {lead_data['service_type']} Request - Next Steps",
                'message': self._generate_customer_message(lead_data),
                'lead_id': lead_data['id'],
                'preferred_channel': 'email'
            }
            
            message_id = self.message_service.send_message(message_data)
            
            return WorkflowAction(
                action_type=ActionType.MESSAGE_SENT,
                timestamp=datetime.utcnow(),
                details={
                    'message_id': message_id,
                    'recipient': lead_data['customer_email'],
                    'message_type': 'customer_handoff'
                }
            )
        except Exception as e:
            self.logger.error(f"Error sending customer message: {str(e)}")
            raise MessageError(f"Failed to send customer message: {str(e)}")
    
    def _log_workflow_actions(self, workflow_result: WorkflowResult) -> WorkflowAction:
        """Log all workflow actions to audit trail"""
        try:
            audit_data = {
                'workflow_id': workflow_result.workflow_id,
                'lead_id': workflow_result.lead_id,
                'workflow_type': 'lead_completion',
                'status': workflow_result.status.value,
                'actions_count': len(workflow_result.actions_performed),
                'start_time': workflow_result.start_time.isoformat(),
                'end_time': workflow_result.end_time.isoformat() if workflow_result.end_time else None,
                'actions_detail': [
                    {
                        'action_type': action.action_type.value,
                        'timestamp': action.timestamp.isoformat(),
                        'success': action.success,
                        'details': action.details,
                        'error': action.error_message
                    } for action in workflow_result.actions_performed
                ]
            }
            
            audit_id = self.audit_logger.log_workflow(audit_data)
            
            return WorkflowAction(
                action_type=ActionType.AUDIT_LOG,
                timestamp=datetime.utcnow(),
                details={
                    'audit_id': audit_id,
                    'actions_logged': len(workflow_result.actions_performed)
                }
            )
        except Exception as e:
            self.logger.error(f"Error logging workflow actions: {str(e)}")
            raise WorkflowError(f"Failed to log workflow actions: {str(e)}")
    
    def _generate_contractor_message(self, lead_data: Dict[str, Any]) -> str:
        """Generate notification message for contractor"""
        return f"""
Hello {lead_data['contractor_name']},

You have been assigned a new lead for {lead_data['service_type']} services.

Customer Details:
- Name: {lead_data['customer_name']}
- Email: {lead_data['customer_email']}
- Phone: {lead_data['customer_phone']}
- Address: {lead_data['customer_address']}

Project Requirements:
{lead_data.get('requirements', 'No specific requirements provided')}

Budget: {lead_data.get('budget', 'Not specified')}

Please contact the customer within 24 hours to discuss the project details and schedule a consultation.

Lead ID: {lead_data['id']}
Date Assigned: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Lead Management System
        """.strip()
    
    def _generate_customer_message(self, lead_data: Dict[str, Any]) -> str:
        """Generate handoff message for customer"""
        return f"""
Dear {lead_data['customer_name']},

Great news! We have successfully matched you with a qualified contractor for your {lead_data['service_type']} project.

Your Assigned Contractor:
- Company: {lead_data['company_name']}
- Contact: {lead_data['contractor_name']}
- Email: {lead_data['contractor_email']}
- Phone: {lead_data['contractor_phone']}

Next Steps:
1. Your contractor will contact you within 24 hours
2. They will discuss your project requirements in detail
3. A consultation will be scheduled at your convenience
4. You'll receive a detailed project proposal

Project Reference: {lead_data['id']}
Date: {datetime.utcnow().strftime('%Y-%m-%d')}

If you have any questions or concerns, please don't hesitate to contact our support team.

Thank you for choosing our platform!

Best regards,
Customer Success Team
        """.strip()
    
    def _rollback_actions(self, actions: List[WorkflowAction], lead_id: str):
        """Attempt to rollback completed actions"""
        rollback_errors = []
        
        for action in reversed(actions):
            try:
                if action.action_type == ActionType.STATUS_UPDATE:
                    # Rollback status update
                    with self.transaction_context() as conn:
                        query = "UPDATE leads SET status = 'qualified' WHERE id = %s"
                        cursor = conn.cursor()
                        cursor.execute(query, (lead_id,))
                        cursor.close()
                        
                elif action.action_type == ActionType.NOTIFICATION_SENT:
                    # Cancel notification if possible
                    notification_id = action.details.get('notification_id')
                    if notification_id:
                        self.notification_service.cancel_notification(notification_id)
                
                elif action.action_type == ActionType.MESSAGE_SENT:
                    # Log message cancellation attempt
                    message_id = action.details.get('message_id')
                    if message_id:
                        self.message_service.mark_message_cancelled(message_id)
                
            except Exception as e:
                rollback_errors.append(f"Failed to rollback {action.action_type.value}: {str(e)}")
                self.logger.error(f"Rollback error for {action.action_type.value}: {str(e)}")
        
        if rollback_errors:
            self.logger.error(f"Rollback completed with errors: {rollback_errors}")
        
        return rollback_errors
    
    def complete_qualification(self, lead_id: str) -> WorkflowResult:
        """
        Complete lead qualification workflow with full error handling and rollback.
        
        Args:
            lead_id: The ID of the lead to complete
            
        Returns:
            WorkflowResult containing the workflow execution details
            
        Raises:
            LeadNotFoundError: If lead doesn't exist
            InvalidLeadStatusError: If lead status is invalid
            WorkflowError: For other workflow failures
        """
        workflow_id = f"wf_{lead_id}_{int(datetime.utcnow().timestamp())}"
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            lead_id=lead_id,
            status=WorkflowStatus.PENDING
        )
        
        try:
            self.logger.info(f"Starting lead completion workflow for lead {lead_id}")
            workflow_result.status = WorkflowStatus.IN_PROGRESS
            
            # Step 1: Retrieve and validate lead data
            with self.transaction_context() as conn:
                lead_data = self._get_lead_details(lead_id, conn)
                self._validate_lead_for_completion(lead_data)
                
                # Step 2: Update lead status
                status_action = self._update_lead_status(lead_id, 'completed', conn)
                workflow_result.actions_performed.append(status_action)
            
            # Step 3: Send contractor notification
            notification_action = self._send_contractor_notification(lead_data)
            workflow_result.actions_performed.append(notification_action)
            
            # Step 4: Send customer handoff message
            message_action = self._send_customer_handoff_message(lead_data)
            workflow_result.actions_performed.append(message_action)
            
            # Step 5: Log workflow actions
            workflow_result.end_time = datetime.utcnow()
            workflow_result.status = WorkflowStatus.COMPLETED
            
            audit_action = self._log_workflow_actions(workflow_result)
            workflow_result.actions_performed.append(audit_action)
            
            self.logger.info(f"Lead completion workflow successful for lead {lead_id}")
            return workflow_result
            
        except (LeadNotFoundError, InvalidLeadStatusError) as e:
            # These errors don't require rollback as no actions were taken
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.end_time = datetime.utcnow()
            workflow_result.error_details = str(e)
            self.logger.warning(f"Workflow validation failed for lead {lead_id}: {str(e)}")
            raise e
            
        except Exception as e:
            # Perform rollback for any completed actions
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.end_time = datetime.utcnow()
            workflow_result.error_details = str(e)
            
            self.logger.error(f"Workflow failed for lead {lead_id}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Attempt rollback
            if workflow_result.actions_performed:
                self.logger.info(f"Attempting rollback for {len(workflow_result.actions_performed)} actions")
                rollback_errors = self._rollback_actions(workflow_result.actions_performed, lead_id)
                
                if rollback_errors:
                    workflow_result.status = WorkflowStatus.ROLLED_BACK
                    workflow_result.error_details += f" | Rollback errors: {'; '.join(rollback_errors)}"
                else:
                    workflow_result.status = WorkflowStatus.ROLLED_BACK
                    self.logger.info(f"Successful rollback completed for lead {lead_id}")
            
            # Log failed workflow
            try:
                self._log_workflow_actions(workflow_result)
            except Exception as log_error:
                self.logger.error(f"Failed to log workflow failure: {str(log_error)}")
            
            raise WorkflowError(f"Lead completion workflow failed: {str(e)}")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow execution status and details"""
        try:
            return self.audit_logger.get_workflow_by_id(workflow_id)
        except Exception as e:
            self.logger.error(f"Error retrieving workflow status: {str(e)}")
            return None
    
    def retry_failed_workflow(self, workflow_id: str) -> WorkflowResult:
        """Retry a failed workflow"""
        workflow_details = self.get_workflow_status(workflow_id)
        if not workflow_details:
            raise WorkflowError(f"Workflow {workflow_id} not found")
        
        lead_id = workflow_details.get('lead_id')
        if not lead_id:
            raise WorkflowError("Lead ID not found in workflow details")
        
        return self.complete_qualification(lead_id)


# Global workflow instance
lead_workflow = LeadHandoffWorkflow()


def complete_qualification(lead_id: str) -> WorkflowResult:
    """
    Public API function to complete lead qualification workflow.
    
    Args:
        lead_id: The ID of the lead to complete
        
    Returns:
        WorkflowResult containing execution details
    """
    return lead_workflow.complete_qualification(lead_id)


def get_workflow_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a workflow execution.
    
    Args:
        workflow_id: The workflow execution ID
        
    Returns:
        Dict containing workflow details or None if not found
    """
    return lead_workflow.get_workflow_status(workflow_id)


def retry_workflow(workflow_id: str) -> WorkflowResult:
    """
    Retry a failed workflow execution.
    
    Args:
        workflow_id: The workflow execution ID to retry
        
    Returns:
        WorkflowResult containing new execution details
    """
    return lead_workflow.retry_failed_workflow(workflow_id)