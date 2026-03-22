# Interface Mapping Document

## Overview
This document maps the interfaces between the 6 core modules of the LinkedIn outreach system, identifying function-based vs class-based patterns and proposing adapter solutions for interface mismatches.

## Module Interface Specifications

### 1. database.py
**Architecture**: Function-based
**Purpose**: Database operations and data persistence

#### Exports
```python
# Core database functions
connect_db() -> sqlite3.Connection
init_db(conn: sqlite3.Connection) -> None
close_db(conn: sqlite3.Connection) -> None

# Lead management functions
save_lead(conn: sqlite3.Connection, lead_data: dict) -> int
get_lead(conn: sqlite3.Connection, lead_id: int) -> Optional[dict]
get_pending_leads(conn: sqlite3.Connection) -> List[dict]
update_lead_status(conn: sqlite3.Connection, lead_id: int, status: str) -> bool

# Reply tracking functions
save_reply(conn: sqlite3.Connection, lead_id: int, reply_text: str) -> int
get_replies_for_lead(conn: sqlite3.Connection, lead_id: int) -> List[dict]

# Analytics functions
get_engagement_stats(conn: sqlite3.Connection) -> dict
get_leads_by_date_range(conn: sqlite3.Connection, start_date: str, end_date: str) -> List[dict]
```

#### Inputs
- `conn`: sqlite3.Connection object
- `lead_data`: dict with keys ['name', 'profile_url', 'company', 'job_title', 'message_text']
- `lead_id`: int (primary key)
- `status`: str ('pending', 'qualified', 'replied', 'contacted')
- `reply_text`: str (message content)
- Date strings in 'YYYY-MM-DD' format

#### Outputs
- Database connection objects
- Lead records as dictionaries
- Integer IDs for new records
- Boolean success indicators
- Lists of dictionaries for bulk queries

### 2. lead_parser.py
**Architecture**: Class-based
**Purpose**: Parse and extract lead information from LinkedIn profiles

#### Exports
```python
class LeadParser:
    def __init__(self, config: dict = None):
        pass
    
    def parse_profile(self, profile_url: str) -> dict:
        """Parse a single LinkedIn profile"""
        pass
    
    def parse_batch(self, profile_urls: List[str]) -> List[dict]:
        """Parse multiple profiles in batch"""
        pass
    
    def extract_contact_info(self, profile_data: dict) -> dict:
        """Extract contact information from profile"""
        pass
    
    def validate_profile_data(self, data: dict) -> bool:
        """Validate extracted profile data"""
        pass
    
    def get_parsing_stats(self) -> dict:
        """Return parsing statistics"""
        pass

# Utility functions (function-based)
def sanitize_profile_url(url: str) -> str:
def is_valid_linkedin_url(url: str) -> bool:
```

#### Inputs
- `config`: Optional dict with parsing configuration
- `profile_url`: str (LinkedIn profile URL)
- `profile_urls`: List[str] (batch of URLs)
- `profile_data`: dict (raw profile data)

#### Outputs
- Lead data dictionaries with standardized schema
- Lists of lead dictionaries for batch operations
- Contact information dictionaries
- Boolean validation results
- Statistics dictionaries

### 3. reply_generator.py
**Architecture**: Class-based
**Purpose**: Generate personalized replies using AI

#### Exports
```python
class ReplyGenerator:
    def __init__(self, ai_config: dict):
        pass
    
    def generate_reply(self, lead_data: dict, context: str = "") -> str:
        """Generate personalized reply for a lead"""
        pass
    
    def generate_follow_up(self, lead_data: dict, previous_messages: List[str]) -> str:
        """Generate follow-up message"""
        pass
    
    def customize_template(self, template: str, lead_data: dict) -> str:
        """Customize message template with lead data"""
        pass
    
    def validate_reply(self, reply_text: str) -> dict:
        """Validate generated reply"""
        pass
    
    def get_generation_stats(self) -> dict:
        """Return generation statistics"""
        pass

# Template management (function-based utilities)
def load_templates(template_dir: str) -> dict:
def save_template(template_name: str, content: str) -> bool:
```

#### Inputs
- `ai_config`: dict with AI model configuration
- `lead_data`: dict (standardized lead information)
- `context`: str (additional context for generation)
- `previous_messages`: List[str] (message history)
- `template`: str (message template)
- `reply_text`: str (generated reply to validate)

#### Outputs
- Generated reply strings
- Validation result dictionaries
- Customized template strings
- Statistics dictionaries
- Boolean success indicators

### 4. qualified_lead_detector.py
**Architecture**: Function-based
**Purpose**: Detect and score qualified leads

#### Exports
```python
# Core qualification functions
calculate_lead_score(lead_data: dict) -> float
is_qualified_lead(lead_data: dict, threshold: float = 0.7) -> bool
analyze_company_fit(company_info: dict) -> dict
analyze_role_relevance(job_title: str, target_roles: List[str]) -> float

# Batch processing functions
process_lead_batch(leads: List[dict]) -> List[dict]:
filter_qualified_leads(leads: List[dict], threshold: float = 0.7) -> List[dict]

# Configuration functions
load_scoring_config(config_path: str) -> dict
update_scoring_weights(weights: dict) -> bool

# Analytics functions
get_qualification_stats(leads: List[dict]) -> dict
generate_scoring_report(leads: List[dict]) -> str
```

#### Inputs
- `lead_data`: dict (standardized lead information)
- `threshold`: float (qualification threshold, 0.0-1.0)
- `company_info`: dict (company details)
- `job_title`: str (lead's job title)
- `target_roles`: List[str] (target role patterns)
- `leads`: List[dict] (batch of lead data)
- `config_path`: str (path to scoring configuration)
- `weights`: dict (scoring weight adjustments)

#### Outputs
- Float scores (0.0-1.0 range)
- Boolean qualification results
- Analysis dictionaries with detailed breakdowns
- Processed lead lists with scores
- Filtered qualified lead lists
- Statistics and report strings

### 5. contractor_notifier.py
**Architecture**: Class-based
**Purpose**: Send notifications to contractors about qualified leads

#### Exports
```python
class ContractorNotifier:
    def __init__(self, notification_config: dict):
        pass
    
    def send_lead_notification(self, contractor_id: str, lead_data: dict) -> bool:
        """Send new lead notification"""
        pass
    
    def send_batch_notification(self, contractor_id: str, leads: List[dict]) -> dict:
        """Send batch lead notifications"""
        pass
    
    def send_reply_notification(self, contractor_id: str, reply_data: dict) -> bool:
        """Notify about new replies"""
        pass
    
    def register_contractor(self, contractor_info: dict) -> str:
        """Register new contractor"""
        pass
    
    def update_notification_preferences(self, contractor_id: str, preferences: dict) -> bool:
        """Update contractor notification preferences"""
        pass
    
    def get_notification_history(self, contractor_id: str) -> List[dict]:
        """Get notification history"""
        pass

# Utility functions (function-based)
def format_lead_summary(lead_data: dict) -> str:
def validate_email_address(email: str) -> bool:
def send_test_notification(email: str) -> bool:
```

#### Inputs
- `notification_config`: dict (email/SMS configuration)
- `contractor_id`: str (unique contractor identifier)
- `lead_data`: dict (standardized lead information)
- `leads`: List[dict] (batch of leads)
- `reply_data`: dict (reply information)
- `contractor_info`: dict (contractor registration data)
- `preferences`: dict (notification preferences)

#### Outputs
- Boolean success indicators
- Batch notification result dictionaries
- Contractor ID strings
- Notification history lists
- Formatted summary strings

### 6. main.py (Orchestrator)
**Architecture**: Function-based with coordination logic
**Purpose**: Orchestrate the entire pipeline

#### Exports
```python
# Main orchestration functions
def main() -> None:
def process_leads_pipeline(config: dict) -> dict:
def setup_application(config_path: str) -> dict:
def cleanup_application(app_state: dict) -> None:

# Pipeline stage functions
def run_lead_parsing(profile_urls: List[str], parser_config: dict) -> List[dict]:
def run_qualification(leads: List[dict], qual_config: dict) -> List[dict]:
def run_reply_generation(qualified_leads: List[dict], reply_config: dict) -> List[dict]:
def run_notifications(qualified_leads: List[dict], notification_config: dict) -> dict:

# Monitoring and control functions
def monitor_pipeline_health() -> dict:
def handle_pipeline_errors(error: Exception, context: dict) -> None:
def get_pipeline_stats() -> dict:
```

#### Inputs
- `config`: dict (application configuration)
- `config_path`: str (path to configuration file)
- `app_state`: dict (application state information)
- `profile_urls`: List[str] (LinkedIn profile URLs to process)
- Various configuration dictionaries for each module

#### Outputs
- Pipeline execution result dictionaries
- Application state dictionaries
- Statistics and monitoring data
- Error handling results

## Interface Mismatches and Adapter Solutions

### 1. Database (Function-based) ↔ Lead Parser (Class-based)

**Mismatch**: Lead parser returns objects with methods, but database expects flat dictionaries.

**Adapter Solution**:
```python
class DatabaseLeadAdapter:
    """Adapter to bridge LeadParser objects and database functions"""
    
    @staticmethod
    def parser_to_db_format(lead_parser_result: dict) -> dict:
        """Convert parser output to database input format"""
        return {
            'name': lead_parser_result.get('full_name', ''),
            'profile_url': lead_parser_result.get('profile_url', ''),
            'company': lead_parser_result.get('current_company', ''),
            'job_title': lead_parser_result.get('job_title', ''),
            'message_text': lead_parser_result.get('bio_summary', ''),
            'parsed_timestamp': lead_parser_result.get('extraction_time'),
            'raw_data': json.dumps(lead_parser_result.get('raw_profile_data', {}))
        }
    
    @staticmethod
    def db_to_parser_format(db_record: dict) -> dict:
        """Convert database record to parser input format"""
        raw_data = json.loads(db_record.get('raw_data', '{}'))
        return {
            'profile_url': db_record['profile_url'],
            'cached_data': raw_data,
            'last_updated': db_record.get('parsed_timestamp')
        }
```

### 2. Qualified Lead Detector (Function-based) ↔ Reply Generator (Class-based)

**Mismatch**: Function returns score values, but class expects object context.

**Adapter Solution**:
```python
class QualificationReplyAdapter:
    """Adapter between qualification functions and reply generator"""
    
    def __init__(self, reply_generator: ReplyGenerator):
        self.reply_generator = reply_generator
        self.qualification_cache = {}
    
    def generate_qualified_reply(self, lead_data: dict, score_threshold: float = 0.7) -> Optional[str]:
        """Generate reply only if lead is qualified"""
        score = calculate_lead_score(lead_data)
        
        if score < score_threshold:
            return None
            
        # Enhance lead data with qualification context
        enhanced_data = self._add_qualification_context(lead_data, score)
        return self.reply_generator.generate_reply(enhanced_data)
    
    def _add_qualification_context(self, lead_data: dict, score: float) -> dict:
        """Add qualification context to lead data for better reply generation"""
        qualification_analysis = analyze_company_fit(lead_data.get('company_info', {}))
        
        enhanced_data = lead_data.copy()
        enhanced_data['qualification_score'] = score
        enhanced_data['qualification_reasons'] = qualification_analysis.get('fit_reasons', [])
        enhanced_data['company_fit_score'] = qualification_analysis.get('fit_score', 0.0)
        
        return enhanced_data
```

### 3. Reply Generator (Class-based) ↔ Database (Function-based)

**Mismatch**: Class maintains state and context, but database functions are stateless.

**Adapter Solution**:
```python
class ReplyDatabaseAdapter:
    """Adapter to manage reply generation state with database persistence"""
    
    def __init__(self, db_connection: sqlite3.Connection, reply_generator: ReplyGenerator):
        self.db_conn = db_connection
        self.reply_generator = reply_generator
    
    def generate_and_save_reply(self, lead_id: int) -> Optional[str]:
        """Generate reply and save to database in one operation"""
        # Get lead data from database
        lead_data = get_lead(self.db_conn, lead_id)
        if not lead_data:
            return None
            
        # Get previous replies for context
        previous_replies = get_replies_for_lead(self.db_conn, lead_id)
        reply_history = [r['reply_text'] for r in previous_replies]
        
        # Generate new reply with context
        if reply_history:
            reply = self.reply_generator.generate_follow_up(lead_data, reply_history)
        else:
            reply = self.reply_generator.generate_reply(lead_data)
            
        # Save reply to database
        if reply:
            save_reply(self.db_conn, lead_id, reply)
            
        return reply
    
    def batch_generate_replies(self, lead_ids: List[int]) -> dict:
        """Generate replies for multiple leads"""
        results = {}
        for lead_id in lead_ids:
            try:
                reply = self.generate_and_save_reply(lead_id)
                results[lead_id] = {'success': True, 'reply': reply}
            except Exception as e:
                results[lead_id] = {'success': False, 'error': str(e)}
        return results
```

### 4. Main Orchestrator (Function-based) ↔ All Class-based Modules

**Mismatch**: Orchestrator uses functional patterns but needs to manage class instances.

**Adapter Solution**:
```python
class PipelineOrchestrator:
    """Orchestrator adapter to manage class-based modules functionally"""
    
    def __init__(self, config: dict):
        self.config = config
        self.db_conn = None
        self.lead_parser = None
        self.reply_generator = None
        self.contractor_notifier = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all class-based components"""
        # Database connection (function-based)
        self.db_conn = connect_db()
        init_db(self.db_conn)
        
        # Class-based components
        self.lead_parser = LeadParser(self.config.get('parser_config', {}))
        self.reply_generator = ReplyGenerator(self.config.get('ai_config', {}))
        self.contractor_notifier = ContractorNotifier(self.config.get('notification_config', {}))
        
        # Initialize adapters
        self.db_adapter = DatabaseLeadAdapter()
        self.qual_reply_adapter = QualificationReplyAdapter(self.reply_generator)
        self.reply_db_adapter = ReplyDatabaseAdapter(self.db_conn, self.reply_generator)
    
    def process_leads_functionally(self, profile_urls: List[str]) -> dict:
        """Process leads using functional interface over class-based components"""
        results = {
            'processed': 0,
            'qualified': 0,
            'replies_generated': 0,
            'notifications_sent': 0,
            'errors': []
        }
        
        try:
            # Step 1: Parse leads (class-based → function-like)
            parsed_leads = self.lead_parser.parse_batch(profile_urls)
            
            # Step 2: Save to database (adapter bridges class→function)
            for parsed_lead in parsed_leads:
                db_format_lead = self.db_adapter.parser_to_db_format(parsed_lead)
                lead_id = save_lead(self.db_conn, db_format_lead)
                
                # Step 3: Qualify leads (function-based)
                if is_qualified_lead(db_format_lead):
                    results['qualified'] += 1
                    
                    # Step 4: Generate replies (adapter bridges function→class)
                    reply = self.reply_db_adapter.generate_and_save_reply(lead_id)
                    if reply:
                        results['replies_generated'] += 1
                        
                        # Step 5: Send notifications (class-based)
                        notification_sent = self.contractor_notifier.send_lead_notification(
                            self.config.get('default_contractor_id'),
                            db_format_lead
                        )
                        if notification_sent:
                            results['notifications_sent'] += 1
                
                results['processed'] += 1
                
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.db_conn:
            close_db(self.db_conn)
```

## Parameter and Return Value Standardization

### Standardized Lead Data Schema
```python
STANDARD_LEAD_SCHEMA = {
    'id': int,              # Database primary key (optional for new leads)
    'name': str,            # Full name
    'profile_url': str,     # LinkedIn profile URL
    'company': str,         # Current company
    'job_title': str,       # Current job title
    'location': str,        # Geographic location
    'bio_summary': str,     # Profile summary/bio
    'experience': List[dict], # Work experience
    'education': List[dict], # Education history
    'skills': List[str],    # Listed skills
    'connections': int,     # Number of connections
    'created_at': str,      # ISO timestamp
    'updated_at': str,      # ISO timestamp
    'raw_data': dict,       # Original parsed data
    'qualification_score': float, # 0.0-1.0 (optional)
    'status': str          # 'pending', 'qualified', 'contacted', etc.
}
```

### Standardized Configuration Schema
```python
STANDARD_CONFIG_SCHEMA = {
    'database': {
        'path': str,
        'backup_enabled': bool,
        'connection_timeout': int
    },
    'parser_config': {
        'batch_size': int,
        'rate_limit': float,
        'cache_enabled': bool,
        'timeout_seconds': int
    },
    'qualification_config': {
        'threshold': float,
        'weights': dict,
        'target_roles': List[str],
        'target_companies': List[str]
    },
    'ai_config': {
        'model': str,
        'api_key': str,
        'temperature': float,
        'max_tokens': int
    },
    'notification_config': {
        'email_provider': str,
        'smtp_settings': dict,
        'templates': dict,
        'batch_size': int
    }
}
```

## Error Handling Patterns

### Consistent Error Response Format
```python
STANDARD_ERROR_RESPONSE = {
    'success': bool,
    'data': Any,           # None if success=False
    'error': {
        'code': str,       # Error code
        'message': str,    # Human-readable message
        'details': dict,   # Additional error context
        'timestamp': str   # ISO timestamp
    } if not success else None
}
```

This interface mapping provides a comprehensive foundation for implementing adapters that bridge the architectural differences between function-based and class-based modules, ensuring smooth data flow and consistent behavior across the entire system.