import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple
import hashlib
import json
import re
from dataclasses import dataclass

from database import DatabaseManager, Lead, Message, LeadStatus
from gmail_client import GmailClient, EmailMessage
from claude_client import ClaudeClient
from qualification import QualificationManager, QualificationStep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contractor_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ProcessedMessage:
    """Represents a processed email message"""
    message_id: str
    sender_email: str
    subject: str
    content: str
    timestamp: datetime
    attachments: List[str]
    thread_id: str

class EmailProcessor:
    """Main email processing engine"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.gmail_client = GmailClient()
        self.claude_client = ClaudeClient()
        self.qualification_manager = QualificationManager()
        
        # Message deduplication tracking
        self.processed_messages: Set[str] = set()
        self.last_poll_time: Optional[datetime] = None
        
        # System state
        self.running = False
        self.poll_interval = 60  # seconds
        
        # Load previously processed messages
        self._load_processed_messages()
        
    def _load_processed_messages(self):
        """Load previously processed message IDs from database"""
        try:
            # Get all message IDs from the last 30 days to avoid reprocessing
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            messages = self.db.get_messages_since(cutoff_date)
            self.processed_messages = {msg.gmail_message_id for msg in messages if msg.gmail_message_id}
            logger.info(f"Loaded {len(self.processed_messages)} previously processed messages")
        except Exception as e:
            logger.error(f"Error loading processed messages: {e}")
            self.processed_messages = set()
    
    async def start(self):
        """Start the email processing system"""
        logger.info("Starting contractor lead system...")
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Initialize connections
            await self._initialize_connections()
            
            # Main processing loop
            while self.running:
                try:
                    await self._process_emails()
                    await asyncio.sleep(self.poll_interval)
                except Exception as e:
                    logger.error(f"Error in main processing loop: {e}", exc_info=True)
                    await asyncio.sleep(30)  # Short delay before retry
                    
        except Exception as e:
            logger.critical(f"Critical error in main loop: {e}", exc_info=True)
        finally:
            await self._cleanup()
    
    async def _initialize_connections(self):
        """Initialize all external connections"""
        try:
            # Initialize database
            self.db.initialize_tables()
            logger.info("Database initialized")
            
            # Test Gmail connection
            await self.gmail_client.authenticate()
            logger.info("Gmail client authenticated")
            
            # Test Claude connection
            await self.claude_client.test_connection()
            logger.info("Claude client connected")
            
        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise
    
    async def _process_emails(self):
        """Main email processing logic"""
        try:
            # Get new emails since last poll
            emails = await self._get_new_emails()
            
            if not emails:
                logger.debug("No new emails to process")
                return
                
            logger.info(f"Processing {len(emails)} new emails")
            
            for email in emails:
                try:
                    await self._process_single_email(email)
                except Exception as e:
                    logger.error(f"Error processing email {email.message_id}: {e}", exc_info=True)
                    continue
                    
            # Update last poll time
            self.last_poll_time = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error in email processing: {e}", exc_info=True)
    
    async def _get_new_emails(self) -> List[EmailMessage]:
        """Retrieve new emails from Gmail"""
        try:
            # Calculate search timeframe
            if self.last_poll_time:
                since_date = self.last_poll_time - timedelta(minutes=5)  # 5-minute overlap
            else:
                since_date = datetime.utcnow() - timedelta(hours=24)  # Start with last 24 hours
            
            # Get emails from Gmail
            emails = await self.gmail_client.get_emails_since(since_date)
            
            # Filter out already processed messages
            new_emails = [
                email for email in emails 
                if email.message_id not in self.processed_messages
            ]
            
            logger.info(f"Retrieved {len(emails)} emails, {len(new_emails)} are new")
            return new_emails
            
        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            return []
    
    async def _process_single_email(self, email: EmailMessage):
        """Process a single email message"""
        logger.info(f"Processing email from {email.sender_email}: {email.subject}")
        
        try:
            # Mark as processed immediately to avoid duplicates
            self.processed_messages.add(email.message_id)
            
            # Convert to ProcessedMessage
            processed_msg = ProcessedMessage(
                message_id=email.message_id,
                sender_email=email.sender_email.lower().strip(),
                subject=email.subject,
                content=email.content,
                timestamp=email.timestamp,
                attachments=email.attachments,
                thread_id=email.thread_id
            )
            
            # Check if this is a new lead or existing conversation
            existing_lead = await self._find_existing_lead(processed_msg)
            
            if existing_lead:
                await self._handle_existing_lead(existing_lead, processed_msg)
            else:
                await self._handle_new_lead(processed_msg)
                
        except Exception as e:
            logger.error(f"Error processing email {email.message_id}: {e}", exc_info=True)
            # Remove from processed set so it can be retried
            self.processed_messages.discard(email.message_id)
            raise
    
    async def _find_existing_lead(self, message: ProcessedMessage) -> Optional[Lead]:
        """Find existing lead based on sender email and thread context"""
        try:
            # First, try to find by email address
            lead = self.db.get_lead_by_email(message.sender_email)
            
            if lead:
                logger.debug(f"Found existing lead by email: {lead.id}")
                return lead
            
            # If no direct match, check for thread-based conversations
            if message.thread_id:
                # Look for any lead that has messages in this thread
                thread_lead = self.db.get_lead_by_thread_id(message.thread_id)
                if thread_lead:
                    logger.debug(f"Found existing lead by thread ID: {thread_lead.id}")
                    return thread_lead
            
            # Check for similar email domains (same company)
            domain = message.sender_email.split('@')[1] if '@' in message.sender_email else None
            if domain and not domain.endswith(('.gmail.com', '.yahoo.com', '.hotmail.com', '.outlook.com')):
                domain_leads = self.db.get_leads_by_domain(domain)
                if domain_leads:
                    logger.debug(f"Found potential company match by domain: {domain}")
                    # Return the most recent lead from this domain
                    return max(domain_leads, key=lambda x: x.created_at)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding existing lead: {e}")
            return None
    
    async def _handle_new_lead(self, message: ProcessedMessage):
        """Handle a new lead email"""
        logger.info(f"Processing new lead from {message.sender_email}")
        
        try:
            # Parse email content with Claude to extract lead information
            lead_info = await self._extract_lead_information(message)
            
            # Create new lead record
            lead = Lead(
                email=message.sender_email,
                name=lead_info.get('name', ''),
                company=lead_info.get('company', ''),
                phone=lead_info.get('phone', ''),
                project_type=lead_info.get('project_type', ''),
                project_description=lead_info.get('description', message.subject),
                location=lead_info.get('location', ''),
                budget_range=lead_info.get('budget', ''),
                timeline=lead_info.get('timeline', ''),
                source='email',
                status=LeadStatus.NEW,
                qualification_step=QualificationStep.INITIAL_CONTACT.value,
                created_at=datetime.utcnow()
            )
            
            # Save lead to database
            lead_id = self.db.create_lead(lead)
            lead.id = lead_id
            
            # Store the original message
            original_message = Message(
                lead_id=lead_id,
                sender='customer',
                content=message.content,
                timestamp=message.timestamp,
                gmail_message_id=message.message_id,
                thread_id=message.thread_id
            )
            self.db.create_message(original_message)
            
            # Process any photo attachments
            if message.attachments:
                await self._process_attachments(lead, message.attachments)
            
            # Send initial qualification response
            await self._send_qualification_response(lead, QualificationStep.INITIAL_CONTACT)
            
            logger.info(f"Created new lead {lead_id} for {message.sender_email}")
            
        except Exception as e:
            logger.error(f"Error handling new lead: {e}", exc_info=True)
            raise
    
    async def _handle_existing_lead(self, lead: Lead, message: ProcessedMessage):
        """Handle email from existing lead"""
        logger.info(f"Processing message from existing lead {lead.id}: {lead.email}")
        
        try:
            # Store the incoming message
            incoming_message = Message(
                lead_id=lead.id,
                sender='customer',
                content=message.content,
                timestamp=message.timestamp,
                gmail_message_id=message.message_id,
                thread_id=message.thread_id
            )
            self.db.create_message(incoming_message)
            
            # Process any photo attachments
            if message.attachments:
                await self._process_attachments(lead, message.attachments)
            
            # Determine current qualification step
            current_step = QualificationStep(lead.qualification_step) if lead.qualification_step else QualificationStep.INITIAL_CONTACT
            
            # Analyze the message to understand intent and extract information
            analysis = await self._analyze_customer_response(lead, message, current_step)
            
            # Update lead information based on analysis
            if analysis.get('extracted_info'):
                await self._update_lead_information(lead, analysis['extracted_info'])
            
            # Determine next step based on analysis
            next_step = await self._determine_next_qualification_step(lead, analysis, current_step)
            
            # Send appropriate response
            if next_step:
                await self._send_qualification_response(lead, next_step)
                
                # Update lead status and step
                lead.qualification_step = next_step.value
                if next_step == QualificationStep.QUALIFIED:
                    lead.status = LeadStatus.QUALIFIED
                elif next_step in [QualificationStep.NOT_QUALIFIED, QualificationStep.NOT_INTERESTED]:
                    lead.status = LeadStatus.DISQUALIFIED
                else:
                    lead.status = LeadStatus.IN_PROGRESS
                
                self.db.update_lead(lead)
            
            logger.info(f"Processed message for lead {lead.id}, current step: {next_step}")
            
        except Exception as e:
            logger.error(f"Error handling existing lead: {e}", exc_info=True)
            raise
    
    async def _extract_lead_information(self, message: ProcessedMessage) -> Dict:
        """Extract lead information from email using Claude"""
        try:
            prompt = f"""
            Analyze this email from a potential contractor lead and extract relevant information.
            
            From: {message.sender_email}
            Subject: {message.subject}
            Content: {message.content}
            
            Please extract and return JSON with the following fields (use empty string if not found):
            - name: Person's name
            - company: Company name
            - phone: Phone number
            - project_type: Type of construction/contractor work needed
            - description: Project description
            - location: Project location/address
            - budget: Budget information
            - timeline: Project timeline
            - urgency: How urgent the project seems (low/medium/high)
            
            Return only valid JSON.
            """
            
            response = await self.claude_client.analyze_message(prompt)
            
            # Parse JSON response
            try:
                info = json.loads(response)
                return info
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response from Claude: {response}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting lead information: {e}")
            return {}
    
    async def _analyze_customer_response(self, lead: Lead, message: ProcessedMessage, current_step: QualificationStep) -> Dict:
        """Analyze customer response using Claude"""
        try:
            # Get conversation history for context
            recent_messages = self.db.get_recent_messages(lead.id, limit=10)
            conversation_history = "\n".join([
                f"{'Bot' if msg.sender == 'system' else 'Customer'}: {msg.content}"
                for msg in reversed(recent_messages)
            ])
            
            prompt = f"""
            Analyze this customer response in the context of contractor lead qualification.
            
            Lead Information:
            - Name: {lead.name}
            - Email: {lead.email}
            - Project: {lead.project_description}
            - Current Step: {current_step.name}
            
            Recent Conversation:
            {conversation_history}
            
            Latest Customer Message: {message.content}
            
            Analyze and return JSON with:
            - intent: customer's intent (interested/not_interested/asking_question/providing_info/requesting_quote)
            - sentiment: positive/neutral/negative
            - extracted_info: any new information about project (as dict with keys: budget, timeline, location, requirements, etc.)
            - questions_asked: list of questions the customer asked
            - ready_for_quote: boolean - are they ready for a quote/estimate?
            - qualification_status: qualified/not_qualified/needs_more_info
            
            Return only valid JSON.
            """
            
            response = await self.claude_client.analyze_message(prompt)
            
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response from Claude: {response}")
                return {'intent': 'unknown', 'sentiment': 'neutral'}
                
        except Exception as e:
            logger.error(f"Error analyzing customer response: {e}")
            return {'intent': 'unknown', 'sentiment': 'neutral'}
    
    async def _update_lead_information(self, lead: Lead, extracted_info: Dict):
        """Update lead information with newly extracted data"""
        try:
            updated = False
            
            # Update fields if new information is provided
            if extracted_info.get('budget') and not lead.budget_range:
                lead.budget_range = extracted_info['budget']
                updated = True
            
            if extracted_info.get('timeline') and not lead.timeline:
                lead.timeline = extracted_info['timeline']
                updated = True
                
            if extracted_info.get('location') and not lead.location:
                lead.location = extracted_info['location']
                updated = True
                
            if extracted_info.get('requirements'):
                # Append to project description
                if lead.project_description:
                    lead.project_description += f"\n\nAdditional requirements: {extracted_info['requirements']}"
                else:
                    lead.project_description = extracted_info['requirements']
                updated = True
            
            if extracted_info.get('phone') and not lead.phone:
                lead.phone = extracted_info['phone']
                updated = True
            
            if updated:
                self.db.update_lead(lead)
                logger.info(f"Updated lead {lead.id} with new information")
                
        except Exception as e:
            logger.error(f"Error updating lead information: {e}")
    
    async def _determine_next_qualification_step(self, lead: Lead, analysis: Dict, current_step: QualificationStep) -> Optional[QualificationStep]:
        """Determine the next qualification step based on analysis"""
        try:
            intent = analysis.get('intent', '').lower()
            sentiment = analysis.get('sentiment', '').lower()
            qualification_status = analysis.get('qualification_status', '').lower()
            ready_for_quote = analysis.get('ready_for_quote', False)
            
            # Handle not interested responses
            if intent == 'not_interested' or sentiment == 'negative':
                return QualificationStep.NOT_INTERESTED
            
            # Handle qualification status
            if qualification_status == 'not_qualified':
                return QualificationStep.NOT_QUALIFIED
            elif qualification_status == 'qualified' or ready_for_quote:
                return QualificationStep.QUALIFIED
            
            # Progress through qualification steps
            if current_step == QualificationStep.INITIAL_CONTACT:
                if intent in ['interested', 'providing_info', 'asking_question']:
                    return QualificationStep.PROJECT_DETAILS
                    
            elif current_step == QualificationStep.PROJECT_DETAILS:
                # Check if we have enough project information
                if (lead.project_description and lead.location) or intent == 'providing_info':
                    return QualificationStep.BUDGET_TIMELINE
                    
            elif current_step == QualificationStep.BUDGET_TIMELINE:
                # Check if we have budget and timeline info
                if lead.budget_range and lead.timeline:
                    return QualificationStep.AVAILABILITY
                elif intent == 'providing_info':
                    return QualificationStep.AVAILABILITY
                    
            elif current_step == QualificationStep.AVAILABILITY:
                return QualificationStep.QUALIFIED
            
            # If customer is asking questions, provide information
            if intent == 'asking_question':
                return QualificationStep.ANSWERING_QUESTIONS
                
            # Default: stay at current step if no clear progression
            return current_step
            
        except Exception as e:
            logger.error(f"Error determining next qualification step: {e}")
            return current_step
    
    async def _send_qualification_response(self, lead: Lead, step: QualificationStep):
        """Send qualification response based on current step"""
        try:
            # Generate response using qualification manager
            response_content = await self.qualification_manager.generate_response(lead, step)
            
            if not response_content:
                logger.warning(f"No response generated for step {step}")
                return
            
            # Send email response
            await self._send_email_response(lead.email, response_content, lead)
            
            # Store the sent message
            sent_message = Message(
                lead_id=lead.id,
                sender='system',
                content=response_content,
                timestamp=datetime.utcnow()
            )
            self.db.create_message(sent_message)
            
            logger.info(f"Sent qualification response for step {step} to lead {lead.id}")
            
        except Exception as e:
            logger.error(f"Error sending qualification response: {e}")
            raise
    
    async def _send_email_response(self, to_email: str, content: str, lead: Lead):
        """Send email response through Gmail"""
        try:
            subject = f"Re: Your Construction Project Inquiry"
            
            # If this is part of an existing thread, use appropriate subject
            recent_messages = self.db.get_recent_messages(lead.id, limit=1)
            if recent_messages and recent_messages[0].sender == 'customer':
                # Try to maintain thread continuity
                subject = f"Re: {lead.project_description[:50]}..." if lead.project_description else subject
            
            await self.gmail_client.send_email(to_email, subject, content)
            logger.info(f"Email sent to {to_email}")
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            raise
    
    async def _process_attachments(self, lead: Lead, attachments: List[str]):
        """Process photo attachments for trade assessment"""
        try:
            for attachment_id in attachments:
                # Download attachment from Gmail
                attachment_data = await self.gmail_client.get_attachment(attachment_id)
                
                if not attachment_data:
                    continue
                
                # Check if it's an image
                if not attachment_data.get('content_type', '').startswith('image/'):
                    continue
                
                # Analyze image with Claude Vision
                analysis = await self.claude_client.analyze_image(
                    attachment_data['data'],
                    "Analyze this construction/contractor related image. What type of work is needed? What trade specialties are required? Provide assessment of scope and complexity."
                )
                
                if analysis:
                    # Store image analysis as a message
                    analysis_message = Message(
                        lead_id=lead.id,
                        sender='system',
                        content=f"Photo Analysis: {analysis}",
                        timestamp=datetime.utcnow()
                    )
                    self.db.create_message(analysis_message)
                    
                    # Update project description with analysis
                    if lead.project_description:
                        lead.project_description += f"\n\nPhoto Analysis: {analysis}"
                    else:
                        lead.project_description = f"Photo Analysis: {analysis}"
                    
                    self.db.update_lead(lead)
                    
                    logger.info(f"Processed image attachment for lead {lead.id}")
                
        except Exception as e:
            logger.error(f"Error processing attachments: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            # Close database connections
            if hasattr(self.db, 'close'):
                self.db.close()
            
            # Clean up Gmail client
            if hasattr(self.gmail_client, 'close'):
                await self.gmail_client.close()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point"""
    try:
        processor = EmailProcessor()
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())