import asyncio
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime

from conversation_manager import ConversationManager, ConversationState
from qualified_lead_detector import QualifiedLeadDetector
from contractor_notifier import ContractorNotifier
from customer_handoff_messenger import CustomerHandoffMessenger
from database import Database
from lead_scorer import LeadScorer
from message_processor import MessageProcessor
from response_generator import ResponseGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatbotMain:
    def __init__(self):
        self.db = Database()
        self.conversation_manager = ConversationManager(self.db)
        self.lead_scorer = LeadScorer()
        self.message_processor = MessageProcessor()
        self.response_generator = ResponseGenerator()
        self.qualified_lead_detector = QualifiedLeadDetector()
        self.contractor_notifier = ContractorNotifier()
        self.customer_handoff_messenger = CustomerHandoffMessenger()
        
    async def initialize(self):
        """Initialize the chatbot system."""
        try:
            await self.db.initialize()
            logger.info("Chatbot system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot system: {e}")
            raise

    async def process_message(self, user_id: str, message: str, channel: str = "web") -> Dict[str, Any]:
        """
        Process an incoming message and return the response.
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            channel: The communication channel (web, sms, etc.)
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # Get or create conversation
            conversation = await self.conversation_manager.get_or_create_conversation(user_id, channel)
            
            # Process the incoming message
            processed_message = await self.message_processor.process(message, conversation)
            
            # Update conversation with user message
            await self.conversation_manager.add_message(
                conversation.id,
                "user",
                processed_message["text"],
                processed_message.get("metadata", {})
            )
            
            # Generate response
            response_data = await self.response_generator.generate_response(
                conversation, processed_message
            )
            
            # Add bot response to conversation
            await self.conversation_manager.add_message(
                conversation.id,
                "bot",
                response_data["text"],
                response_data.get("metadata", {})
            )
            
            # Update lead score
            lead_score = await self.lead_scorer.calculate_score(conversation)
            await self.conversation_manager.update_lead_score(conversation.id, lead_score)
            
            # Check for qualified leads after conversation update
            await self._check_and_handle_qualified_lead(conversation, lead_score)
            
            return {
                "success": True,
                "response": response_data["text"],
                "conversation_id": conversation.id,
                "lead_score": lead_score,
                "metadata": response_data.get("metadata", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm sorry, I encountered an error processing your message. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _check_and_handle_qualified_lead(self, conversation, lead_score: float):
        """
        Check if a lead is qualified and handle the handoff process.
        
        Args:
            conversation: The conversation object
            lead_score: Current lead score
        """
        try:
            # Skip if lead is already completed or in handoff
            if conversation.lead_status in ["completed", "handoff_in_progress"]:
                return
                
            # Check if lead is qualified
            is_qualified = await self.qualified_lead_detector.is_qualified_lead(conversation, lead_score)
            
            if is_qualified:
                logger.info(f"Qualified lead detected for conversation {conversation.id}")
                
                # Update lead status to handoff in progress
                await self.conversation_manager.update_lead_status(
                    conversation.id, 
                    "handoff_in_progress"
                )
                
                # Perform handoff process
                await self._perform_lead_handoff(conversation)
                
        except Exception as e:
            logger.error(f"Error handling qualified lead for conversation {conversation.id}: {e}")
            # Revert status if handoff failed
            try:
                await self.conversation_manager.update_lead_status(
                    conversation.id, 
                    "qualified"
                )
            except:
                pass

    async def _perform_lead_handoff(self, conversation):
        """
        Perform the complete lead handoff process.
        
        Args:
            conversation: The conversation object
        """
        try:
            # Step 1: Notify contractors
            contractor_notification_sent = await self._notify_contractors(conversation)
            
            if not contractor_notification_sent:
                logger.warning(f"Failed to notify contractors for conversation {conversation.id}")
                return
            
            # Step 2: Send customer handoff message
            customer_message_sent = await self._send_customer_handoff_message(conversation)
            
            if not customer_message_sent:
                logger.warning(f"Failed to send customer handoff message for conversation {conversation.id}")
                return
            
            # Step 3: Update lead status to completed
            await self.conversation_manager.update_lead_status(
                conversation.id, 
                "completed"
            )
            
            # Step 4: Log successful handoff
            await self._log_successful_handoff(conversation)
            
            logger.info(f"Successfully completed lead handoff for conversation {conversation.id}")
            
        except Exception as e:
            logger.error(f"Error during lead handoff for conversation {conversation.id}: {e}")
            # Update status to indicate handoff failure
            try:
                await self.conversation_manager.update_lead_status(
                    conversation.id, 
                    "handoff_failed"
                )
            except:
                pass
            raise

    async def _notify_contractors(self, conversation) -> bool:
        """
        Notify contractors about the qualified lead.
        
        Args:
            conversation: The conversation object
            
        Returns:
            bool: True if notification was successful
        """
        try:
            # Extract lead information
            lead_info = await self._extract_lead_info(conversation)
            
            # Send contractor notifications
            notification_result = await self.contractor_notifier.notify_contractors(
                lead_info,
                conversation.id
            )
            
            if notification_result.get("success", False):
                logger.info(f"Contractors notified for conversation {conversation.id}")
                return True
            else:
                logger.error(f"Failed to notify contractors: {notification_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error notifying contractors for conversation {conversation.id}: {e}")
            return False

    async def _send_customer_handoff_message(self, conversation) -> bool:
        """
        Send handoff message to customer.
        
        Args:
            conversation: The conversation object
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Send customer handoff message
            message_result = await self.customer_handoff_messenger.send_handoff_message(
                conversation.user_id,
                conversation.channel,
                conversation.id
            )
            
            if message_result.get("success", False):
                logger.info(f"Customer handoff message sent for conversation {conversation.id}")
                
                # Add the handoff message to conversation history
                await self.conversation_manager.add_message(
                    conversation.id,
                    "system",
                    message_result.get("message", "Your request has been forwarded to our contractors."),
                    {"type": "handoff_message", "timestamp": datetime.utcnow().isoformat()}
                )
                
                return True
            else:
                logger.error(f"Failed to send customer handoff message: {message_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending customer handoff message for conversation {conversation.id}: {e}")
            return False

    async def _extract_lead_info(self, conversation) -> Dict[str, Any]:
        """
        Extract relevant lead information from conversation.
        
        Args:
            conversation: The conversation object
            
        Returns:
            Dictionary containing lead information
        """
        try:
            # Get conversation messages
            messages = await self.conversation_manager.get_conversation_messages(conversation.id)
            
            # Extract lead information using qualified lead detector
            lead_info = await self.qualified_lead_detector.extract_lead_info(conversation, messages)
            
            # Add basic conversation metadata
            lead_info.update({
                "conversation_id": conversation.id,
                "user_id": conversation.user_id,
                "channel": conversation.channel,
                "created_at": conversation.created_at,
                "lead_score": conversation.lead_score
            })
            
            return lead_info
            
        except Exception as e:
            logger.error(f"Error extracting lead info for conversation {conversation.id}: {e}")
            return {
                "conversation_id": conversation.id,
                "user_id": conversation.user_id,
                "channel": conversation.channel,
                "error": "Failed to extract lead information"
            }

    async def _log_successful_handoff(self, conversation):
        """
        Log successful handoff for analytics and monitoring.
        
        Args:
            conversation: The conversation object
        """
        try:
            handoff_data = {
                "conversation_id": conversation.id,
                "user_id": conversation.user_id,
                "channel": conversation.channel,
                "lead_score": conversation.lead_score,
                "handoff_completed_at": datetime.utcnow().isoformat(),
                "total_messages": len(await self.conversation_manager.get_conversation_messages(conversation.id))
            }
            
            # Log to database for analytics
            await self.db.log_handoff_event("completed", handoff_data)
            
            logger.info(f"Handoff event logged for conversation {conversation.id}")
            
        except Exception as e:
            logger.error(f"Error logging handoff event for conversation {conversation.id}: {e}")

    async def get_conversation_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: The user's unique identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            Dictionary containing conversation history
        """
        try:
            conversations = await self.conversation_manager.get_user_conversations(user_id, limit)
            
            return {
                "success": True,
                "conversations": conversations,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_lead_status(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the current lead status for a conversation.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Dictionary containing lead status information
        """
        try:
            conversation = await self.conversation_manager.get_conversation(conversation_id)
            
            if not conversation:
                return {
                    "success": False,
                    "error": "Conversation not found"
                }
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "lead_status": conversation.lead_status,
                "lead_score": conversation.lead_score,
                "last_updated": conversation.updated_at,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving lead status for conversation {conversation_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def shutdown(self):
        """Gracefully shutdown the chatbot system."""
        try:
            await self.db.close()
            logger.info("Chatbot system shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Main execution function
async def main():
    """Main entry point for the chatbot system."""
    chatbot = ChatbotMain()
    
    try:
        await chatbot.initialize()
        logger.info("Chatbot system started successfully")
        
        # Keep the system running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
    finally:
        await chatbot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())