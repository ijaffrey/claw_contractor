import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re

from .config import Config
from .reply_generator import ReplyGenerator, ReplyContext

logger = logging.getLogger(__name__)

@dataclass
class ContractorInfo:
    """Contractor information for handoff messages"""
    name: str
    title: str
    phone: str
    email: str
    certifications: List[str]
    experience_years: int
    specialties: List[str]
    availability: str = "Within 24 hours"
    photo_url: Optional[str] = None

@dataclass
class ServiceTimeline:
    """Service timeline information"""
    initial_contact: str = "Within 24 hours"
    site_visit: str = "1-3 business days"
    quote_delivery: str = "24-48 hours after site visit"
    project_start: str = "Upon approval and scheduling"
    estimated_completion: Optional[str] = None

@dataclass
class HandoffContext:
    """Context for generating handoff messages"""
    customer_name: str
    service_type: str
    urgency_level: str = "standard"  # urgent, high, standard, low
    contractor: ContractorInfo
    timeline: ServiceTimeline
    lead_source: str = ""
    specific_requirements: List[str] = None
    location: str = ""
    budget_range: str = ""
    preferred_contact_method: str = "phone"
    additional_notes: str = ""

class CustomerHandoffMessenger:
    """Handles generation of professional customer handoff messages"""
    
    def __init__(self, config: Config):
        self.config = config
        self.reply_generator = ReplyGenerator(config)
        self.templates = self._load_templates()
        self.company_info = self._load_company_info()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load handoff message templates"""
        try:
            templates_path = Path(self.config.get('templates_path', 'templates'))
            handoff_templates_file = templates_path / 'handoff_templates.json'
            
            if handoff_templates_file.exists():
                with open(handoff_templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_templates()
        except Exception as e:
            logger.error(f"Error loading handoff templates: {e}")
            return self._get_default_templates()
    
    def _load_company_info(self) -> Dict[str, Any]:
        """Load company branding information"""
        return {
            'name': self.config.get('company_name', 'Professional Services'),
            'phone': self.config.get('company_phone', ''),
            'email': self.config.get('company_email', ''),
            'website': self.config.get('company_website', ''),
            'logo_url': self.config.get('company_logo_url', ''),
            'tagline': self.config.get('company_tagline', 'Quality service you can trust'),
            'address': self.config.get('company_address', ''),
            'license_number': self.config.get('license_number', ''),
            'insurance_info': self.config.get('insurance_info', 'Fully licensed and insured')
        }
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Get default handoff message templates"""
        return {
            'standard': """
Hello {customer_name},

Thank you for choosing {company_name} for your {service_type} needs. We're excited to help you with your project!

**Your Next Steps:**
{next_steps}

**Your Assigned Contractor:**
{contractor_introduction}

**What to Expect:**
{timeline_section}

**Project Details:**
{project_details}

{urgency_message}

**Questions or Concerns:**
If you have any questions before your contractor contacts you, please don't hesitate to reach out to our customer service team at {company_phone} or {company_email}.

{closing_section}

Best regards,
{company_name} Team
{company_tagline}
""",
            'urgent': """
🚨 URGENT SERVICE REQUEST - IMMEDIATE RESPONSE 🚨

Hello {customer_name},

We've received your urgent request for {service_type} and are taking immediate action to assist you.

**PRIORITY ASSIGNMENT:**
{contractor_introduction}

**IMMEDIATE NEXT STEPS:**
{next_steps}

**EXPEDITED TIMELINE:**
{timeline_section}

{urgency_message}

**24/7 Support:**
For immediate assistance: {company_phone}
Emergency contact: {contractor_phone}

{closing_section}

{company_name} - Here when you need us most
""",
            'follow_up': """
Hello {customer_name},

Following up on your {service_type} inquiry with {company_name}.

**Status Update:**
{status_update}

**Your Contractor:**
{contractor_introduction}

**Next Actions:**
{next_steps}

{closing_section}

Best regards,
{company_name}
"""
        }
    
    def generate_handoff_message(self, context: HandoffContext) -> Dict[str, Any]:
        """Generate a complete handoff message"""
        try:
            # Determine message template based on urgency
            template_key = self._get_template_key(context.urgency_level)
            template = self.templates.get(template_key, self.templates['standard'])
            
            # Generate message components
            components = {
                'customer_name': context.customer_name,
                'company_name': self.company_info['name'],
                'company_phone': self.company_info['phone'],
                'company_email': self.company_info['email'],
                'service_type': context.service_type,
                'contractor_introduction': self._generate_contractor_introduction(context.contractor),
                'next_steps': self._generate_next_steps(context),
                'timeline_section': self._generate_timeline_section(context.timeline, context.urgency_level),
                'project_details': self._generate_project_details(context),
                'urgency_message': self._generate_urgency_message(context.urgency_level),
                'closing_section': self._generate_closing_section(),
                'contractor_phone': context.contractor.phone,
                'status_update': self._generate_status_update(context)
            }
            
            # Format the message
            message = template.format(**components)
            
            # Generate subject line
            subject = self._generate_subject_line(context)
            
            # Create reply context for integration
            reply_context = ReplyContext(
                message_type='handoff',
                customer_name=context.customer_name,
                service_type=context.service_type,
                urgency=context.urgency_level,
                additional_context={'handoff_data': asdict(context)}
            )
            
            return {
                'message': message,
                'subject': subject,
                'contractor_info': asdict(context.contractor),
                'timeline': asdict(context.timeline),
                'urgency_level': context.urgency_level,
                'reply_context': reply_context,
                'formatted_html': self._generate_html_version(message, components),
                'attachments': self._get_recommended_attachments(context),
                'follow_up_schedule': self._generate_follow_up_schedule(context)
            }
            
        except Exception as e:
            logger.error(f"Error generating handoff message: {e}")
            return self._generate_fallback_message(context)
    
    def _get_template_key(self, urgency_level: str) -> str:
        """Determine template key based on urgency level"""
        urgency_mapping = {
            'urgent': 'urgent',
            'emergency': 'urgent',
            'high': 'standard',
            'standard': 'standard',
            'low': 'standard'
        }
        return urgency_mapping.get(urgency_level.lower(), 'standard')
    
    def _generate_contractor_introduction(self, contractor: ContractorInfo) -> str:
        """Generate contractor introduction section"""
        intro_parts = [
            f"**{contractor.name}** - {contractor.title}",
            f"📱 Direct: {contractor.phone}",
            f"📧 Email: {contractor.email}"
        ]
        
        if contractor.experience_years:
            intro_parts.append(f"🏆 Experience: {contractor.experience_years}+ years")
        
        if contractor.certifications:
            certs = ", ".join(contractor.certifications)
            intro_parts.append(f"🎓 Certifications: {certs}")
        
        if contractor.specialties:
            specialties = ", ".join(contractor.specialties)
            intro_parts.append(f"🔧 Specialties: {specialties}")
        
        intro_parts.append(f"⏰ Availability: {contractor.availability}")
        
        return "\n".join(intro_parts)
    
    def _generate_next_steps(self, context: HandoffContext) -> str:
        """Generate next steps based on context"""
        steps = []
        
        # Step 1: Initial contact
        contact_method = context.preferred_contact_method.lower()
        if contact_method == 'phone':
            steps.append(f"1. {context.contractor.name} will call you within {context.timeline.initial_contact}")
        elif contact_method == 'email':
            steps.append(f"1. {context.contractor.name} will email you within {context.timeline.initial_contact}")
        else:
            steps.append(f"1. {context.contractor.name} will contact you within {context.timeline.initial_contact}")
        
        # Step 2: Site visit/assessment
        if context.service_type.lower() in ['repair', 'installation', 'maintenance', 'inspection']:
            steps.append(f"2. Schedule a site visit within {context.timeline.site_visit}")
        else:
            steps.append("2. Discuss your specific requirements and preferences")
        
        # Step 3: Quote
        steps.append(f"3. Receive a detailed quote within {context.timeline.quote_delivery}")
        
        # Step 4: Project start
        steps.append(f"4. Begin work {context.timeline.project_start}")
        
        return "\n".join(steps)
    
    def _generate_timeline_section(self, timeline: ServiceTimeline, urgency: str) -> str:
        """Generate timeline expectations section"""
        timeline_parts = [
            f"• Initial Contact: {timeline.initial_contact}",
            f"• Site Visit: {timeline.site_visit}",
            f"• Quote Delivery: {timeline.quote_delivery}",
            f"• Project Start: {timeline.project_start}"
        ]
        
        if timeline.estimated_completion:
            timeline_parts.append(f"• Estimated Completion: {timeline.estimated_completion}")
        
        if urgency.lower() in ['urgent', 'emergency']:
            timeline_parts.insert(0, "⚡ **EXPEDITED SERVICE** ⚡")
        
        return "\n".join(timeline_parts)
    
    def _generate_project_details(self, context: HandoffContext) -> str:
        """Generate project details section"""
        details = []
        
        if context.location:
            details.append(f"• Location: {context.location}")
        
        if context.service_type:
            details.append(f"• Service: {context.service_type}")
        
        if context.budget_range:
            details.append(f"• Budget Range: {context.budget_range}")
        
        if context.specific_requirements:
            req_list = "\n  - ".join(context.specific_requirements)
            details.append(f"• Requirements:\n  - {req_list}")
        
        if context.lead_source:
            details.append(f"• Referred from: {context.lead_source}")
        
        if context.additional_notes:
            details.append(f"• Additional Notes: {context.additional_notes}")
        
        return "\n".join(details) if details else "• Service details will be confirmed during initial consultation"
    
    def _generate_urgency_message(self, urgency_level: str) -> str:
        """Generate urgency-specific messaging"""
        urgency_messages = {
            'urgent': """
🚨 **URGENT PRIORITY SERVICE** 🚨
Your request has been marked as urgent. Our contractor will prioritize your call and aim to provide same-day service if possible.
""",
            'emergency': """
🆘 **EMERGENCY SERVICE ACTIVATED** 🆘
We understand this is an emergency situation. Our contractor is on standby and will contact you immediately.
""",
            'high': """
⚡ **HIGH PRIORITY** ⚡
Your request has been flagged as high priority. We'll ensure prompt service and communication throughout the process.
""",
            'standard': """
Thank you for your patience as we coordinate the best service for your needs.
""",
            'low': """
We appreciate your flexibility with timing and will ensure quality service at your convenience.
"""
        }
        
        return urgency_messages.get(urgency_level.lower(), urgency_messages['standard'])
    
    def _generate_closing_section(self) -> str:
        """Generate professional closing with company branding"""
        closing_parts = []
        
        # Company credentials
        if self.company_info['license_number']:
            closing_parts.append(f"License #: {self.company_info['license_number']}")
        
        if self.company_info['insurance_info']:
            closing_parts.append(f"Insurance: {self.company_info['insurance_info']}")
        
        # Contact information
        contact_info = []
        if self.company_info['website']:
            contact_info.append(f"🌐 Website: {self.company_info['website']}")
        if self.company_info['address']:
            contact_info.append(f"📍 Address: {self.company_info['address']}")
        
        if contact_info:
            closing_parts.extend(contact_info)
        
        # Satisfaction guarantee
        closing_parts.append("💯 Your satisfaction is our guarantee!")
        
        return "\n".join(closing_parts)
    
    def _generate_subject_line(self, context: HandoffContext) -> str:
        """Generate appropriate subject line"""
        urgency_prefix = {
            'urgent': '[URGENT] ',
            'emergency': '[EMERGENCY] ',
            'high': '[HIGH PRIORITY] '
        }.get(context.urgency_level.lower(), '')
        
        service_desc = context.service_type.title()
        
        return f"{urgency_prefix}Your {service_desc} Request - Contractor Assigned ({context.contractor.name})"
    
    def _generate_status_update(self, context: HandoffContext) -> str:
        """Generate status update for follow-up messages"""
        return f"Your {context.service_type} request has been assigned to {context.contractor.name}, who will be your dedicated point of contact."
    
    def _generate_html_version(self, message: str, components: Dict[str, str]) -> str:
        """Generate HTML version of the message"""
        # Convert markdown-style formatting to HTML
        html_message = message.replace('**', '<strong>').replace('**', '</strong>')
        html_message = html_message.replace('🚨', '<span style="color: red; font-weight: bold;">🚨</span>')
        html_message = html_message.replace('⚡', '<span style="color: orange; font-weight: bold;">⚡</span>')
        html_message = html_message.replace('\n', '<br>\n')
        
        # Wrap in basic HTML structure
        html_template = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .contractor-info {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .timeline {{ background-color: #f0f8f0; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .footer {{ background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; }}
                .urgent {{ color: #d32f2f; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{components.get('company_name', 'Professional Services')}</h2>
                <p>{self.company_info['tagline']}</p>
            </div>
            <div class="content">
                {html_message}
            </div>
            <div class="footer">
                <p>© 2024 {components.get('company_name', 'Professional Services')}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _get_recommended_attachments(self, context: HandoffContext) -> List[Dict[str, str]]:
        """Get recommended attachments for handoff message"""
        attachments = []
        
        # Service brochure
        attachments.append({
            'type': 'brochure',
            'name': f'{context.service_type.replace(" ", "_")}_service_guide.pdf',
            'description': f'Detailed information about our {context.service_type} services'
        })
        
        # Contractor profile
        if context.contractor.photo_url:
            attachments.append({
                'type': 'photo',
                'name': f'{context.contractor.name.replace(" ", "_")}_profile.jpg',
                'url': context.contractor.photo_url,
                'description': f'Photo of your assigned contractor, {context.contractor.name}'
            })
        
        # Company credentials
        attachments.append({
            'type': 'credentials',
            'name': 'company_credentials.pdf',
            'description': 'License, insurance, and certification information'
        })
        
        return attachments
    
    def _generate_follow_up_schedule(self, context: HandoffContext) -> List[Dict[str, Any]]:
        """Generate follow-up communication schedule"""
        schedule = []
        now = datetime.now()
        
        # Initial contact follow-up
        if context.urgency_level.lower() in ['urgent', 'emergency']:
            schedule.append({
                'type': 'contact_check',
                'datetime': now + timedelta(hours=2),
                'message': 'Verify contractor has made initial contact'
            })
        else:
            schedule.append({
                'type': 'contact_check',
                'datetime': now + timedelta(days=1),
                'message': 'Verify contractor has made initial contact'
            })
        
        # Quote follow-up
        schedule.append({
            'type': 'quote_follow_up',
            'datetime': now + timedelta(days=3),
            'message': 'Check if quote has been received and address any questions'
        })
        
        # Project status
        schedule.append({
            'type': 'project_status',
            'datetime': now + timedelta(days=7),
            'message': 'Check project status and satisfaction'
        })
        
        return schedule
    
    def _generate_fallback_message(self, context: HandoffContext) -> Dict[str, Any]:
        """Generate fallback message if template processing fails"""
        fallback_message = f"""
Hello {context.customer_name},

Thank you for choosing {self.company_info['name']} for your {context.service_type} needs.

Your assigned contractor is {context.contractor.name} and they will contact you within {context.timeline.initial_contact}.

Contact information:
- Phone: {context.contractor.phone}
- Email: {context.contractor.email}

If you have any questions, please contact us at {self.company_info['phone']}.

Best regards,
{self.company_info['name']} Team
"""
        
        return {
            'message': fallback_message,
            'subject': f"Your {context.service_type} Request - Contractor Assignment",
            'contractor_info': asdict(context.contractor),
            'timeline': asdict(context.timeline),
            'urgency_level': context.urgency_level,
            'formatted_html': fallback_message.replace('\n', '<br>'),
            'attachments': [],
            'follow_up_schedule': []
        }
    
    def create_contractor_info(self, name: str, title: str, phone: str, email: str,
                            certifications: List[str] = None, experience_years: int = 0,
                            specialties: List[str] = None, **kwargs) -> ContractorInfo:
        """Helper method to create ContractorInfo objects"""
        return ContractorInfo(
            name=name,
            title=title,
            phone=phone,
            email=email,
            certifications=certifications or [],
            experience_years=experience_years,
            specialties=specialties or [],
            **kwargs
        )
    
    def create_handoff_context(self, customer_name: str, service_type: str,
                             contractor: ContractorInfo, **kwargs) -> HandoffContext:
        """Helper method to create HandoffContext objects"""
        return HandoffContext(
            customer_name=customer_name,
            service_type=service_type,
            contractor=contractor,
            timeline=kwargs.get('timeline', ServiceTimeline()),
            **{k: v for k, v in kwargs.items() if k != 'timeline'}
        )
    
    def generate_bulk_handoff_messages(self, contexts: List[HandoffContext]) -> List[Dict[str, Any]]:
        """Generate multiple handoff messages efficiently"""
        results = []
        
        for context in contexts:
            try:
                message_data = self.generate_handoff_message(context)
                message_data['success'] = True
                message_data['customer_name'] = context.customer_name
            except Exception as e:
                logger.error(f"Error generating handoff for {context.customer_name}: {e}")
                message_data = {
                    'success': False,
                    'error': str(e),
                    'customer_name': context.customer_name
                }
            
            results.append(message_data)
        
        return results
    
    def update_templates(self, new_templates: Dict[str, str]) -> bool:
        """Update handoff templates"""
        try:
            self.templates.update(new_templates)
            
            # Save to file if templates path is configured
            templates_path = Path(self.config.get('templates_path', 'templates'))
            templates_path.mkdir(exist_ok=True)
            
            handoff_templates_file = templates_path / 'handoff_templates.json'
            with open(handoff_templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            
            logger.info("Handoff templates updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating handoff templates: {e}")
            return False
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template keys"""
        return list(self.templates.keys())
    
    def validate_handoff_context(self, context: HandoffContext) -> Dict[str, List[str]]:
        """Validate handoff context and return any issues"""
        issues = {'errors': [], 'warnings': []}
        
        # Required fields
        if not context.customer_name.strip():
            issues['errors'].append("Customer name is required")
        
        if not context.service_type.strip():
            issues['errors'].append("Service type is required")
        
        if not context.contractor.name.strip():
            issues['errors'].append("Contractor name is required")
        
        if not context.contractor.phone.strip():
            issues['errors'].append("Contractor phone is required")
        
        # Validate phone format
        phone_pattern = re.compile(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$')
        if context.contractor.phone and not phone_pattern.match(context.contractor.phone):
            issues['warnings'].append("Contractor phone format may be invalid")
        
        # Validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if context.contractor.email and not email_pattern.match(context.contractor.email):
            issues['warnings'].append("Contractor email format may be invalid")
        
        # Check for missing optional but recommended fields
        if not context.contractor.title:
            issues['warnings'].append("Contractor title is missing")
        
        if not context.contractor.experience_years:
            issues['warnings'].append("Contractor experience years not specified")
        
        return issues