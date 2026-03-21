"""
Email configuration module for claw_contractor application.

Handles SMTP settings, notification recipients, templates, and policies
with environment-based configuration support.
"""

import os
import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class EmailPriority(Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class SMTPConfig:
    """SMTP server configuration."""
    host: str
    port: int
    use_tls: bool = True
    use_ssl: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    local_hostname: Optional[str] = None
    
    def __post_init__(self):
        """Validate SMTP configuration."""
        if self.use_tls and self.use_ssl:
            raise ValueError("Cannot use both TLS and SSL simultaneously")
        
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")


@dataclass
class RetryPolicy:
    """Email retry policy configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 300.0
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on_timeout: bool = True
    retry_on_connection_error: bool = True
    
    def __post_init__(self):
        """Validate retry policy."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


@dataclass
class RateLimitConfig:
    """Email rate limiting configuration."""
    enabled: bool = True
    max_emails_per_minute: int = 60
    max_emails_per_hour: int = 1000
    max_emails_per_day: int = 10000
    burst_limit: int = 10
    cooldown_period: int = 300  # seconds
    
    def __post_init__(self):
        """Validate rate limiting configuration."""
        if self.max_emails_per_minute <= 0:
            raise ValueError("max_emails_per_minute must be positive")
        
        if self.max_emails_per_hour < self.max_emails_per_minute:
            logger.warning("max_emails_per_hour is less than max_emails_per_minute")
        
        if self.max_emails_per_day < self.max_emails_per_hour:
            logger.warning("max_emails_per_day is less than max_emails_per_hour")


@dataclass
class AttachmentConfig:
    """Email attachment handling configuration."""
    max_size_mb: int = 25
    max_total_size_mb: int = 50
    max_files: int = 10
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.rtf',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        '.zip', '.rar', '.7z', '.csv'
    ])
    blocked_extensions: List[str] = field(default_factory=lambda: [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs',
        '.js', '.jar', '.app', '.deb', '.pkg', '.dmg'
    ])
    scan_for_viruses: bool = True
    quarantine_suspicious: bool = True
    temp_storage_path: str = "/tmp/email_attachments"
    cleanup_after_hours: int = 24
    
    def __post_init__(self):
        """Validate attachment configuration."""
        if self.max_size_mb <= 0:
            raise ValueError("max_size_mb must be positive")
        
        if self.max_total_size_mb < self.max_size_mb:
            raise ValueError("max_total_size_mb must be >= max_size_mb")
        
        if self.max_files <= 0:
            raise ValueError("max_files must be positive")
        
        # Ensure blocked extensions take precedence
        self.allowed_extensions = [
            ext for ext in self.allowed_extensions 
            if ext.lower() not in [blocked.lower() for blocked in self.blocked_extensions]
        ]


@dataclass
class NotificationRecipient:
    """Email notification recipient."""
    email: str
    name: Optional[str] = None
    role: str = "user"
    active: bool = True
    priorities: List[EmailPriority] = field(default_factory=lambda: [EmailPriority.NORMAL])
    
    def __post_init__(self):
        """Validate recipient."""
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid email address: {self.email}")


@dataclass
class TemplateConfig:
    """Email template configuration."""
    base_path: str = "templates/email"
    default_language: str = "en"
    supported_languages: List[str] = field(default_factory=lambda: ["en", "es", "fr"])
    cache_templates: bool = True
    template_extension: str = ".html"
    
    # Template files
    contractor_notification: str = "contractor_notification.html"
    project_update: str = "project_update.html"
    payment_reminder: str = "payment_reminder.html"
    system_alert: str = "system_alert.html"
    welcome: str = "welcome.html"
    password_reset: str = "password_reset.html"
    
    def __post_init__(self):
        """Validate template configuration."""
        if not Path(self.base_path).exists():
            logger.warning(f"Template base path does not exist: {self.base_path}")
        
        if self.default_language not in self.supported_languages:
            raise ValueError(f"Default language {self.default_language} not in supported languages")


class EmailConfig:
    """Main email configuration class with environment support."""
    
    def __init__(self, environment: Optional[Union[str, Environment]] = None):
        """Initialize email configuration for specific environment."""
        if isinstance(environment, str):
            environment = Environment(environment.lower())
        
        self.environment = environment or self._detect_environment()
        self.smtp = self._load_smtp_config()
        self.retry_policy = self._load_retry_policy()
        self.rate_limit = self._load_rate_limit_config()
        self.attachments = self._load_attachment_config()
        self.templates = self._load_template_config()
        self.recipients = self._load_recipients()
        
        # General settings
        self.sender_name = self._get_env("EMAIL_SENDER_NAME", "Claw Contractor System")
        self.sender_email = self._get_env("EMAIL_SENDER_EMAIL", "noreply@clawcontractor.com")
        self.reply_to = self._get_env("EMAIL_REPLY_TO", None)
        self.bounce_email = self._get_env("EMAIL_BOUNCE_ADDRESS", "bounce@clawcontractor.com")
        
        # Notification settings
        self.enable_notifications = self._get_bool("EMAIL_ENABLE_NOTIFICATIONS", True)
        self.enable_system_alerts = self._get_bool("EMAIL_ENABLE_SYSTEM_ALERTS", True)
        self.enable_contractor_notifications = self._get_bool("EMAIL_ENABLE_CONTRACTOR_NOTIFICATIONS", True)
        
        # Security settings
        self.enable_dkim = self._get_bool("EMAIL_ENABLE_DKIM", True)
        self.enable_spf = self._get_bool("EMAIL_ENABLE_SPF", True)
        self.enable_dmarc = self._get_bool("EMAIL_ENABLE_DMARC", True)
        
        self._validate_configuration()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _get_env(self, key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """Get environment variable with environment prefix."""
        env_key = f"{self.environment.value.upper()}_{key}"
        value = os.getenv(env_key) or os.getenv(key, default)
        
        if required and value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        
        return value
    
    def _get_int(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        value = self._get_env(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    def _get_float(self, key: str, default: float) -> float:
        """Get float environment variable."""
        value = self._get_env(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid float value for {key}: {value}, using default: {default}")
            return default
    
    def _get_bool(self, key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = self._get_env(key, str(default))
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def _get_list(self, key: str, default: List[str], separator: str = ",") -> List[str]:
        """Get list environment variable."""
        value = self._get_env(key)
        if not value:
            return default
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def _load_smtp_config(self) -> SMTPConfig:
        """Load SMTP configuration from environment."""
        host = self._get_env("SMTP_HOST", required=True)
        port = self._get_int("SMTP_PORT", 587)
        use_tls = self._get_bool("SMTP_USE_TLS", True)
        use_ssl = self._get_bool("SMTP_USE_SSL", False)
        username = self._get_env("SMTP_USERNAME")
        password = self._get_env("SMTP_PASSWORD")
        timeout = self._get_int("SMTP_TIMEOUT", 30)
        local_hostname = self._get_env("SMTP_LOCAL_HOSTNAME")
        
        return SMTPConfig(
            host=host,
            port=port,
            use_tls=use_tls,
            use_ssl=use_ssl,
            username=username,
            password=password,
            timeout=timeout,
            local_hostname=local_hostname
        )
    
    def _load_retry_policy(self) -> RetryPolicy:
        """Load retry policy from environment."""
        return RetryPolicy(
            max_attempts=self._get_int("EMAIL_RETRY_MAX_ATTEMPTS", 3),
            base_delay=self._get_float("EMAIL_RETRY_BASE_DELAY", 1.0),
            max_delay=self._get_float("EMAIL_RETRY_MAX_DELAY", 300.0),
            exponential_backoff=self._get_bool("EMAIL_RETRY_EXPONENTIAL_BACKOFF", True),
            jitter=self._get_bool("EMAIL_RETRY_JITTER", True),
            retry_on_timeout=self._get_bool("EMAIL_RETRY_ON_TIMEOUT", True),
            retry_on_connection_error=self._get_bool("EMAIL_RETRY_ON_CONNECTION_ERROR", True)
        )
    
    def _load_rate_limit_config(self) -> RateLimitConfig:
        """Load rate limiting configuration from environment."""
        return RateLimitConfig(
            enabled=self._get_bool("EMAIL_RATE_LIMIT_ENABLED", True),
            max_emails_per_minute=self._get_int("EMAIL_RATE_LIMIT_PER_MINUTE", 60),
            max_emails_per_hour=self._get_int("EMAIL_RATE_LIMIT_PER_HOUR", 1000),
            max_emails_per_day=self._get_int("EMAIL_RATE_LIMIT_PER_DAY", 10000),
            burst_limit=self._get_int("EMAIL_RATE_LIMIT_BURST", 10),
            cooldown_period=self._get_int("EMAIL_RATE_LIMIT_COOLDOWN", 300)
        )
    
    def _load_attachment_config(self) -> AttachmentConfig:
        """Load attachment configuration from environment."""
        allowed_extensions = self._get_list(
            "EMAIL_ATTACHMENT_ALLOWED_EXTENSIONS",
            ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.rtf',
             '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
             '.zip', '.rar', '.7z', '.csv']
        )
        
        blocked_extensions = self._get_list(
            "EMAIL_ATTACHMENT_BLOCKED_EXTENSIONS",
            ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs',
             '.js', '.jar', '.app', '.deb', '.pkg', '.dmg']
        )
        
        return AttachmentConfig(
            max_size_mb=self._get_int("EMAIL_ATTACHMENT_MAX_SIZE_MB", 25),
            max_total_size_mb=self._get_int("EMAIL_ATTACHMENT_MAX_TOTAL_SIZE_MB", 50),
            max_files=self._get_int("EMAIL_ATTACHMENT_MAX_FILES", 10),
            allowed_extensions=allowed_extensions,
            blocked_extensions=blocked_extensions,
            scan_for_viruses=self._get_bool("EMAIL_ATTACHMENT_SCAN_VIRUSES", True),
            quarantine_suspicious=self._get_bool("EMAIL_ATTACHMENT_QUARANTINE", True),
            temp_storage_path=self._get_env("EMAIL_ATTACHMENT_TEMP_PATH", "/tmp/email_attachments"),
            cleanup_after_hours=self._get_int("EMAIL_ATTACHMENT_CLEANUP_HOURS", 24)
        )
    
    def _load_template_config(self) -> TemplateConfig:
        """Load template configuration from environment."""
        return TemplateConfig(
            base_path=self._get_env("EMAIL_TEMPLATE_BASE_PATH", "templates/email"),
            default_language=self._get_env("EMAIL_TEMPLATE_DEFAULT_LANGUAGE", "en"),
            supported_languages=self._get_list("EMAIL_TEMPLATE_SUPPORTED_LANGUAGES", ["en", "es", "fr"]),
            cache_templates=self._get_bool("EMAIL_TEMPLATE_CACHE", True),
            template_extension=self._get_env("EMAIL_TEMPLATE_EXTENSION", ".html"),
            contractor_notification=self._get_env("EMAIL_TEMPLATE_CONTRACTOR_NOTIFICATION", "contractor_notification.html"),
            project_update=self._get_env("EMAIL_TEMPLATE_PROJECT_UPDATE", "project_update.html"),
            payment_reminder=self._get_env("EMAIL_TEMPLATE_PAYMENT_REMINDER", "payment_reminder.html"),
            system_alert=self._get_env("EMAIL_TEMPLATE_SYSTEM_ALERT", "system_alert.html"),
            welcome=self._get_env("EMAIL_TEMPLATE_WELCOME", "welcome.html"),
            password_reset=self._get_env("EMAIL_TEMPLATE_PASSWORD_RESET", "password_reset.html")
        )
    
    def _load_recipients(self) -> Dict[str, List[NotificationRecipient]]:
        """Load notification recipients from environment."""
        recipients = {
            "contractors": [],
            "administrators": [],
            "system_alerts": [],
            "payments": [],
            "projects": []
        }
        
        # Load recipients from environment variables
        for category in recipients.keys():
            env_key = f"EMAIL_RECIPIENTS_{category.upper()}"
            recipient_emails = self._get_list(env_key, [])
            
            for email in recipient_emails:
                try:
                    recipients[category].append(NotificationRecipient(
                        email=email,
                        role=category,
                        priorities=[EmailPriority.NORMAL, EmailPriority.HIGH]
                    ))
                except ValueError as e:
                    logger.warning(f"Invalid recipient email in {category}: {e}")
        
        # Default recipients for development
        if self.environment == Environment.DEVELOPMENT:
            dev_email = self._get_env("DEV_EMAIL", "dev@example.com")
            for category in recipients.keys():
                if not recipients[category]:
                    recipients[category].append(NotificationRecipient(
                        email=dev_email,
                        name="Developer",
                        role="developer"
                    ))
        
        return recipients
    
    def _validate_configuration(self):
        """Validate the complete configuration."""
        errors = []
        
        # Validate required settings
        if not self.sender_email:
            errors.append("EMAIL_SENDER_EMAIL is required")
        
        # Validate SMTP configuration
        try:
            # This will raise an exception if invalid
            pass
        except Exception as e:
            errors.append(f"SMTP configuration invalid: {e}")
        
        # Validate recipients
        total_recipients = sum(len(recipients) for recipients in self.recipients.values())
        if total_recipients == 0 and self.environment == Environment.PRODUCTION:
            logger.warning("No email recipients configured for production environment")
        
        # Validate template paths
        template_path = Path(self.templates.base_path)
        if not template_path.exists() and self.environment == Environment.PRODUCTION:
            logger.warning(f"Template directory does not exist: {self.templates.base_path}")
        
        if errors:
            raise ValueError(f"Email configuration errors: {'; '.join(errors)}")
        
        logger.info(f"Email configuration loaded successfully for {self.environment.value} environment")
    
    def get_recipients_by_priority(self, priority: EmailPriority) -> List[NotificationRecipient]:
        """Get all recipients that should receive emails of the given priority."""
        matching_recipients = []
        
        for category_recipients in self.recipients.values():
            for recipient in category_recipients:
                if recipient.active and priority in recipient.priorities:
                    matching_recipients.append(recipient)
        
        return matching_recipients
    
    def get_recipients_by_category(self, category: str) -> List[NotificationRecipient]:
        """Get recipients by category."""
        return self.recipients.get(category, [])
    
    def is_attachment_allowed(self, filename: str, size_mb: float) -> bool:
        """Check if attachment is allowed based on configuration."""
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in [ext.lower() for ext in self.attachments.blocked_extensions]:
            return False
        
        if (self.attachments.allowed_extensions and 
            file_ext not in [ext.lower() for ext in self.attachments.allowed_extensions]):
            return False
        
        # Check size
        if size_mb > self.attachments.max_size_mb:
            return False
        
        return True
    
    def get_template_path(self, template_name: str, language: str = None) -> str:
        """Get full path to email template."""
        language = language or self.templates.default_language
        
        if language not in self.templates.supported_languages:
            language = self.templates.default_language
        
        template_file = getattr(self.templates, template_name, f"{template_name}{self.templates.template_extension}")
        
        return str(Path(self.templates.base_path) / language / template_file)


# Global configuration instance
_email_config = None


def get_email_config(environment: Optional[Union[str, Environment]] = None) -> EmailConfig:
    """Get email configuration instance (singleton pattern)."""
    global _email_config
    
    if _email_config is None or (environment and _email_config.environment != environment):
        _email_config = EmailConfig(environment)
    
    return _email_config


def reload_email_config(environment: Optional[Union[str, Environment]] = None):
    """Reload email configuration."""
    global _email_config
    _email_config = EmailConfig(environment)
    return _email_config