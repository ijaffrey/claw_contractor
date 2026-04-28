import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from database import Database
from models.conversation import Conversation, Message
from models.lead import Lead
from qualification import QualificationManager

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation flow, history, and qualification state for leads.
    Handles database operations for messages and conversation tracking.
    """

    def __init__(self, database: Database):
        self.database = database
        self.qualification_manager = QualificationManager()

    def load_conversation_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Query database for all messages associated with lead_id.
        Returns chronological list with message content, timestamps, sender type, and qualification state.

        Args:
            lead_id: Unique identifier for the lead

        Returns:
            List of message dictionaries with chronological order
        """
        try:
            logger.info(f"Loading conversation history for lead_id: {lead_id}")

            query = """
                SELECT m.id, m.content, m.timestamp, m.sender_type, m.message_type,
                       c.qualification_step, c.status, c.thread_id, m.metadata
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.lead_id = %s
                ORDER BY m.timestamp ASC
            """

            cursor = self.database.execute_query(query, (lead_id,))
            rows = cursor.fetchall()

            if not rows:
                logger.info(f"No conversation history found for lead_id: {lead_id}")
                return []

            messages = []
            for row in rows:
                message_data = {
                    "id": row[0],
                    "content": row[1],
                    "timestamp": row[2],
                    "sender_type": row[3],  # 'lead' or 'ai'
                    "message_type": row[4],  # 'email', 'text', etc.
                    "qualification_step": row[5],
                    "conversation_status": row[6],
                    "thread_id": row[7],
                    "metadata": json.loads(row[8]) if row[8] else {},
                }
                messages.append(message_data)

            logger.info(f"Loaded {len(messages)} messages for lead_id: {lead_id}")
            return messages

        except Exception as e:
            logger.error(
                f"Error loading conversation history for lead_id {lead_id}: {str(e)}"
            )
            raise Exception(f"Failed to load conversation history: {str(e)}")

    def get_conversation_context(self, lead_id: str) -> Dict[str, Any]:
        """
        Return comprehensive context for conversation including current qualification step,
        history, lead info, and context for generating next response.

        Args:
            lead_id: Unique identifier for the lead

        Returns:
            Dictionary containing full conversation context
        """
        try:
            logger.info(f"Getting conversation context for lead_id: {lead_id}")

            # Get lead information
            lead_info = self._get_lead_info(lead_id)
            if not lead_info:
                raise ValueError(f"Lead not found: {lead_id}")

            # Get conversation history
            conversation_history = self.load_conversation_history(lead_id)

            # Get current conversation record
            conversation_record = self._get_conversation_record(lead_id)

            # Determine current qualification step
            current_step = self._determine_current_qualification_step(
                conversation_history, conversation_record
            )

            # Get next qualification action
            next_action = self.get_next_qualification_step(lead_id)

            # Build context dictionary
            context = {
                "lead_id": lead_id,
                "lead_info": lead_info,
                "conversation_history": conversation_history,
                "current_qualification_step": current_step,
                "next_qualification_action": next_action,
                "conversation_status": (
                    conversation_record.get("status", "active")
                    if conversation_record
                    else "new"
                ),
                "thread_id": (
                    conversation_record.get("thread_id")
                    if conversation_record
                    else None
                ),
                "last_activity": (
                    conversation_history[-1]["timestamp"]
                    if conversation_history
                    else None
                ),
                "message_count": len(conversation_history),
                "qualification_progress": self._calculate_qualification_progress(
                    conversation_history
                ),
                "context_summary": self._generate_context_summary(
                    conversation_history, lead_info
                ),
            }

            logger.info(
                f"Generated context for lead_id {lead_id}: step={current_step}, status={context['conversation_status']}"
            )
            return context

        except Exception as e:
            logger.error(
                f"Error getting conversation context for lead_id {lead_id}: {str(e)}"
            )
            raise Exception(f"Failed to get conversation context: {str(e)}")

    def update_thread_id(self, lead_id: str, thread_id: str) -> bool:
        """
        Update database to map Gmail thread ID to lead conversation for tracking
        multi-message threads.

        Args:
            lead_id: Unique identifier for the lead
            thread_id: Gmail thread ID to associate

        Returns:
            Boolean indicating success
        """
        try:
            logger.info(
                f"Updating thread_id for lead_id: {lead_id}, thread_id: {thread_id}"
            )

            # Check if conversation exists
            conversation_id = self._get_or_create_conversation(lead_id)

            # Update thread_id
            update_query = """
                UPDATE conversations 
                SET thread_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """

            cursor = self.database.execute_query(
                update_query, (thread_id, conversation_id)
            )

            if cursor.rowcount == 0:
                logger.warning(
                    f"No conversation found to update for lead_id: {lead_id}"
                )
                return False

            self.database.commit()
            logger.info(f"Successfully updated thread_id for lead_id: {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating thread_id for lead_id {lead_id}: {str(e)}")
            self.database.rollback()
            return False

    def get_next_qualification_step(self, lead_id: str) -> Dict[str, Any]:
        """
        Analyze conversation history to determine next qualification question/action
        based on current state and qualification progress.

        Args:
            lead_id: Unique identifier for the lead

        Returns:
            Dictionary containing next step information and suggested action
        """
        try:
            logger.info(f"Determining next qualification step for lead_id: {lead_id}")

            conversation_history = self.load_conversation_history(lead_id)
            lead_info = self._get_lead_info(lead_id)

            if not lead_info:
                raise ValueError(f"Lead not found: {lead_id}")

            # Analyze current qualification state
            qualification_state = self._analyze_qualification_state(
                conversation_history
            )

            # Get next step from qualification manager
            next_step = self.qualification_manager.get_next_step(
                qualification_state=qualification_state,
                conversation_history=conversation_history,
                lead_info=lead_info,
            )

            logger.info(
                f"Next qualification step for lead_id {lead_id}: {next_step['step_name']}"
            )
            return next_step

        except Exception as e:
            logger.error(
                f"Error determining next qualification step for lead_id {lead_id}: {str(e)}"
            )
            raise Exception(f"Failed to determine next qualification step: {str(e)}")

    def add_message(
        self,
        lead_id: str,
        content: str,
        sender_type: str,
        message_type: str = "email",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add a new message to the conversation history.

        Args:
            lead_id: Unique identifier for the lead
            content: Message content
            sender_type: 'lead' or 'ai'
            message_type: Type of message ('email', 'text', etc.)
            metadata: Additional message metadata

        Returns:
            Message ID
        """
        try:
            logger.info(
                f"Adding message for lead_id: {lead_id}, sender_type: {sender_type}"
            )

            conversation_id = self._get_or_create_conversation(lead_id)

            insert_query = """
                INSERT INTO messages (conversation_id, content, sender_type, message_type, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """

            metadata_json = json.dumps(metadata) if metadata else None
            cursor = self.database.execute_query(
                insert_query,
                (conversation_id, content, sender_type, message_type, metadata_json),
            )

            message_id = cursor.fetchone()[0]

            # Update conversation timestamp and qualification step if needed
            self._update_conversation_after_message(conversation_id, sender_type)

            self.database.commit()
            logger.info(f"Added message with ID: {message_id}")
            return str(message_id)

        except Exception as e:
            logger.error(f"Error adding message for lead_id {lead_id}: {str(e)}")
            self.database.rollback()
            raise Exception(f"Failed to add message: {str(e)}")

    def update_conversation_status(self, lead_id: str, status: str) -> bool:
        """
        Update the status of a conversation.

        Args:
            lead_id: Unique identifier for the lead
            status: New status ('active', 'qualified', 'disqualified', 'closed')

        Returns:
            Boolean indicating success
        """
        try:
            logger.info(
                f"Updating conversation status for lead_id: {lead_id} to: {status}"
            )

            update_query = """
                UPDATE conversations 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE lead_id = %s
            """

            cursor = self.database.execute_query(update_query, (status, lead_id))

            if cursor.rowcount == 0:
                logger.warning(
                    f"No conversation found to update for lead_id: {lead_id}"
                )
                return False

            self.database.commit()
            logger.info(
                f"Successfully updated conversation status for lead_id: {lead_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error updating conversation status for lead_id {lead_id}: {str(e)}"
            )
            self.database.rollback()
            return False

    def _get_lead_info(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead information from database."""
        try:
            query = """
                SELECT id, email, phone, name, company, source, status, created_at, metadata
                FROM leads 
                WHERE id = %s
            """

            cursor = self.database.execute_query(query, (lead_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "email": row[1],
                "phone": row[2],
                "name": row[3],
                "company": row[4],
                "source": row[5],
                "status": row[6],
                "created_at": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
            }

        except Exception as e:
            logger.error(f"Error getting lead info for lead_id {lead_id}: {str(e)}")
            return None

    def _get_conversation_record(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation record from database."""
        try:
            query = """
                SELECT id, lead_id, status, qualification_step, thread_id, created_at, updated_at
                FROM conversations 
                WHERE lead_id = %s
            """

            cursor = self.database.execute_query(query, (lead_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "id": row[0],
                "lead_id": row[1],
                "status": row[2],
                "qualification_step": row[3],
                "thread_id": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }

        except Exception as e:
            logger.error(
                f"Error getting conversation record for lead_id {lead_id}: {str(e)}"
            )
            return None

    def _get_or_create_conversation(self, lead_id: str) -> str:
        """Get existing conversation ID or create new conversation."""
        try:
            # Check for existing conversation
            query = "SELECT id FROM conversations WHERE lead_id = %s"
            cursor = self.database.execute_query(query, (lead_id,))
            row = cursor.fetchone()

            if row:
                return str(row[0])

            # Create new conversation
            insert_query = """
                INSERT INTO conversations (lead_id, status, qualification_step, created_at, updated_at)
                VALUES (%s, 'active', 'initial_contact', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """

            cursor = self.database.execute_query(insert_query, (lead_id,))
            conversation_id = cursor.fetchone()[0]
            self.database.commit()

            logger.info(
                f"Created new conversation with ID: {conversation_id} for lead_id: {lead_id}"
            )
            return str(conversation_id)

        except Exception as e:
            logger.error(
                f"Error getting/creating conversation for lead_id {lead_id}: {str(e)}"
            )
            raise Exception(f"Failed to get or create conversation: {str(e)}")

    def _determine_current_qualification_step(
        self, conversation_history: List[Dict], conversation_record: Optional[Dict]
    ) -> str:
        """Determine current qualification step based on conversation history."""
        try:
            if not conversation_history:
                return "initial_contact"

            if conversation_record and conversation_record.get("qualification_step"):
                return conversation_record["qualification_step"]

            # Analyze conversation history to determine step
            return self.qualification_manager.analyze_current_step(conversation_history)

        except Exception as e:
            logger.error(f"Error determining current qualification step: {str(e)}")
            return "initial_contact"

    def _analyze_qualification_state(
        self, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze conversation history to determine qualification state."""
        try:
            if not conversation_history:
                return {
                    "step": "initial_contact",
                    "completed_steps": [],
                    "gathered_info": {},
                    "qualification_score": 0,
                    "needs_info": [],
                }

            return self.qualification_manager.analyze_qualification_state(
                conversation_history
            )

        except Exception as e:
            logger.error(f"Error analyzing qualification state: {str(e)}")
            return {
                "step": "initial_contact",
                "completed_steps": [],
                "gathered_info": {},
            }

    def _calculate_qualification_progress(
        self, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate qualification progress based on conversation history."""
        try:
            total_steps = self.qualification_manager.get_total_qualification_steps()
            completed_steps = self.qualification_manager.count_completed_steps(
                conversation_history
            )

            progress_percentage = (
                (completed_steps / total_steps) * 100 if total_steps > 0 else 0
            )

            return {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "progress_percentage": round(progress_percentage, 2),
                "remaining_steps": total_steps - completed_steps,
            }

        except Exception as e:
            logger.error(f"Error calculating qualification progress: {str(e)}")
            return {"total_steps": 0, "completed_steps": 0, "progress_percentage": 0}

    def _generate_context_summary(
        self, conversation_history: List[Dict], lead_info: Dict[str, Any]
    ) -> str:
        """Generate a summary of the conversation context for AI processing."""
        try:
            if not conversation_history:
                return f"New conversation with {lead_info.get('name', 'lead')} from {lead_info.get('company', 'unknown company')}"

            last_message = conversation_history[-1]
            message_count = len(conversation_history)

            summary = f"Ongoing conversation with {lead_info.get('name', 'lead')} "
            summary += f"from {lead_info.get('company', 'unknown company')}. "
            summary += f"Total messages: {message_count}. "
            summary += f"Last message from: {last_message['sender_type']} "
            summary += f"at {last_message['timestamp']}."

            return summary

        except Exception as e:
            logger.error(f"Error generating context summary: {str(e)}")
            return "Context summary unavailable"

    def _update_conversation_after_message(
        self, conversation_id: str, sender_type: str
    ):
        """Update conversation record after adding a message."""
        try:
            update_query = """
                UPDATE conversations 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """

            self.database.execute_query(update_query, (conversation_id,))

        except Exception as e:
            logger.error(f"Error updating conversation after message: {str(e)}")

    def get_active_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of active conversations with basic info."""
        try:
            query = """
                SELECT c.id, c.lead_id, c.status, c.qualification_step, c.updated_at,
                       l.name, l.email, l.company,
                       COUNT(m.id) as message_count
                FROM conversations c
                JOIN leads l ON c.lead_id = l.id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.status = 'active'
                GROUP BY c.id, l.id
                ORDER BY c.updated_at DESC
                LIMIT %s
            """

            cursor = self.database.execute_query(query, (limit,))
            rows = cursor.fetchall()

            conversations = []
            for row in rows:
                conversations.append(
                    {
                        "conversation_id": row[0],
                        "lead_id": row[1],
                        "status": row[2],
                        "qualification_step": row[3],
                        "updated_at": row[4],
                        "lead_name": row[5],
                        "lead_email": row[6],
                        "lead_company": row[7],
                        "message_count": row[8],
                    }
                )

            return conversations

        except Exception as e:
            logger.error(f"Error getting active conversations: {str(e)}")
            return []
