import logging
import time
import signal
import sys
from datetime import datetime, timedelta
from typing import Set, Dict, List, Optional
import threading
from contextlib import contextmanager

from gmail_client import GmailClient
from lead_parser import LeadParser
from database import DatabaseManager
from photo_processor import PhotoProcessor
from qualification_messages import QualificationMessages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class EmailMonitor:
    """
    Main email monitoring and lead qualification system.
    """
    
    def __init__(self):
        self.running = False
        self.processed_emails: Set[str] = set()
        self.gmail_client = None
        self.lead_parser = None
        self.db_manager = None
        self.photo_processor = None
        self.qualification_messages = None
        self.poll_interval = 60  # seconds
        self.last_processed_time = datetime.utcnow() - timedelta(hours=1)
        self.shutdown_event = threading.Event()
        
    def initialize_components(self):
        """Initialize all system components with error handling."""
        try:
            logger.info("Initializing system components...")
            
            # Initialize Gmail client
            self.gmail_client = GmailClient()
            logger.info("Gmail client initialized successfully")
            
            # Initialize lead parser
            self.lead_parser = LeadParser()
            logger.info("Lead parser initialized successfully")
            
            # Initialize database manager
            self.db_manager = DatabaseManager()
            self.db_manager.create_tables()
            logger.info("Database manager initialized successfully")
            
            # Initialize photo processor
            self.photo_processor = PhotoProcessor()
            logger.info("Photo processor initialized successfully")
            
            # Initialize qualification messages
            self.qualification_messages = QualificationMessages()
            logger.info("Qualification messages initialized successfully")
            
            # Load previously processed email IDs
            self._load_processed_emails()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            return False
    
    def _load_processed_emails(self):
        """Load previously processed email IDs from database to prevent reprocessing."""
        try:
            processed_ids = self.db_manager.get_processed_email_ids()
            self.processed_emails.update(processed_ids)
            logger.info(f"Loaded {len(processed_ids)} previously processed email IDs")
        except Exception as e:
            logger.warning(f"Could not load processed email IDs: {str(e)}")
            self.processed_emails = set()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
            self.shutdown_event.set()
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @contextmanager
    def error_handling(self, operation_name: str):
        """Context manager for consistent error handling."""
        try:
            yield
        except Exception as e:
            logger.error(f"Error in {operation_name}: {str(e)}", exc_info=True)
            # Don't re-raise to allow the main loop to continue
    
    def fetch_new_emails(self) -> List[Dict]:
        """Fetch new emails from Gmail."""
        try:
            emails = self.gmail_client.get_recent_emails(
                since=self.last_processed_time,
                max_results=50
            )
            
            # Filter out already processed emails
            new_emails = [
                email for email in emails 
                if email['id'] not in self.processed_emails
            ]
            
            logger.info(f"Found {len(emails)} recent emails, {len(new_emails)} new")
            return new_emails
            
        except Exception as e:
            logger.error(f"Failed to fetch emails: {str(e)}")
            return []
    
    def process_email(self, email: Dict) -> bool:
        """Process a single email through the complete workflow."""
        email_id = email['id']
        sender_email = email.get('sender', '')
        
        try:
            logger.info(f"Processing email {email_id} from {sender_email}")
            
            # Check if lead already exists
            existing_lead = self.db_manager.get_lead_by_email(sender_email)
            
            if existing_lead:
                # Update existing lead conversation
                success = self._handle_existing_lead(email, existing_lead)
            else:
                # Parse and create new lead
                success = self._handle_new_lead(email)
            
            if success:
                # Mark email as processed
                self.processed_emails.add(email_id)
                self.db_manager.mark_email_processed(email_id)
                logger.info(f"Successfully processed email {email_id}")
                return True
            else:
                logger.warning(f"Failed to process email {email_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing email {email_id}: {str(e)}", exc_info=True)
            return False
    
    def _handle_new_lead(self, email: Dict) -> bool:
        """Handle processing of email from new lead."""
        try:
            # Parse lead information
            lead_data = self.lead_parser.parse_email(email)
            if not lead_data:
                logger.warning(f"Could not parse lead data from email {email['id']}")
                return False
            
            # Check for photo attachments
            photos = self._process_attachments(email)
            if photos:
                lead_data['photos'] = photos
                lead_data['has_photos'] = True
            
            # Determine initial qualification step
            qualification_step = self._determine_initial_step(lead_data)
            lead_data['qualification_step'] = qualification_step
            lead_data['status'] = 'active'
            lead_data['created_at'] = datetime.utcnow()
            lead_data['updated_at'] = datetime.utcnow()
            
            # Store lead in database
            lead_id = self.db_manager.create_lead(lead_data)
            if not lead_id:
                logger.error(f"Failed to create lead for email {email['id']}")
                return False
            
            # Send appropriate qualification message
            response_sent = self._send_qualification_response(
                email['sender'], 
                qualification_step, 
                lead_data
            )
            
            if response_sent:
                # Update lead status
                self.db_manager.update_lead_status(
                    lead_id, 
                    'awaiting_response', 
                    f"Sent {qualification_step} message"
                )
            
            logger.info(f"Created new lead {lead_id} with step {qualification_step}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling new lead: {str(e)}", exc_info=True)
            return False
    
    def _handle_existing_lead(self, email: Dict, existing_lead: Dict) -> bool:
        """Handle processing of email from existing lead."""
        try:
            lead_id = existing_lead['id']
            current_step = existing_lead.get('qualification_step', 'initial_contact')
            
            # Process any new attachments
            photos = self._process_attachments(email)
            if photos:
                self.db_manager.add_lead_photos(lead_id, photos)
            
            # Parse email content for updated information
            updated_data = self.lead_parser.parse_email(email)
            if updated_data:
                # Update lead with new information
                updated_data['updated_at'] = datetime.utcnow()
                self.db_manager.update_lead(lead_id, updated_data)
            
            # Determine next qualification step
            next_step = self._determine_next_step(existing_lead, email)
            
            if next_step != current_step:
                # Send appropriate response for next step
                response_sent = self._send_qualification_response(
                    email['sender'], 
                    next_step, 
                    existing_lead
                )
                
                if response_sent:
                    # Update lead qualification step and status
                    self.db_manager.update_lead_qualification_step(
                        lead_id, 
                        next_step
                    )
                    self.db_manager.update_lead_status(
                        lead_id, 
                        'awaiting_response', 
                        f"Advanced to {next_step}"
                    )
                    logger.info(f"Advanced lead {lead_id} to step {next_step}")
            else:
                # Update last contact time
                self.db_manager.update_lead_status(
                    lead_id, 
                    existing_lead.get('status', 'active'), 
                    "Received follow-up email"
                )
                logger.info(f"Updated existing lead {lead_id} contact time")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling existing lead: {str(e)}", exc_info=True)
            return False
    
    def _process_attachments(self, email: Dict) -> List[str]:
        """Process photo attachments from email."""
        try:
            attachments = email.get('attachments', [])
            if not attachments:
                return []
            
            processed_photos = []
            for attachment in attachments:
                if self.photo_processor.is_photo(attachment.get('filename', '')):
                    # Download and process photo
                    photo_data = self.gmail_client.get_attachment(
                        email['id'], 
                        attachment['attachment_id']
                    )
                    
                    if photo_data:
                        # Process and save photo
                        photo_path = self.photo_processor.process_photo(
                            photo_data, 
                            attachment['filename']
                        )
                        if photo_path:
                            processed_photos.append(photo_path)
            
            if processed_photos:
                logger.info(f"Processed {len(processed_photos)} photos from email {email['id']}")
            
            return processed_photos
            
        except Exception as e:
            logger.error(f"Error processing attachments: {str(e)}")
            return []
    
    def _determine_initial_step(self, lead_data: Dict) -> str:
        """Determine initial qualification step for new lead."""
        # Check if lead provided key information upfront
        if lead_data.get('budget') and lead_data.get('timeline'):
            return 'technical_requirements'
        elif lead_data.get('project_type'):
            return 'budget_timeline'
        else:
            return 'initial_contact'
    
    def _determine_next_step(self, existing_lead: Dict, email: Dict) -> str:
        """Determine next qualification step based on current state and email content."""
        current_step = existing_lead.get('qualification_step', 'initial_contact')
        
        # Parse email for qualification indicators
        email_content = email.get('body', '').lower()
        
        # Define step progression logic
        step_progression = {
            'initial_contact': 'budget_timeline',
            'budget_timeline': 'technical_requirements', 
            'technical_requirements': 'proposal_preparation',
            'proposal_preparation': 'contract_discussion',
            'contract_discussion': 'project_start'
        }
        
        # Check if lead provided information that allows skipping steps
        if current_step == 'initial_contact':
            if any(word in email_content for word in ['budget', '$', 'cost', 'price']):
                if any(word in email_content for word in ['timeline', 'when', 'deadline']):
                    return 'technical_requirements'
                return 'budget_timeline'
        
        elif current_step == 'budget_timeline':
            if any(word in email_content for word in ['technical', 'requirements', 'features']):
                return 'technical_requirements'
        
        # Default progression
        return step_progression.get(current_step, current_step)
    
    def _send_qualification_response(self, recipient: str, step: str, lead_data: Dict) -> bool:
        """Send appropriate qualification response email."""
        try:
            message = self.qualification_messages.get_message(step, lead_data)
            if not message:
                logger.warning(f"No message template found for step {step}")
                return False
            
            success = self.gmail_client.send_email(
                to=recipient,
                subject=message['subject'],
                body=message['body']
            )
            
            if success:
                logger.info(f"Sent {step} message to {recipient}")
            else:
                logger.error(f"Failed to send {step} message to {recipient}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending qualification response: {str(e)}")
            return False
    
    def cleanup_old_data(self):
        """Perform periodic cleanup of old data."""
        try:
            # Clean up old processed email records (older than 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cleaned = self.db_manager.cleanup_old_processed_emails(cutoff_date)
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old processed email records")
            
            # Clean up temporary photo files
            self.photo_processor.cleanup_temp_files()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def health_check(self) -> bool:
        """Perform system health check."""
        try:
            # Check Gmail connection
            if not self.gmail_client.test_connection():
                logger.error("Gmail connection health check failed")
                return False
            
            # Check database connection
            if not self.db_manager.test_connection():
                logger.error("Database connection health check failed")
                return False
            
            logger.info("System health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle."""
        cycle_start = time.time()
        
        with self.error_handling("monitoring cycle"):
            # Fetch new emails
            new_emails = self.fetch_new_emails()
            
            # Process each email
            processed_count = 0
            for email in new_emails:
                if self.shutdown_event.is_set():
                    logger.info("Shutdown requested, stopping email processing")
                    break
                
                if self.process_email(email):
                    processed_count += 1
            
            # Update last processed time
            if new_emails:
                self.last_processed_time = datetime.utcnow()
            
            # Log cycle statistics
            cycle_duration = time.time() - cycle_start
            logger.info(
                f"Monitoring cycle completed: "
                f"processed {processed_count}/{len(new_emails)} emails "
                f"in {cycle_duration:.2f}s"
            )
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting email monitoring system...")
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize system components")
            return False
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        self.running = True
        cycle_count = 0
        last_health_check = time.time()
        last_cleanup = time.time()
        
        logger.info("Email monitoring system started successfully")
        
        try:
            while self.running and not self.shutdown_event.is_set():
                cycle_count += 1
                
                try:
                    # Run monitoring cycle
                    self.run_monitoring_cycle()
                    
                    # Periodic health checks (every 10 minutes)
                    if time.time() - last_health_check > 600:
                        if not self.health_check():
                            logger.warning("Health check failed, continuing monitoring")
                        last_health_check = time.time()
                    
                    # Periodic cleanup (every hour)
                    if time.time() - last_cleanup > 3600:
                        self.cleanup_old_data()
                        last_cleanup = time.time()
                    
                    # Wait for next cycle or shutdown
                    if not self.shutdown_event.wait(timeout=self.poll_interval):
                        continue  # Timeout occurred, continue monitoring
                    else:
                        break  # Shutdown event was set
                        
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in monitoring loop: {str(e)}", exc_info=True)
                    # Sleep before retrying to avoid rapid failure loops
                    time.sleep(30)
        
        finally:
            logger.info("Shutting down email monitoring system...")
            self.running = False
            
            # Close connections
            if self.gmail_client:
                self.gmail_client.close()
            if self.db_manager:
                self.db_manager.close()
            
            logger.info(f"Email monitoring system shut down after {cycle_count} cycles")
        
        return True


def main():
    """Main entry point."""
    logger.info("Email monitoring system starting up...")
    
    monitor = EmailMonitor()
    
    try:
        success = monitor.run()
        if success:
            logger.info("Email monitoring system completed successfully")
            return 0
        else:
            logger.error("Email monitoring system failed to start")
            return 1
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())