import time
import logging
import traceback
import sys
from datetime import datetime
from typing import Set, Dict, Any, Optional, List

from gmail_listener import GmailListener
from lead_parser import LeadParser
from database import Database
from reply_generator import ReplyGenerator
from email_sender import EmailSender
from conversation_manager import ConversationManager
from photo_analyzer import PhotoAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claw_contractor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ClawContractorOrchestrator:
    def __init__(self):
        """Initialize all components and processed message tracking."""
        self.processed_message_ids: Set[str] = set()
        self.gmail_listener = None
        self.lead_parser = None
        self.database = None
        self.reply_generator = None
        self.email_sender = None
        self.conversation_manager = None
        self.photo_analyzer = None
        self.error_count = 0
        self.max_consecutive_errors = 5
        
    def initialize_components(self):
        """Initialize all system components with error handling."""
        try:
            logger.info("Initializing system components...")
            
            self.gmail_listener = GmailListener()
            self.lead_parser = LeadParser()
            self.database = Database()
            self.reply_generator = ReplyGenerator()
            self.email_sender = EmailSender()
            self.conversation_manager = ConversationManager()
            self.photo_analyzer = PhotoAnalyzer()
            
            # Load previously processed message IDs from database
            self.load_processed_message_ids()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def load_processed_message_ids(self):
        """Load processed message IDs from database to prevent reprocessing."""
        try:
            processed_ids = self.database.get_processed_message_ids()
            self.processed_message_ids.update(processed_ids)
            logger.info(f"Loaded {len(processed_ids)} processed message IDs from database")
        except Exception as e:
            logger.warning(f"Could not load processed message IDs: {str(e)}")
    
    def calculate_backoff_delay(self, error_count: int) -> int:
        """Calculate exponential backoff delay for API failures."""
        base_delay = 60
        max_delay = 600  # 10 minutes maximum
        delay = min(base_delay * (2 ** error_count), max_delay)
        return delay
    
    def poll_emails(self) -> List[Dict[str, Any]]:
        """Poll Gmail for new emails with error handling."""
        try:
            logger.info("Polling Gmail for new emails...")
            emails = self.gmail_listener.get_new_emails()
            
            # Filter out already processed emails
            new_emails = []
            for email in emails:
                message_id = email.get('message_id')
                if message_id and message_id not in self.processed_message_ids:
                    new_emails.append(email)
                else:
                    logger.debug(f"Skipping already processed email: {message_id}")
            
            logger.info(f"Found {len(new_emails)} new emails to process")
            return new_emails
            
        except Exception as e:
            logger.error(f"Failed to poll emails: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def is_existing_lead(self, sender_email: str) -> Optional[Dict[str, Any]]:
        """Check if email sender is an existing lead."""
        try:
            return self.database.get_lead_by_email(sender_email)
        except Exception as e:
            logger.error(f"Error checking existing lead for {sender_email}: {str(e)}")
            return None
    
    def process_new_lead(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process email from new lead - parse and store lead information."""
        try:
            logger.info(f"Processing new lead from: {email.get('sender_email')}")
            
            # Parse lead information from email
            lead_data = self.lead_parser.parse_lead_from_email(email)
            
            if not lead_data:
                logger.warning(f"Could not parse lead data from email: {email.get('message_id')}")
                return None
            
            # Store new lead in database
            lead_id = self.database.create_lead(lead_data)
            lead_data['id'] = lead_id
            lead_data['status'] = 'new'
            
            logger.info(f"Created new lead with ID: {lead_id}")
            return lead_data
            
        except Exception as e:
            logger.error(f"Error processing new lead: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def process_photo_attachments(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Process photo attachments and return analysis results."""
        analysis_results = {}
        
        try:
            attachments = email.get('attachments', [])
            photo_attachments = [att for att in attachments if att.get('is_image', False)]
            
            if photo_attachments:
                logger.info(f"Processing {len(photo_attachments)} photo attachments")
                
                for i, attachment in enumerate(photo_attachments):
                    try:
                        analysis = self.photo_analyzer.analyze_trade_photo(attachment)
                        analysis_results[f'photo_{i+1}'] = analysis
                        logger.info(f"Successfully analyzed photo attachment {i+1}")
                    except Exception as e:
                        logger.error(f"Failed to analyze photo attachment {i+1}: {str(e)}")
                        analysis_results[f'photo_{i+1}'] = {'error': str(e)}
            
        except Exception as e:
            logger.error(f"Error processing photo attachments: {str(e)}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def determine_conversation_step(self, lead: Dict[str, Any], email: Dict[str, Any]) -> Dict[str, Any]:
        """Determine current conversation step and next action."""
        try:
            return self.conversation_manager.get_next_step(lead, email)
        except Exception as e:
            logger.error(f"Error determining conversation step: {str(e)}")
            return {
                'step': 'initial_contact',
                'action': 'send_greeting',
                'message': 'Error determining conversation step'
            }
    
    def generate_and_send_response(self, lead: Dict[str, Any], email: Dict[str, Any], 
                                 conversation_step: Dict[str, Any], 
                                 photo_analysis: Dict[str, Any]) -> bool:
        """Generate appropriate response and send it."""
        try:
            logger.info(f"Generating response for lead {lead.get('id')} at step {conversation_step.get('step')}")
            
            # Generate response based on conversation step and context
            response_data = self.reply_generator.generate_response(
                lead=lead,
                email=email,
                conversation_step=conversation_step,
                photo_analysis=photo_analysis
            )
            
            if not response_data:
                logger.error("Failed to generate response")
                return False
            
            # Send the response
            success = self.email_sender.send_response(
                to_email=lead['email'],
                subject=response_data['subject'],
                body=response_data['body'],
                reply_to_message_id=email.get('message_id')
            )
            
            if success:
                logger.info(f"Successfully sent response to {lead['email']}")
                return True
            else:
                logger.error(f"Failed to send response to {lead['email']}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating/sending response: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def update_lead_status(self, lead: Dict[str, Any], conversation_step: Dict[str, Any], 
                          email: Dict[str, Any], response_sent: bool):
        """Update lead status and log interaction."""
        try:
            # Update lead status in database
            new_status = conversation_step.get('next_status', lead.get('status'))
            self.database.update_lead_status(lead['id'], new_status)
            
            # Log the interaction
            interaction_data = {
                'lead_id': lead['id'],
                'email_message_id': email.get('message_id'),
                'conversation_step': conversation_step.get('step'),
                'response_sent': response_sent,
                'timestamp': datetime.now().isoformat()
            }
            
            self.database.log_interaction(interaction_data)
            
            logger.info(f"Updated lead {lead['id']} status to {new_status}")
            
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            logger.error(traceback.format_exc())
    
    def mark_email_processed(self, message_id: str):
        """Mark email as processed to prevent reprocessing."""
        try:
            self.processed_message_ids.add(message_id)
            self.database.mark_message_processed(message_id)
        except Exception as e:
            logger.error(f"Error marking email as processed: {str(e)}")
    
    def process_single_email(self, email: Dict[str, Any]) -> bool:
        """Process a single email through the complete workflow."""
        message_id = email.get('message_id')
        sender_email = email.get('sender_email')
        
        try:
            logger.info(f"Processing email {message_id} from {sender_email}")
            
            # Check if sender is existing lead
            existing_lead = self.is_existing_lead(sender_email)
            
            if existing_lead:
                logger.info(f"Email from existing lead: {existing_lead['id']}")
                lead = existing_lead
            else:
                logger.info("Email from new potential lead")
                lead = self.process_new_lead(email)
                if not lead:
                    logger.warning("Could not process as new lead, skipping")
                    return False
            
            # Process photo attachments if present
            photo_analysis = self.process_photo_attachments(email)
            
            # Determine conversation step
            conversation_step = self.determine_conversation_step(lead, email)
            
            # Generate and send response
            response_sent = self.generate_and_send_response(
                lead, email, conversation_step, photo_analysis
            )
            
            # Update lead status and log interaction
            self.update_lead_status(lead, conversation_step, email, response_sent)
            
            # Mark email as processed
            self.mark_email_processed(message_id)
            
            logger.info(f"Successfully processed email {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing email {message_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run_processing_cycle(self):
        """Run one complete email processing cycle."""
        try:
            # Poll for new emails
            new_emails = self.poll_emails()
            
            if not new_emails:
                logger.debug("No new emails to process")
                return True
            
            # Process each new email
            processed_count = 0
            failed_count = 0
            
            for email in new_emails:
                try:
                    if self.process_single_email(email):
                        processed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process email: {str(e)}")
                    failed_count += 1
            
            logger.info(f"Processing cycle complete: {processed_count} successful, {failed_count} failed")
            
            # Reset error count on successful cycle
            self.error_count = 0
            return True
            
        except Exception as e:
            logger.error(f"Error in processing cycle: {str(e)}")
            logger.error(traceback.format_exc())
            self.error_count += 1
            return False
    
    def run(self):
        """Main orchestration loop."""
        logger.info("Starting Claw Contractor email monitoring system...")
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components, exiting")
            return
        
        logger.info("Email monitoring system started successfully")
        
        try:
            while True:
                try:
                    # Check for too many consecutive errors
                    if self.error_count >= self.max_consecutive_errors:
                        backoff_delay = self.calculate_backoff_delay(self.error_count - self.max_consecutive_errors)
                        logger.warning(f"Too many consecutive errors ({self.error_count}), backing off for {backoff_delay} seconds")
                        time.sleep(backoff_delay)
                    
                    # Run processing cycle
                    self.run_processing_cycle()
                    
                    # Wait before next poll
                    logger.debug("Waiting 60 seconds before next poll...")
                    time.sleep(60)
                    
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt, shutting down gracefully...")
                    break
                    
                except Exception as e:
                    logger.error(f"Unexpected error in main loop: {str(e)}")
                    logger.error(traceback.format_exc())
                    self.error_count += 1
                    
                    # Continue after brief delay
                    time.sleep(10)
        
        except Exception as e:
            logger.error(f"Fatal error in main loop: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            logger.info("Email monitoring system shutdown complete")

def main():
    """Entry point for the application."""
    orchestrator = ClawContractorOrchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()