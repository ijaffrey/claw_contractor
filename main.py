#!/usr/bin/env python3
"""
Lead Management System - Main Entry Point
Automates lead processing from Gmail to contractor notifications
"""

import argparse
import logging
import signal
import sys
import time
from typing import Dict, Any, List

# Import required modules
import gmail_listener
import lead_parser
import lead_adapter
import database_manager
import qualified_lead_detector
import contractor_notifier
import reply_generator
import conversation_manager
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lead_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LeadManagementSystem:
    """Main system class for managing lead processing workflow"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.running = True
        self.poll_interval = 60  # seconds
        
        # Initialize modules
        self.gmail = gmail_listener
        self.parser = lead_parser
        self.adapter = lead_adapter
        self.db = database_manager
        self.detector = qualified_lead_detector
        self.notifier = contractor_notifier
        self.reply_gen = reply_generator
        
        # Initialize conversation manager
        self.conversation_manager = conversation_manager.ConversationManager()
        logger.info(f"System initialized {'in DRY RUN mode' if dry_run else ''}")
    
    def print_startup_banner(self):
        """Print system startup banner"""
        banner = """
╔════════════════════════════════════════════════════════════╗
║                 LEAD MANAGEMENT SYSTEM                     ║
║                      Version 1.0                          ║
╠════════════════════════════════════════════════════════════╣
║  🔄 Gmail Monitoring: ACTIVE                               ║
║  📊 Lead Processing: ENABLED                               ║
║  🤖 Auto Replies: ENABLED                                  ║
║  📞 Contractor Alerts: ENABLED                             ║
╚════════════════════════════════════════════════════════════╝
"""
        print(banner)
        if self.dry_run:
            print("⚠️  DRY RUN MODE ACTIVE - No emails sent, no database writes")
        print(f"🚀 System starting... Polling Gmail every {self.poll_interval} seconds")
        print("📧 Monitoring for new lead emails...")
        print("Press Ctrl+C to stop gracefully\n")
    
    def process_email(self, email_data: Dict[str, Any]) -> bool:
        """
        Process a single email through the complete workflow
        Returns True if processing was successful
        """
        try:
            email_id = email_data.get('id', 'unknown')
            subject = email_data.get('subject', 'No subject')
            sender = email_data.get('sender', 'Unknown sender')
            
            # Check if this is a conversation reply or new lead
            if self.is_conversation_reply(email_data):
                logger.info(f"Processing conversation reply from {sender}")
                self.log_conversation_state(sender, "processing_reply", {"email_id": email_id})
                
                if self.dry_run:
                    logger.info("[DRY RUN] Would route to conversation manager")
                    return True
                else:
                    return self.conversation_manager.process_reply(email_data)
            
            # This is a new lead - continue with existing flow
            logger.info(f"Processing new lead from {sender}")
            self.log_conversation_state(sender, "processing_new_lead", {"email_id": email_id})

            logger.info(f"Processing email {email_id}: {subject} from {sender}")
            
            # Step 1: Parse lead data from email
            if self.dry_run:
                logger.info("[DRY RUN] Would parse lead data from email")
                lead_data = {'name': 'Test Lead', 'email': sender, 'phone': '555-0123'}
            else:
                lead_data = self.parser.parse_lead(email_data)
            
            if not lead_data:
                logger.warning(f"Failed to parse lead data from email {email_id}")
                return False
            
            # Step 2: Normalize lead data
            if self.dry_run:
                logger.info("[DRY RUN] Would normalize lead data")
                normalized_lead = lead_data
            else:
                normalized_lead = self.adapter.normalize_lead(lead_data)
            
            # Step 3: Store lead in database
            if self.dry_run:
                logger.info("[DRY RUN] Would store lead in database")
                lead_id = "dry_run_lead_123"
            else:
                lead_id = self.db.store_lead(normalized_lead)
                logger.info(f"Stored lead with ID: {lead_id}")
            
            # Step 4: Generate and send qualifying reply
            if self.dry_run:
                logger.info("[DRY RUN] Would generate and send qualifying reply")
                reply_sent = True
            else:
                reply_content = self.reply_gen.generate_qualifying_questions(normalized_lead)
                reply_sent = self.reply_gen.send_reply(email_data, reply_content)
            
            if not reply_sent:
                logger.error(f"Failed to send reply for lead {lead_id}")
                return False
            
            logger.info(f"Sent qualifying reply for lead {lead_id}")
            
            # Step 5: Check lead qualification status
            conversation_state = self._get_conversation_state(lead_id, email_data)
            
            if self.dry_run:
                logger.info("[DRY RUN] Would analyze lead qualification")
                qualification_result = {
                    'is_ready_for_handoff': True,
                    'qualification_score': 85,
                    'missing_info': []
                }
            else:
                qualification_result = self.detector.analyze_lead_qualification(
                    normalized_lead, 
                    conversation_state
                )
            
            # Step 6: Notify contractors if lead is qualified
            if qualification_result.get('is_ready_for_handoff', False):
                if self.dry_run:
                    logger.info("[DRY RUN] Would notify contractors of qualified lead")
                else:
                    notification_sent = self.notifier.notify_qualified_lead(
                        normalized_lead, 
                        qualification_result
                    )
                    if notification_sent:
                        logger.info(f"Notified contractors about qualified lead {lead_id}")
                    else:
                        logger.error(f"Failed to notify contractors about lead {lead_id}")
            else:
                logger.info(f"Lead {lead_id} not yet ready for handoff (score: {qualification_result.get('qualification_score', 0)})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing email {email_id}: {str(e)}")
            return False
    
    def _get_conversation_state(self, lead_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation state for lead qualification analysis"""
        if self.dry_run:
            return {
                'thread_id': 'dry_run_thread_123',
                'message_count': 2,
                'last_response_time': time.time(),
                'responses': ['Initial inquiry', 'Follow-up response']
            }
        
        try:
            # Get conversation history from database or email thread
            thread_id = email_data.get('thread_id')
            if thread_id:
                return self.db.get_conversation_state(lead_id, thread_id)
            return {}
        except Exception as e:
            logger.warning(f"Could not retrieve conversation state: {str(e)}")
            return {}
    
    def run_polling_loop(self):
        """Main polling loop for processing emails"""
        logger.info("Starting main polling loop...")
        
        while self.running:
            try:
                # Poll for new emails
                if self.dry_run:
                    logger.debug("[DRY RUN] Would check Gmail for new emails")
                    # Simulate finding emails in dry run mode
                    new_emails = [
                        {
                            'id': 'dry_run_email_1',
                            'subject': 'Roofing Quote Request',
                            'sender': 'john.doe@email.com',
                            'thread_id': 'thread_123'
                        }
                    ] if time.time() % 300 < 60 else []  # Simulate email every 5 minutes
                else:
                    new_emails = self.gmail.get_new_emails()
                
                if new_emails:
                    logger.info(f"Found {len(new_emails)} new email(s)")
                    
                    # Process each email
                    processed_count = 0
                    for email_data in new_emails:
                        if self.process_email(email_data):
                            processed_count += 1
                    
                    logger.info(f"Successfully processed {processed_count}/{len(new_emails)} emails")
                else:
                    logger.debug("No new emails found")
                
                # Wait before next poll
                if self.running:
                    logger.debug(f"Waiting {self.poll_interval} seconds before next poll...")
                    time.sleep(self.poll_interval)
                    
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.shutdown()
                break
            except Exception as e:
                logger.error(f"Error in main polling loop: {str(e)}")
                logger.info(f"Continuing after error... Next poll in {self.poll_interval} seconds")
                time.sleep(self.poll_interval)
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Initiating graceful shutdown...")
        self.running = False
        
        try:
            # Close database connections
            if hasattr(self.db, 'close'):
                self.db.close()
                logger.info("Database connections closed")
                
            # Cleanup other resources
            logger.info("System shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    global lead_system
    if 'lead_system' in globals():
        lead_system.shutdown()
    sys.exit(0)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Lead Management System - Automated lead processing from Gmail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # Run in normal mode
  python main.py --dry-run     # Run in dry-run mode (no emails sent, no database writes)
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode - log actions without executing them'
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    global lead_system
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize the lead management system
        lead_system = LeadManagementSystem(dry_run=args.dry_run)
        
        # Print startup banner
        lead_system.print_startup_banner()
        
        # Start the main polling loop
        lead_system.run_polling_loop()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    def is_conversation_reply(self, email_data: Dict[str, Any]) -> bool:
        """
        Determine if email is a reply to an existing conversation or a new lead.
        Checks for Re:, thread_id, or existing conversation in database.
        """
        subject = email_data.get('subject', '').lower()
        sender_email = email_data.get('sender', '')
        
        # Check for reply indicators in subject
        if subject.startswith('re:') or subject.startswith('fwd:'):
            self.log_conversation_state(sender_email, 'reply_detected', {'method': 'subject_prefix'})
            return True
            
        # Check if sender has existing conversation in database
        if not self.dry_run:
            try:
                # Use database manager to check for existing lead
                existing_leads = self.db.get_leads_by_email(sender_email)
                if existing_leads:
                    self.log_conversation_state(sender_email, 'existing_lead_found', {'lead_count': len(existing_leads)})
                    return True
            except Exception as e:
                logger.warning(f"Error checking existing conversations: {e}")
                
        return False
    
    def log_conversation_state(self, email: str, state: str, details: Dict[str, Any] = None) -> None:
        """
        Log conversation state transitions with timestamps.
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'email': email,
            'state': state,
            'details': details or {}
        }
        logger.info(f"Conversation state transition: {log_entry}")
        
        # Store in database for persistence if not in dry run mode
        if not self.dry_run:
            try:
                # Store conversation state log in database
                self.db.store_conversation_log(log_entry)
            except Exception as e:
                logger.warning(f"Failed to store conversation log: {e}")