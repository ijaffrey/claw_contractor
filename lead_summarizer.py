"""Lead Summarizer Module - Generates structured lead summaries using Claude API"""

import logging
from typing import Dict, Any, List
from anthropic import Anthropic
from config import Config
import database_manager

logger = logging.getLogger(__name__)

class LeadSummarizer:
    """Generates structured qualification summaries for completed conversations"""
    
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.db = database_manager
        
    def generate_summary(self, lead_id: str, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured lead summary from conversation
        
        Args:
            lead_id: Lead identifier
            conversation_data: Complete conversation history
            
        Returns:
            Dict with summary, lead score, and email-ready format
        """
        try:
            # Extract conversation history
            messages = conversation_data.get('messages', [])
            lead_info = conversation_data.get('lead_info', {})
            
            # Build prompt for summary generation
            conversation_text = self._format_conversation(messages)
            prompt = self._build_summary_prompt(lead_info, conversation_text)
            
            # Generate summary with Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude response
            summary_text = response.content[0].text
            structured_summary = {'raw_summary': summary_text, 'timestamp': self._get_timestamp()}
            
            # Add lead scoring
            lead_score = self._calculate_lead_score(structured_summary, messages)
            
            # Format for email delivery
            email_content = self._format_for_email(structured_summary, lead_score)
            
            return {
                'lead_id': lead_id,
                'summary': structured_summary,
                'lead_score': lead_score,
                'email_content': email_content,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error generating summary for lead {lead_id}: {str(e)}")
            return {'lead_id': lead_id, 'error': str(e), 'status': 'failed'}
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation messages for Claude analysis"""
        formatted = []
        for msg in messages:
            sender = "Customer" if msg.get('from_customer', True) else "Assistant"
            content = msg.get('content', msg.get('body', ''))
            formatted.append(f"{sender}: {content}")
        return "\n\n".join(formatted)
    def _build_summary_prompt(self, lead_info: Dict, conversation: str) -> str:
        """Build prompt for Claude summary generation"""
        # Include enrichment fields if already populated
        enrichment_block = ""
        if any(lead_info.get(k) for k in ("job_type_classification", "value_tier", "urgency_score", "one_line_summary")):
            enrichment_block = f"""
**Job Classification:** {lead_info.get('job_type_classification', 'N/A')}
**Value Tier:** {lead_info.get('value_tier', 'N/A')}
**Urgency Score:** {lead_info.get('urgency_score', 'N/A')} / 5
**Summary:** {lead_info.get('one_line_summary', 'N/A')}
"""

        return f"""Analyze this contractor lead conversation and create a structured summary.

Lead Information:
Name: {lead_info.get('name', 'Unknown')}
Email: {lead_info.get('email', 'Unknown')}
Phone: {lead_info.get('phone', 'Unknown')}

Conversation:
{conversation}

Provide a summary in this exact format:

## Lead Summary
**Name:** [name]
**Contact:** [email and phone]
**Project:** [brief project description]
**Timeline:** [when they need work done]
**Budget:** [budget mentioned or "Not specified"]
**Urgency:** [how urgent this seems]
{enrichment_block}
## Key Details
- [bullet point of important details]
- [another important detail]

## Questions Asked & Answered
Q: [question from conversation]
A: [customer's answer]

[repeat for all Q&A pairs]

## Lead Quality Assessment
**Interest Level:** [High/Medium/Low]
**Project Readiness:** [Ready to start/Planning phase/Just exploring]
**Decision Making:** [Ready to hire/Still comparing/Early research]
"""
    
    def _calculate_lead_score(self, summary: Dict, messages: List) -> Dict[str, Any]:
        """Calculate lead scoring (hot/warm/cold)"""
        score = 50  # Base score
        
        # Scoring factors
        message_count = len(messages)
        if message_count > 5:
            score += 20  # Engaged conversation
        elif message_count > 2:
            score += 10
            
        # Check for urgency keywords in summary
        summary_text = summary.get('raw_summary', '').lower()
        if any(word in summary_text for word in ['urgent', 'asap', 'quickly', 'soon']):
            score += 25
            
        # Check for budget discussion
        if any(word in summary_text for word in ['budget', '$', 'cost', 'price']):
            score += 15
            
        # Determine category
        if score >= 80:
            category = 'hot'
        elif score >= 60:
            category = 'warm'
        else:
            category = 'cold'
            
        return {
            'score': score,
            'category': category,
            'factors': {
                'message_count': message_count,
                'engagement_level': 'high' if message_count > 5 else 'medium' if message_count > 2 else 'low'
            }
        }
    
    def _format_for_email(self, summary: Dict, lead_score: Dict) -> str:
        """Format summary for contractor email delivery"""
        score_emoji = {'hot': '🔥', 'warm': '⭐', 'cold': '❄️'}
        emoji = score_emoji.get(lead_score['category'], '📋')
        
        return f"""{emoji} New Lead Summary - {lead_score['category'].upper()} Lead (Score: {lead_score['score']})

{summary.get('raw_summary', 'Summary not available')}

---
Generated at: {summary.get('timestamp', 'Unknown')}
Lead Score: {lead_score['score']}/100 ({lead_score['category']})
"""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
