import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json

from .lead_qualifier import LeadQualifier
from .handoff_orchestrator import HandoffOrchestrator
from .notification_service import NotificationService
from .crm_integration import CRMIntegration
from .conversation_manager import ConversationManager
from .response_generator import ResponseGenerator
from .context_manager import ContextManager
from .analytics_tracker import AnalyticsTracker

logger = logging.getLogger(__name__)

class EnhancedMainLoop:
    """Enhanced main conversation loop with integrated lead qualification and handoff capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize core components
        self.conversation_manager = ConversationManager(config)
        self.response_generator = ResponseGenerator(config)
        self.context_manager = ContextManager(config)
        self.analytics_tracker = AnalyticsTracker(config)
        
        # Initialize handoff components
        self.lead_qualifier = LeadQualifier(config.get('lead_qualification', {}))
        self.handoff_orchestrator = HandoffOrchestrator(config.get('handoff', {}))
        self.notification_service = NotificationService(config.get('notifications', {}))
        self.crm_integration = CRMIntegration(config.get('crm', {}))
        
        # Configuration
        self.max_conversation_length = config.get('max_conversation_length', 100)
        self.qualification_check_interval = config.get('qualification_check_interval', 1)
        self.handoff_timeout = config.get('handoff_timeout', 300)
        self.error_retry_limit = config.get('error_retry_limit', 3)
        
        # State tracking
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        self.handoff_in_progress: Dict[str, bool] = {}
        self.error_counts: Dict[str, int] = {}
        
        logger.info("Enhanced main loop initialized with handoff capabilities")

    async def start_conversation(self, conversation_id: str, initial_message: str, 
                                customer_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a new conversation with enhanced tracking and qualification."""
        try:
            logger.info(f"Starting conversation {conversation_id}")
            
            # Initialize conversation state
            conversation_state = {
                'id': conversation_id,
                'started_at': datetime.now(timezone.utc),
                'customer_info': customer_info or {},
                'message_count': 0,
                'qualified': False,
                'handoff_attempted': False,
                'last_qualification_check': None,
                'interaction_scores': [],
                'context_data': {}
            }
            
            self.active_conversations[conversation_id] = conversation_state
            self.handoff_in_progress[conversation_id] = False
            self.error_counts[conversation_id] = 0
            
            # Process initial message
            response = await self._process_message(
                conversation_id, 
                initial_message, 
                is_initial=True
            )
            
            # Track conversation start
            await self.analytics_tracker.track_conversation_start(
                conversation_id, 
                customer_info
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error starting conversation {conversation_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return await self._handle_error(conversation_id, "conversation_start", e)

    async def process_message(self, conversation_id: str, message: str, 
                            message_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a customer message with integrated qualification and handoff detection."""
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"Conversation {conversation_id} not found, starting new conversation")
                return await self.start_conversation(conversation_id, message)
            
            # Check if handoff is in progress
            if self.handoff_in_progress.get(conversation_id, False):
                return await self._handle_handoff_in_progress(conversation_id, message)
            
            # Process the message
            response = await self._process_message(
                conversation_id, 
                message, 
                message_metadata
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message for conversation {conversation_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return await self._handle_error(conversation_id, "message_processing", e)

    async def _process_message(self, conversation_id: str, message: str, 
                             message_metadata: Dict[str, Any] = None, 
                             is_initial: bool = False) -> Dict[str, Any]:
        """Internal message processing with qualification and handoff logic."""
        conversation_state = self.active_conversations[conversation_id]
        
        try:
            # Update conversation state
            conversation_state['message_count'] += 1
            conversation_state['last_message_at'] = datetime.now(timezone.utc)
            
            # Get conversation context
            context = await self.context_manager.get_context(conversation_id)
            
            # Update context with new message
            await self.context_manager.add_message(
                conversation_id, 
                'customer', 
                message,
                metadata=message_metadata
            )
            
            # Generate response
            bot_response = await self.response_generator.generate_response(
                conversation_id,
                message,
                context,
                conversation_state['customer_info']
            )
            
            # Add bot response to context
            await self.context_manager.add_message(
                conversation_id,
                'assistant',
                bot_response.get('content', ''),
                metadata={'response_type': bot_response.get('type', 'standard')}
            )
            
            # Check for lead qualification after each interaction
            await self._check_lead_qualification(conversation_id, message, bot_response)
            
            # Prepare response
            response = {
                'conversation_id': conversation_id,
                'message': bot_response.get('content', ''),
                'message_type': bot_response.get('type', 'standard'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'qualified': conversation_state.get('qualified', False),
                'handoff_available': self._should_offer_handoff(conversation_state),
                'metadata': {
                    'message_count': conversation_state['message_count'],
                    'qualification_score': conversation_state.get('qualification_score', 0),
                    'interaction_quality': bot_response.get('quality_score', 0)
                }
            }
            
            # Track interaction
            await self.analytics_tracker.track_interaction(
                conversation_id,
                'customer_message',
                {
                    'message_length': len(message),
                    'response_type': bot_response.get('type', 'standard'),
                    'qualification_score': conversation_state.get('qualification_score', 0)
                }
            )
            
            # Reset error count on successful processing
            self.error_counts[conversation_id] = 0
            
            return response
            
        except Exception as e:
            logger.error(f"Error in _process_message for {conversation_id}: {str(e)}")
            raise

    async def _check_lead_qualification(self, conversation_id: str, 
                                      customer_message: str, 
                                      bot_response: Dict[str, Any]):
        """Check if the lead should be qualified and trigger handoff if necessary."""
        conversation_state = self.active_conversations[conversation_id]
        
        try:
            # Get full conversation context for qualification
            context = await self.context_manager.get_context(conversation_id)
            
            # Perform qualification check
            qualification_result = await self.lead_qualifier.qualify_lead(
                conversation_id,
                context,
                conversation_state['customer_info']
            )
            
            # Update conversation state with qualification results
            conversation_state['qualification_score'] = qualification_result.get('score', 0)
            conversation_state['qualification_factors'] = qualification_result.get('factors', {})
            conversation_state['last_qualification_check'] = datetime.now(timezone.utc)
            
            # Check if lead is now qualified
            if qualification_result.get('qualified', False) and not conversation_state.get('qualified', False):
                logger.info(f"Lead qualified for conversation {conversation_id}")
                conversation_state['qualified'] = True
                conversation_state['qualified_at'] = datetime.now(timezone.utc)
                
                # Track qualification event
                await self.analytics_tracker.track_lead_qualification(
                    conversation_id,
                    qualification_result
                )
                
                # Check if automatic handoff should be triggered
                if await self._should_trigger_automatic_handoff(qualification_result):
                    await self._trigger_automatic_handoff(conversation_id, qualification_result)
            
            # Store interaction quality score
            interaction_score = {
                'timestamp': datetime.now(timezone.utc),
                'customer_message_length': len(customer_message),
                'bot_response_type': bot_response.get('type', 'standard'),
                'qualification_score': qualification_result.get('score', 0),
                'engagement_level': qualification_result.get('engagement_level', 'low')
            }
            
            conversation_state['interaction_scores'].append(interaction_score)
            
            # Keep only recent interaction scores
            if len(conversation_state['interaction_scores']) > 10:
                conversation_state['interaction_scores'] = conversation_state['interaction_scores'][-10:]
            
        except Exception as e:
            logger.error(f"Error in lead qualification check for {conversation_id}: {str(e)}")
            # Don't fail the entire interaction if qualification fails
            conversation_state['qualification_error'] = str(e)

    async def _should_trigger_automatic_handoff(self, qualification_result: Dict[str, Any]) -> bool:
        """Determine if automatic handoff should be triggered based on qualification results."""
        score = qualification_result.get('score', 0)
        factors = qualification_result.get('factors', {})
        
        # High-priority triggers
        if score >= 90:  # Very high qualification score
            return True
        
        if factors.get('explicit_sales_request', False):  # Customer explicitly asked for sales
            return True
            
        if factors.get('high_value_opportunity', False):  # High value potential
            return True
            
        if factors.get('ready_to_buy', False):  # Strong buying signals
            return True
        
        # Medium-priority triggers (require multiple factors)
        medium_triggers = [
            factors.get('budget_confirmed', False),
            factors.get('timeline_urgent', False),
            factors.get('decision_maker', False),
            score >= 70
        ]
        
        if sum(medium_triggers) >= 2:  # At least 2 medium triggers
            return True
        
        return False

    async def _trigger_automatic_handoff(self, conversation_id: str, 
                                       qualification_result: Dict[str, Any]):
        """Trigger automatic handoff for qualified leads."""
        try:
            logger.info(f"Triggering automatic handoff for conversation {conversation_id}")
            
            conversation_state = self.active_conversations[conversation_id]
            
            # Mark handoff in progress
            self.handoff_in_progress[conversation_id] = True
            conversation_state['handoff_attempted'] = True
            conversation_state['handoff_triggered_at'] = datetime.now(timezone.utc)
            
            # Get conversation context for handoff
            context = await self.context_manager.get_context(conversation_id)
            
            # Prepare handoff data
            handoff_data = {
                'conversation_id': conversation_id,
                'customer_info': conversation_state['customer_info'],
                'qualification_result': qualification_result,
                'conversation_context': context,
                'handoff_reason': 'automatic_qualification',
                'priority': self._calculate_handoff_priority(qualification_result),
                'requested_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Execute handoff through orchestrator
            handoff_result = await self.handoff_orchestrator.initiate_handoff(
                conversation_id,
                handoff_data
            )
            
            # Update conversation state with handoff result
            conversation_state['handoff_result'] = handoff_result
            conversation_state['handoff_status'] = handoff_result.get('status', 'failed')
            
            # Track handoff event
            await self.analytics_tracker.track_handoff_initiated(
                conversation_id,
                handoff_result
            )
            
            logger.info(f"Automatic handoff initiated for {conversation_id}: {handoff_result.get('status', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error triggering automatic handoff for {conversation_id}: {str(e)}")
            self.handoff_in_progress[conversation_id] = False
            conversation_state['handoff_error'] = str(e)

    def _calculate_handoff_priority(self, qualification_result: Dict[str, Any]) -> str:
        """Calculate handoff priority based on qualification factors."""
        score = qualification_result.get('score', 0)
        factors = qualification_result.get('factors', {})
        
        # High priority conditions
        if (score >= 90 or 
            factors.get('explicit_sales_request', False) or
            factors.get('high_value_opportunity', False)):
            return 'high'
        
        # Medium priority conditions
        if (score >= 70 or
            factors.get('ready_to_buy', False) or
            factors.get('timeline_urgent', False)):
            return 'medium'
        
        return 'normal'

    def _should_offer_handoff(self, conversation_state: Dict[str, Any]) -> bool:
        """Determine if handoff should be offered to the customer."""
        if conversation_state.get('qualified', False) and not conversation_state.get('handoff_attempted', False):
            return True
        
        # Offer handoff for long conversations even if not fully qualified
        if conversation_state['message_count'] >= 15:
            return True
        
        return False

    async def request_handoff(self, conversation_id: str, 
                            handoff_reason: str = 'customer_request') -> Dict[str, Any]:
        """Handle explicit handoff requests from customers."""
        try:
            if conversation_id not in self.active_conversations:
                return {'success': False, 'error': 'Conversation not found'}
            
            if self.handoff_in_progress.get(conversation_id, False):
                return {'success': False, 'error': 'Handoff already in progress'}
            
            conversation_state = self.active_conversations[conversation_id]
            
            logger.info(f"Processing handoff request for conversation {conversation_id}")
            
            # Mark handoff in progress
            self.handoff_in_progress[conversation_id] = True
            conversation_state['handoff_attempted'] = True
            conversation_state['handoff_requested_at'] = datetime.now(timezone.utc)
            
            # Get current qualification status
            context = await self.context_manager.get_context(conversation_id)
            qualification_result = await self.lead_qualifier.qualify_lead(
                conversation_id,
                context,
                conversation_state['customer_info']
            )
            
            # Prepare handoff data
            handoff_data = {
                'conversation_id': conversation_id,
                'customer_info': conversation_state['customer_info'],
                'qualification_result': qualification_result,
                'conversation_context': context,
                'handoff_reason': handoff_reason,
                'priority': 'high' if handoff_reason == 'customer_request' else 'normal',
                'requested_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Execute handoff
            handoff_result = await self.handoff_orchestrator.initiate_handoff(
                conversation_id,
                handoff_data
            )
            
            # Update conversation state
            conversation_state['handoff_result'] = handoff_result
            conversation_state['handoff_status'] = handoff_result.get('status', 'failed')
            
            # Track handoff event
            await self.analytics_tracker.track_handoff_initiated(
                conversation_id,
                handoff_result
            )
            
            return {
                'success': handoff_result.get('success', False),
                'status': handoff_result.get('status', 'failed'),
                'message': handoff_result.get('message', 'Handoff processing'),
                'estimated_wait_time': handoff_result.get('estimated_wait_time'),
                'handoff_id': handoff_result.get('handoff_id')
            }
            
        except Exception as e:
            logger.error(f"Error processing handoff request for {conversation_id}: {str(e)}")
            self.handoff_in_progress[conversation_id] = False
            return {'success': False, 'error': 'Internal error processing handoff request'}

    async def _handle_handoff_in_progress(self, conversation_id: str, 
                                        message: str) -> Dict[str, Any]:
        """Handle messages when handoff is in progress."""
        try:
            conversation_state = self.active_conversations[conversation_id]
            handoff_status = conversation_state.get('handoff_status', 'unknown')
            
            # Check current handoff status
            handoff_result = conversation_state.get('handoff_result', {})
            handoff_id = handoff_result.get('handoff_id')
            
            if handoff_id:
                # Get updated status from orchestrator
                status_update = await self.handoff_orchestrator.get_handoff_status(handoff_id)
                handoff_status = status_update.get('status', handoff_status)
                conversation_state['handoff_status'] = handoff_status
            
            # Generate appropriate response based on handoff status
            if handoff_status == 'completed':
                self.handoff_in_progress[conversation_id] = False
                response_content = "Great! You've been successfully connected with one of our specialists. They'll be with you shortly."
            elif handoff_status == 'failed':
                self.handoff_in_progress[conversation_id] = False
                response_content = "I apologize, but there was an issue with the handoff. Let me continue to assist you, or we can try the handoff again."
            elif handoff_status == 'pending':
                response_content = f"I've added your message to the queue. You're still in line to speak with a specialist. Current wait time is approximately {handoff_result.get('estimated_wait_time', 'unknown')}."
            else:
                response_content = "Your request to speak with a specialist is being processed. Please hold on while I connect you."
            
            # Add message to context for continuity
            await self.context_manager.add_message(
                conversation_id,
                'customer',
                message,
                metadata={'during_handoff': True}
            )
            
            await self.context_manager.add_message(
                conversation_id,
                'assistant',
                response_content,
                metadata={'handoff_status': handoff_status}
            )
            
            return {
                'conversation_id': conversation_id,
                'message': response_content,
                'message_type': 'handoff_status',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'handoff_status': handoff_status,
                'qualified': conversation_state.get('qualified', False),
                'metadata': {
                    'handoff_in_progress': True,
                    'handoff_id': handoff_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error handling handoff in progress for {conversation_id}: {str(e)}")
            # Fall back to normal processing
            self.handoff_in_progress[conversation_id] = False
            return await self._process_message(conversation_id, message)

    async def _handle_error(self, conversation_id: str, error_type: str, 
                          error: Exception) -> Dict[str, Any]:
        """Handle errors with retry logic and graceful degradation."""
        self.error_counts[conversation_id] = self.error_counts.get(conversation_id, 0) + 1
        
        # Track error
        await self.analytics_tracker.track_error(
            conversation_id,
            error_type,
            str(error)
        )
        
        # If too many errors, end conversation gracefully
        if self.error_counts[conversation_id] >= self.error_retry_limit:
            logger.error(f"Too many errors for conversation {conversation_id}, ending gracefully")
            await self.end_conversation(conversation_id, reason='error_limit_exceeded')
            
            return {
                'conversation_id': conversation_id,
                'message': "I'm experiencing technical difficulties. Please try starting a new conversation or contact our support team directly.",
                'message_type': 'error',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': True,
                'conversation_ended': True
            }
        
        # Return generic error response
        return {
            'conversation_id': conversation_id,
            'message': "I'm having trouble processing that. Could you please rephrase your question?",
            'message_type': 'error',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': True,
            'retry_count': self.error_counts[conversation_id]
        }

    async def end_conversation(self, conversation_id: str, 
                             reason: str = 'customer_ended') -> Dict[str, Any]:
        """End a conversation and clean up resources."""
        try:
            if conversation_id not in self.active_conversations:
                return {'success': False, 'error': 'Conversation not found'}
            
            conversation_state = self.active_conversations[conversation_id]
            conversation_state['ended_at'] = datetime.now(timezone.utc)
            conversation_state['end_reason'] = reason
            
            # Track conversation end
            await self.analytics_tracker.track_conversation_end(
                conversation_id,
                reason,
                conversation_state
            )
            
            # Cancel any pending handoffs
            if self.handoff_in_progress.get(conversation_id, False):
                handoff_result = conversation_state.get('handoff_result', {})
                handoff_id = handoff_result.get('handoff_id')
                
                if handoff_id:
                    try:
                        await self.handoff_orchestrator.cancel_handoff(handoff_id, reason)
                    except Exception as e:
                        logger.error(f"Error canceling handoff {handoff_id}: {str(e)}")
            
            # Clean up state
            self.active_conversations.pop(conversation_id, None)
            self.handoff_in_progress.pop(conversation_id, None)
            self.error_counts.pop(conversation_id, None)
            
            # Clean up context (optionally, based on retention policy)
            await self.context_manager.archive_conversation(conversation_id)
            
            logger.info(f"Conversation {conversation_id} ended: {reason}")
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'ended_at': conversation_state['ended_at'].isoformat(),
                'reason': reason,
                'message_count': conversation_state.get('message_count', 0),
                'qualified': conversation_state.get('qualified', False)
            }
            
        except Exception as e:
            logger.error(f"Error ending conversation {conversation_id}: {str(e)}")
            return {'success': False, 'error': 'Error ending conversation'}

    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get current status of a conversation."""
        try:
            if conversation_id not in self.active_conversations:
                return {'exists': False, 'error': 'Conversation not found'}
            
            conversation_state = self.active_conversations[conversation_id]
            
            # Get handoff status if applicable
            handoff_status = None
            if self.handoff_in_progress.get(conversation_id, False):
                handoff_result = conversation_state.get('handoff_result', {})
                handoff_id = handoff_result.get('handoff_id')
                
                if handoff_id:
                    try:
                        status_update = await self.handoff_orchestrator.get_handoff_status(handoff_id)
                        handoff_status = status_update.get('status')
                    except Exception as e:
                        logger.error(f"Error getting handoff status: {str(e)}")
            
            return {
                'exists': True,
                'conversation_id': conversation_id,
                'started_at': conversation_state['started_at'].isoformat(),
                'message_count': conversation_state['message_count'],
                'qualified': conversation_state.get('qualified', False),
                'qualification_score': conversation_state.get('qualification_score', 0),
                'handoff_in_progress': self.handoff_in_progress.get(conversation_id, False),
                'handoff_status': handoff_status,
                'last_message_at': conversation_state.get('last_message_at', '').isoformat() if conversation_state.get('last_message_at') else None,
                'customer_info': conversation_state.get('customer_info', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation status for {conversation_id}: {str(e)}")
            return {'exists': False, 'error': 'Error retrieving conversation status'}

    async def cleanup_inactive_conversations(self, max_age_hours: int = 24):
        """Clean up old inactive conversations."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            conversations_to_end = []
            
            for conversation_id, state in self.active_conversations.items():
                last_activity = state.get('last_message_at', state['started_at'])
                if last_activity < cutoff_time:
                    conversations_to_end.append(conversation_id)
            
            for conversation_id in conversations_to_end:
                await self.end_conversation(conversation_id, reason='inactive_timeout')
            
            logger.info(f"Cleaned up {len(conversations_to_end)} inactive conversations")
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive conversations: {str(e)}")

    def get_active_conversation_count(self) -> int:
        """Get count of currently active conversations."""
        return len(self.active_conversations)

    def get_handoff_in_progress_count(self) -> int:
        """Get count of conversations with handoffs in progress."""
        return sum(1 for status in self.handoff_in_progress.values() if status)