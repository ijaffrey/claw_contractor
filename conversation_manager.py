from database_manager import DatabaseManager


class ConversationManager:
    """Manages conversation history and context for leads."""
    
    def __init__(self):
        """Initialize the ConversationManager."""
        pass
    
    def load_conversation_history(self, lead_id):
        """
        Load conversation history for a given lead ID.
        
        Args:
            lead_id (int): The lead ID to load conversation history for
            
        Returns:
            list: List of conversation messages or empty list if none found
        """
        try:
            if not lead_id:
                return []
            
            history = get_conversation_history(lead_id)
            return history if history is not None else []
        except Exception as e:
            print(f"Error loading conversation history for lead {lead_id}: {e}")
            return []
    
    def get_conversation_context(self, lead_id):
        """
        Get conversation context for a lead including history and lead details.
        
        Args:
            lead_id (int): The lead ID to get context for
            
        Returns:
            dict: Dictionary containing conversation context or None if error
        """
        try:
            if not lead_id:
                return None
            
            # Get conversation history
            history = self.load_conversation_history(lead_id)
            
            # Get lead details by using conversation history to find thread_id
            lead_details = None
            if history:
                # Try to get lead details if we have history
                for message in history:
                    if hasattr(message, 'get') and message.get('thread_id'):
                        lead_details = get_lead_by_thread_id(message['thread_id'])
                        break
            
            context = {
                'lead_id': lead_id,
                'conversation_history': history,
                'lead_details': lead_details,
                'message_count': len(history)
            }
            
            return context
        except Exception as e:
            print(f"Error getting conversation context for lead {lead_id}: {e}")
            return None
    
    def update_thread_id(self, lead_id, thread_id):
        """
        Update thread ID for a lead by inserting a system message.
        
        Args:
            lead_id (int): The lead ID to update
            thread_id (str): The thread ID to associate with the lead
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not lead_id or not thread_id:
                return False
            
            # Insert a system message to associate the thread_id with the lead
            success = insert_conversation_message(
                lead_id=lead_id,
                message="Thread initialized",
                sender="system",
                thread_id=thread_id
            )
            
            return bool(success)
        except Exception as e:
            print(f"Error updating thread ID for lead {lead_id}: {e}")
            return False