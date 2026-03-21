import logging
import time
import signal
import sys
from typing import Dict, List, Optional, Set
from datetime import datetime

from gmail_client import GmailClient
from claude_client import ClaudeClient
from email_client import EmailClient
from database import Database, Lead


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


class ClawContractor:
    def __init__(self):
        """Initialize the Claw Contractor lead qualification system."""
        self.running = False
        self.processed_message_ids: Set[str] = set()
        
        # Initialize clients
        try:
            self.gmail_client = GmailClient()
            self.claude_client = ClaudeClient()
            self.email_client = EmailClient()
            self.database = Database()
            
            logger.info("All clients initialized successfully")
            
            # Load previously processed message IDs from database
            self._load_processed_message_ids()
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            raise
    
    def _load_processed_message_ids(self):
        """Load processed message IDs from database to prevent reprocessing."""
        try:
            processed_ids = self.database.get_processed_message_ids()
            self.processed_message_ids.update(processed_ids)
            logger.info(f"Loaded {len(processed_ids)} processed message IDs")
        except Exception as e:
            logger.error(f"Failed to load processed message IDs: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Start the main processing loop."""
        logger.info("Starting Claw Contractor lead qualification system")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        
        while self.running:
            try:
                self._process_emails()
                
                if self.running:
                    logger.info("Sleeping for 60 seconds before next poll...")
                    time.sleep(60)
                    
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                if self.running:
                    time.sleep(30)  # Wait before retrying
        
        logger.info("Claw Contractor system shutdown complete")
    
    def _process_emails(self):
        """Process new emails from Gmail."""
        try:
            # Get new emails
            emails = self.gmail_client.get_new_emails()
            logger.info(f"Retrieved {len(emails)} emails")
            
            for email_data in emails:
                try:
                    if self._should_process_email(email_data):
                        self._process_single_email(email_data)
                    else:
                        logger.debug(f"Skipping already processed email: {email_data.get('id')}")
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_data.get('id')}: {e}", exc_info=True)
                    continue
                    
        except Exception as e:
            logger.error(f"Error retrieving emails: {e}", exc_info=True)
    
    def _should_process_email(self, email_data: Dict) -> bool:
        """Check if email should be processed (not already processed)."""
        message_id = email_data.get('id')
        if not message_id:
            return False
            
        return message_id not in self.processed_message_ids
    
    def _process_single_email(self, email_data: Dict):
        """Process a single email."""
        message_id = email_data.get('id')
        sender_email = email_data.get('sender_email', '').lower()
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        attachments = email_data.get('attachments', [])
        
        logger.info(f"Processing email from {sender_email} - Subject: {subject}")
        
        # Mark as processed first to avoid reprocessing
        self.processed_message_ids.add(message_id)
        self.database.mark_message_processed(message_id)
        
        # Check if this is from an existing lead
        existing_lead = self.database.get_lead_by_email(sender_email)
        
        if existing_lead:
            self._process_existing_lead_email(existing_lead, email_data)
        else:
            self._process_new_lead_email(email_data)
    
    def _process_new_lead_email(self, email_data: Dict):
        """Process email from a new lead."""
        sender_email = email_data.get('sender_email', '').lower()
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        attachments = email_data.get('attachments', [])
        
        logger.info(f"Processing new lead: {sender_email}")
        
        try:
            # Parse lead information using Claude
            lead_info = self.claude_client.parse_new_lead_email(
                sender_email=sender_email,
                subject=subject,
                body=body
            )
            
            # Process any photo attachments
            photo_analysis = None
            if attachments:
                photo_analysis = self._process_photo_attachments(attachments)
            
            # Create new lead record
            lead = Lead(
                email=sender_email,
                name=lead_info.get('name', ''),
                phone=lead_info.get('phone', ''),
                location=lead_info.get('location', ''),
                project_type=lead_info.get('project_type', ''),
                project_details=lead_info.get('project_details', ''),
                status='initial_contact',
                source='email',
                photo_analysis=photo_analysis
            )
            
            lead_id = self.database.create_lead(lead)
            logger.info(f"Created new lead with ID: {lead_id}")
            
            # Store conversation history
            self.database.add_conversation_entry(
                lead_id=lead_id,
                sender='lead',
                subject=subject,
                content=body,
                attachments=len(attachments)
            )
            
            # Send initial qualification message
            self._send_qualification_message(lead, 'initial_contact')
            
        except Exception as e:
            logger.error(f"Error processing new lead {sender_email}: {e}", exc_info=True)
    
    def _process_existing_lead_email(self, lead: Lead, email_data: Dict):
        """Process email from an existing lead."""
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        attachments = email_data.get('attachments', [])
        
        logger.info(f"Processing response from existing lead: {lead.email} (Status: {lead.status})")
        
        try:
            # Store conversation history
            self.database.add_conversation_entry(
                lead_id=lead.id,
                sender='lead',
                subject=subject,
                content=body,
                attachments=len(attachments)
            )
            
            # Process any new photo attachments
            if attachments:
                photo_analysis = self._process_photo_attachments(attachments)
                if photo_analysis:
                    # Update lead with new photo analysis
                    existing_analysis = lead.photo_analysis or {}
                    existing_analysis.update(photo_analysis)
                    self.database.update_lead_photo_analysis(lead.id, existing_analysis)
            
            # Analyze response and determine next action
            next_action = self.claude_client.analyze_lead_response(
                current_status=lead.status,
                email_content=body,
                lead_context=self._get_lead_context(lead)
            )
            
            # Update lead status based on analysis
            new_status = next_action.get('next_status', lead.status)
            if new_status != lead.status:
                self.database.update_lead_status(lead.id, new_status)
                lead.status = new_status
                logger.info(f"Updated lead {lead.email} status to: {new_status}")
            
            # Send appropriate follow-up message
            action_type = next_action.get('action_type', 'continue_qualification')
            if action_type in ['continue_qualification', 'request_info', 'schedule_call']:
                self._send_qualification_message(lead, new_status)
            elif action_type == 'qualified':
                self._handle_qualified_lead(lead)
            elif action_type == 'disqualified':
                self._handle_disqualified_lead(lead)
            
        except Exception as e:
            logger.error(f"Error processing existing lead {lead.email}: {e}", exc_info=True)
    
    def _process_photo_attachments(self, attachments: List[Dict]) -> Optional[Dict]:
        """Process photo attachments and return analysis."""
        if not attachments:
            return None
        
        photo_analyses = []
        
        for attachment in attachments:
            if attachment.get('content_type', '').startswith('image/'):
                try:
                    # Download and analyze photo
                    photo_data = self.gmail_client.download_attachment(attachment)
                    analysis = self.claude_client.analyze_trade_photo(photo_data)
                    
                    if analysis:
                        photo_analyses.append({
                            'filename': attachment.get('filename', 'unknown'),
                            'analysis': analysis,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing photo attachment {attachment.get('filename')}: {e}")
        
        if photo_analyses:
            return {'photos': photo_analyses}
        
        return None
    
    def _get_lead_context(self, lead: Lead) -> Dict:
        """Get context information about a lead for Claude analysis."""
        return {
            'name': lead.name,
            'phone': lead.phone,
            'location': lead.location,
            'project_type': lead.project_type,
            'project_details': lead.project_details,
            'photo_analysis': lead.photo_analysis,
            'conversation_history': self.database.get_conversation_history(lead.id)
        }
    
    def _send_qualification_message(self, lead: Lead, status: str):
        """Send appropriate qualification message based on lead status."""
        try:
            # Generate message content using Claude
            message_content = self.claude_client.generate_qualification_message(
                status=status,
                lead_context=self._get_lead_context(lead)
            )
            
            # Send email
            success = self.email_client.send_email(
                to_email=lead.email,
                to_name=lead.name,
                subject=message_content.get('subject', 'Re: Your Project Inquiry'),
                body=message_content.get('body', '')
            )
            
            if success:
                # Store sent message in conversation history
                self.database.add_conversation_entry(
                    lead_id=lead.id,
                    sender='system',
                    subject=message_content.get('subject', ''),
                    content=message_content.get('body', ''),
                    attachments=0
                )
                
                logger.info(f"Sent qualification message to {lead.email} for status: {status}")
            else:
                logger.error(f"Failed to send message to {lead.email}")
                
        except Exception as e:
            logger.error(f"Error sending qualification message to {lead.email}: {e}", exc_info=True)
    
    def _handle_qualified_lead(self, lead: Lead):
        """Handle a fully qualified lead."""
        try:
            logger.info(f"Lead {lead.email} is fully qualified!")
            
            # Update status to qualified
            self.database.update_lead_status(lead.id, 'qualified')
            
            # Generate final qualification message
            message_content = self.claude_client.generate_qualification_message(
                status='qualified',
                lead_context=self._get_lead_context(lead)
            )
            
            # Send final message
            self.email_client.send_email(
                to_email=lead.email,
                to_name=lead.name,
                subject=message_content.get('subject', 'Ready to Move Forward!'),
                body=message_content.get('body', '')
            )
            
            # Store sent message
            self.database.add_conversation_entry(
                lead_id=lead.id,
                sender='system',
                subject=message_content.get('subject', ''),
                content=message_content.get('body', ''),
                attachments=0
            )
            
        except Exception as e:
            logger.error(f"Error handling qualified lead {lead.email}: {e}", exc_info=True)
    
    def _handle_disqualified_lead(self, lead: Lead):
        """Handle a disqualified lead."""
        try:
            logger.info(f"Lead {lead.email} has been disqualified")
            
            # Update status to disqualified
            self.database.update_lead_status(lead.id, 'disqualified')
            
            # Optionally send polite closing message
            message_content = self.claude_client.generate_qualification_message(
                status='disqualified',
                lead_context=self._get_lead_context(lead)
            )
            
            if message_content.get('body'):  # Only send if Claude suggests a message
                self.email_client.send_email(
                    to_email=lead.email,
                    to_name=lead.name,
                    subject=message_content.get('subject', 'Thank you for your inquiry'),
                    body=message_content.get('body', '')
                )
                
                # Store sent message
                self.database.add_conversation_entry(
                    lead_id=lead.id,
                    sender='system',
                    subject=message_content.get('subject', ''),
                    content=message_content.get('body', ''),
                    attachments=0
                )
            
        except Exception as e:
            logger.error(f"Error handling disqualified lead {lead.email}: {e}", exc_info=True)


def main():
    """Main entry point."""
    try:
        contractor = ClawContractor()
        contractor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()