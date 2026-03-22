"""
Qualified Lead Handler Module

This module handles the complete workflow for processing qualified leads,
including detection, notifications, summaries, customer handoff, and status updates.
"""

import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime

from database.connection_manager import DatabaseConnectionManager
from qualified_lead_detector import QualifiedLeadDetector
from contractor_notifier import ContractorNotifier
from lead_summary_formatter import LeadSummaryFormatter
from customer_handoff_messenger import CustomerHandoffMessenger
from notification_logger import NotificationLogger


logger = logging.getLogger(__name__)


class QualifiedLeadHandlerError(Exception):
    """Base exception for qualified lead handler errors."""
    pass


class LeadProcessingError(QualifiedLeadHandlerError):
    """Raised when lead processing fails."""
    pass


class NotificationError(QualifiedLeadHandlerError):
    """Raised when notification sending fails."""
    pass


class DatabaseTransactionError(QualifiedLeadHandlerError):
    """Raised when database transaction fails."""
    pass


class QualifiedLeadHandler:
    """Handles the complete workflow for qualified lead processing."""
    
    def __init__(
        self,
        db_manager: DatabaseConnectionManager,
        lead_detector: Optional[QualifiedLeadDetector] = None,
        contractor_notifier: Optional[ContractorNotifier] = None,
        summary_formatter: Optional[LeadSummaryFormatter] = None,
        handoff_messenger: Optional[CustomerHandoffMessenger] = None,
        notification_logger: Optional[NotificationLogger] = None
    ):
        """
        Initialize the qualified lead handler.
        
        Args:
            db_manager: Database connection manager
            lead_detector: Qualified lead detector instance
            contractor_notifier: Contractor notification service
            summary_formatter: Lead summary formatting service
            handoff_messenger: Customer handoff messaging service
            notification_logger: Notification logging service
        """
        self.db_manager = db_manager
        self.lead_detector = lead_detector or QualifiedLeadDetector()
        self.contractor_notifier = contractor_notifier or ContractorNotifier()
        self.summary_formatter = summary_formatter or LeadSummaryFormatter()
        self.handoff_messenger = handoff_messenger or CustomerHandoffMessenger()
        self.notification_logger = notification_logger or NotificationLogger()
        
    @contextmanager
    def database_transaction(self):
        """Context manager for database transactions with rollback on error."""
        connection = None
        try:
            connection = self.db_manager.get_connection()
            connection.begin()
            yield connection
            connection.commit()
            logger.info("Database transaction committed successfully")
        except Exception as e:
            if connection:
                connection.rollback()
                logger.error(f"Database transaction rolled back due to error: {e}")
            raise DatabaseTransactionError(f"Transaction failed: {e}") from e
        finally:
            if connection:
                self.db_manager.return_connection(connection)
                
    def get_lead_data(self, lead_id: int, connection) -> Dict[str, Any]:
        """
        Retrieve complete lead data from database.
        
        Args:
            lead_id: Lead identifier
            connection: Database connection
            
        Returns:
            Complete lead data dictionary
            
        Raises:
            LeadProcessingError: If lead data cannot be retrieved
        """
        try:
            cursor = connection.cursor()
            
            # Get main lead data
            cursor.execute("""
                SELECT l.*, c.name as customer_name, c.email as customer_email,
                       c.phone as customer_phone, c.address as customer_address
                FROM leads l
                JOIN customers c ON l.customer_id = c.id
                WHERE l.id = %s
            """, (lead_id,))
            
            lead_row = cursor.fetchone()
            if not lead_row:
                raise LeadProcessingError(f"Lead {lead_id} not found")
                
            # Convert to dictionary
            columns = [desc[0] for desc in cursor.description]
            lead_data = dict(zip(columns, lead_row))
            
            # Get lead interactions
            cursor.execute("""
                SELECT interaction_type, content, created_at
                FROM lead_interactions
                WHERE lead_id = %s
                ORDER BY created_at ASC
            """, (lead_id,))
            
            interactions = cursor.fetchall()
            lead_data['interactions'] = [
                {
                    'type': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                }
                for row in interactions
            ]
            
            # Get matched contractors
            cursor.execute("""
                SELECT c.id, c.name, c.email, c.phone, c.specialties,
                       lc.match_score, lc.match_reasons
                FROM lead_contractors lc
                JOIN contractors c ON lc.contractor_id = c.id
                WHERE lc.lead_id = %s
                ORDER BY lc.match_score DESC
            """, (lead_id,))
            
            contractors = cursor.fetchall()
            lead_data['matched_contractors'] = [
                {
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'specialties': row[4],
                    'match_score': row[5],
                    'match_reasons': row[6]
                }
                for row in contractors
            ]
            
            return lead_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve lead data for lead {lead_id}: {e}")
            raise LeadProcessingError(f"Failed to retrieve lead data: {e}") from e
            
    def update_lead_status(self, lead_id: int, status: str, connection) -> None:
        """
        Update lead status in database.
        
        Args:
            lead_id: Lead identifier
            status: New status
            connection: Database connection
            
        Raises:
            LeadProcessingError: If status update fails
        """
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE leads 
                SET status = %s, updated_at = %s 
                WHERE id = %s
            """, (status, datetime.utcnow(), lead_id))
            
            if cursor.rowcount == 0:
                raise LeadProcessingError(f"Lead {lead_id} not found for status update")
                
            logger.info(f"Updated lead {lead_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update status for lead {lead_id}: {e}")
            raise LeadProcessingError(f"Failed to update lead status: {e}") from e
            
    def log_processing_step(
        self, 
        lead_id: int, 
        step: str, 
        status: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log processing step for audit trail.
        
        Args:
            lead_id: Lead identifier
            step: Processing step name
            status: Step status (success/error)
            details: Additional step details
        """
        try:
            self.notification_logger.log_processing_step(
                lead_id=lead_id,
                step=step,
                status=status,
                details=details or {}
            )
        except Exception as e:
            # Don't fail the whole process for logging errors
            logger.warning(f"Failed to log processing step {step} for lead {lead_id}: {e}")
            
    def send_contractor_notifications(
        self, 
        lead_data: Dict[str, Any], 
        lead_summary: str
    ) -> List[Dict[str, Any]]:
        """
        Send notifications to all matched contractors.
        
        Args:
            lead_data: Complete lead data
            lead_summary: Formatted lead summary
            
        Returns:
            List of notification results
            
        Raises:
            NotificationError: If critical notifications fail
        """
        notification_results = []
        contractors = lead_data.get('matched_contractors', [])
        
        if not contractors:
            logger.warning(f"No contractors found for lead {lead_data['id']}")
            return notification_results
            
        for contractor in contractors:
            try:
                result = self.contractor_notifier.send_qualified_lead_notification(
                    contractor_data=contractor,
                    lead_summary=lead_summary,
                    lead_data=lead_data
                )
                
                notification_results.append({
                    'contractor_id': contractor['id'],
                    'contractor_name': contractor['name'],
                    'status': 'success',
                    'notification_id': result.get('notification_id'),
                    'sent_at': result.get('sent_at')
                })
                
                logger.info(f"Successfully notified contractor {contractor['name']} about lead {lead_data['id']}")
                
            except Exception as e:
                error_msg = f"Failed to notify contractor {contractor['name']}: {e}"
                logger.error(error_msg)
                
                notification_results.append({
                    'contractor_id': contractor['id'],
                    'contractor_name': contractor['name'],
                    'status': 'error',
                    'error': str(e),
                    'failed_at': datetime.utcnow().isoformat()
                })
                
        # Check if any critical notifications failed
        failed_notifications = [r for r in notification_results if r['status'] == 'error']
        if failed_notifications and len(failed_notifications) == len(contractors):
            raise NotificationError("All contractor notifications failed")
            
        return notification_results
        
    def send_customer_handoff_message(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send handoff message to customer.
        
        Args:
            lead_data: Complete lead data
            
        Returns:
            Handoff message result
            
        Raises:
            NotificationError: If customer notification fails
        """
        try:
            result = self.handoff_messenger.send_handoff_message(
                customer_data={
                    'name': lead_data['customer_name'],
                    'email': lead_data['customer_email'],
                    'phone': lead_data['customer_phone']
                },
                lead_data=lead_data,
                matched_contractors=lead_data.get('matched_contractors', [])
            )
            
            logger.info(f"Successfully sent handoff message to customer for lead {lead_data['id']}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to send customer handoff message for lead {lead_data['id']}: {e}"
            logger.error(error_msg)
            raise NotificationError(error_msg) from e
            
    def process_qualified_lead(self, lead_id: int) -> Dict[str, Any]:
        """
        Process a qualified lead through the complete workflow.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Processing results dictionary
            
        Raises:
            LeadProcessingError: If processing fails
            NotificationError: If notifications fail
            DatabaseTransactionError: If database operations fail
        """
        processing_results = {
            'lead_id': lead_id,
            'started_at': datetime.utcnow().isoformat(),
            'status': 'processing',
            'steps': {}
        }
        
        try:
            with self.database_transaction() as connection:
                # Step 1: Get lead data
                self.log_processing_step(lead_id, 'data_retrieval', 'started')
                lead_data = self.get_lead_data(lead_id, connection)
                processing_results['steps']['data_retrieval'] = {'status': 'success'}
                self.log_processing_step(lead_id, 'data_retrieval', 'success', {
                    'customer_name': lead_data['customer_name'],
                    'contractor_count': len(lead_data.get('matched_contractors', []))
                })
                
                # Step 2: Verify lead is qualified
                self.log_processing_step(lead_id, 'qualification_check', 'started')
                is_qualified = self.lead_detector.is_lead_qualified(lead_data)
                
                if not is_qualified:
                    error_msg = f"Lead {lead_id} is not qualified for processing"
                    self.log_processing_step(lead_id, 'qualification_check', 'error', {
                        'reason': 'not_qualified'
                    })
                    raise LeadProcessingError(error_msg)
                    
                processing_results['steps']['qualification_check'] = {'status': 'success'}
                self.log_processing_step(lead_id, 'qualification_check', 'success')
                
                # Step 3: Generate lead summary
                self.log_processing_step(lead_id, 'summary_generation', 'started')
                lead_summary = self.summary_formatter.format_complete_summary(lead_data)
                processing_results['steps']['summary_generation'] = {
                    'status': 'success',
                    'summary_length': len(lead_summary)
                }
                self.log_processing_step(lead_id, 'summary_generation', 'success', {
                    'summary_length': len(lead_summary)
                })
                
                # Step 4: Send contractor notifications
                self.log_processing_step(lead_id, 'contractor_notifications', 'started')
                contractor_results = self.send_contractor_notifications(lead_data, lead_summary)
                processing_results['steps']['contractor_notifications'] = {
                    'status': 'success',
                    'results': contractor_results,
                    'total_contractors': len(contractor_results),
                    'successful_notifications': len([r for r in contractor_results if r['status'] == 'success'])
                }
                self.log_processing_step(lead_id, 'contractor_notifications', 'success', {
                    'contractor_results': contractor_results
                })
                
                # Step 5: Send customer handoff message
                self.log_processing_step(lead_id, 'customer_handoff', 'started')
                handoff_result = self.send_customer_handoff_message(lead_data)
                processing_results['steps']['customer_handoff'] = {
                    'status': 'success',
                    'result': handoff_result
                }
                self.log_processing_step(lead_id, 'customer_handoff', 'success', {
                    'handoff_result': handoff_result
                })
                
                # Step 6: Update lead status to completed
                self.log_processing_step(lead_id, 'status_update', 'started')
                self.update_lead_status(lead_id, 'completed', connection)
                processing_results['steps']['status_update'] = {'status': 'success'}
                self.log_processing_step(lead_id, 'status_update', 'success', {
                    'new_status': 'completed'
                })
                
                # All steps completed successfully
                processing_results['status'] = 'completed'
                processing_results['completed_at'] = datetime.utcnow().isoformat()
                
                logger.info(f"Successfully processed qualified lead {lead_id}")
                
                # Log final success
                self.log_processing_step(lead_id, 'workflow_completion', 'success', {
                    'processing_results': processing_results
                })
                
                return processing_results
                
        except (NotificationError, LeadProcessingError, DatabaseTransactionError) as e:
            processing_results['status'] = 'error'
            processing_results['error'] = str(e)
            processing_results['failed_at'] = datetime.utcnow().isoformat()
            
            self.log_processing_step(lead_id, 'workflow_completion', 'error', {
                'error': str(e),
                'processing_results': processing_results
            })
            
            logger.error(f"Failed to process qualified lead {lead_id}: {e}")
            raise
            
        except Exception as e:
            processing_results['status'] = 'error'
            processing_results['error'] = f"Unexpected error: {e}"
            processing_results['failed_at'] = datetime.utcnow().isoformat()
            
            self.log_processing_step(lead_id, 'workflow_completion', 'error', {
                'error': f"Unexpected error: {e}",
                'processing_results': processing_results
            })
            
            error_msg = f"Unexpected error processing qualified lead {lead_id}: {e}"
            logger.error(error_msg)
            raise LeadProcessingError(error_msg) from e
            
    def process_qualified_leads_batch(self, lead_ids: List[int]) -> Dict[str, Any]:
        """
        Process multiple qualified leads in batch.
        
        Args:
            lead_ids: List of lead identifiers
            
        Returns:
            Batch processing results
        """
        batch_results = {
            'started_at': datetime.utcnow().isoformat(),
            'total_leads': len(lead_ids),
            'successful': 0,
            'failed': 0,
            'results': []
        }
        
        logger.info(f"Starting batch processing of {len(lead_ids)} qualified leads")
        
        for lead_id in lead_ids:
            try:
                result = self.process_qualified_lead(lead_id)
                batch_results['results'].append(result)
                batch_results['successful'] += 1
                
            except Exception as e:
                batch_results['results'].append({
                    'lead_id': lead_id,
                    'status': 'error',
                    'error': str(e),
                    'failed_at': datetime.utcnow().isoformat()
                })
                batch_results['failed'] += 1
                
        batch_results['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(
            f"Batch processing completed: {batch_results['successful']} successful, "
            f"{batch_results['failed']} failed out of {batch_results['total_leads']} total"
        )
        
        return batch_results
        
    def get_processing_status(self, lead_id: int) -> Dict[str, Any]:
        """
        Get processing status for a lead.
        
        Args:
            lead_id: Lead identifier
            
        Returns:
            Processing status information
        """
        try:
            return self.notification_logger.get_lead_processing_history(lead_id)
        except Exception as e:
            logger.error(f"Failed to get processing status for lead {lead_id}: {e}")
            return {
                'lead_id': lead_id,
                'status': 'unknown',
                'error': f"Failed to retrieve status: {e}"
            }