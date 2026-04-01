import os
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
import enum

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///leads.db')

# Create base class for models
Base = declarative_base()

# Enums for status fields
class LeadStatus(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"

class NotificationType(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"

class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"

# Lead model
class Lead(Base):
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    notes = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship to notifications
    notifications = relationship("NotificationLog", back_populates="lead", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', email='{self.email}', status='{self.status.value}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'source': self.source,
            'status': self.status.value,
            'notes': self.notes,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

# NotificationLog model
class NotificationLog(Base):
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    message = Column(Text, nullable=True)
    recipient = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Relationship to lead
    lead = relationship("Lead", back_populates="notifications")
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, lead_id={self.lead_id}, type='{self.type.value}', status='{self.status.value}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'type': self.type.value,
            'status': self.status.value,
            'message': self.message,
            'recipient': self.recipient,
            'error_message': self.error_message,
            'attempts': self.attempts,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'extra_data': self.extra_data
        }

# Database engine and session
engine = None
SessionLocal = None

def create_database_engine(database_url: str = None):
    """Create and configure database engine"""
    global engine, SessionLocal
    
    if database_url is None:
        database_url = DATABASE_URL
    
    # Special handling for SQLite
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv('DEBUG') == 'true'
        )
    else:
        engine = create_engine(
            database_url,
            echo=os.getenv('DEBUG') == 'true'
        )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database engine created with URL: {database_url}")
    return engine

def get_db_session() -> Session:
    """Get database session"""
    if SessionLocal is None:
        create_database_engine()
    
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error creating database session: {str(e)}")
        raise

def init_database(database_url: str = None):
    """Initialize database and create all tables"""
    try:
        create_database_engine(database_url)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def drop_database():
    """Drop all database tables"""
    try:
        if engine is None:
            create_database_engine()
        
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"Error dropping database: {str(e)}")
        return False

def migrate_database():
    """Run database migrations"""
    try:
        if engine is None:
            create_database_engine()
        
        # Check if tables exist and create missing ones
        Base.metadata.create_all(bind=engine)
        
        # Add any custom migration logic here
        _run_custom_migrations()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        return False

def _run_custom_migrations():
    """Run any custom migration scripts"""
    try:
        db = get_db_session()
        
        # Migration 1: Ensure default values for existing records
        leads_without_status = db.query(Lead).filter(Lead.status.is_(None)).all()
        for lead in leads_without_status:
            lead.status = LeadStatus.NEW
        
        notifications_without_status = db.query(NotificationLog).filter(NotificationLog.status.is_(None)).all()
        for notification in notifications_without_status:
            notification.status = NotificationStatus.PENDING
        
        # Migration 2: Add indexes if they don't exist (handled by SQLAlchemy)
        
        db.commit()
        logger.info("Custom migrations completed")
        
    except Exception as e:
        logger.error(f"Error running custom migrations: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_database_info():
    """Get database information and statistics"""
    try:
        db = get_db_session()
        
        lead_count = db.query(Lead).count()
        active_leads = db.query(Lead).filter(Lead.is_active == True).count()
        notification_count = db.query(NotificationLog).count()
        
        # Count by status
        status_counts = {}
        for status in LeadStatus:
            count = db.query(Lead).filter(Lead.status == status).count()
            status_counts[status.value] = count
        
        # Count by notification type
        notification_type_counts = {}
        for notification_type in NotificationType:
            count = db.query(NotificationLog).filter(NotificationLog.type == notification_type).count()
            notification_type_counts[notification_type.value] = count
        
        info = {
            'total_leads': lead_count,
            'active_leads': active_leads,
            'total_notifications': notification_count,
            'lead_status_counts': status_counts,
            'notification_type_counts': notification_type_counts,
            'database_url': DATABASE_URL
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting database info: {str(e)}")
        return None
    finally:
        db.close()

def check_database_health():
    """Check database connectivity and health"""
    try:
        db = get_db_session()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

# Context manager for database sessions
class DatabaseSession:
    def __init__(self):
        self.db = None
    
    def __enter__(self):
        self.db = get_db_session()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            if exc_type:
                self.db.rollback()
            else:
                self.db.commit()
            self.db.close()

# CRUD operations for Lead
class LeadRepository:
    @staticmethod
    def create_lead(db: Session, lead_data: dict) -> Lead:
        """Create a new lead"""
        lead = Lead(**lead_data)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead
    
    @staticmethod
    def get_lead(db: Session, lead_id: int) -> Optional[Lead]:
        """Get lead by ID"""
        return db.query(Lead).filter(Lead.id == lead_id).first()
    
    @staticmethod
    def get_lead_by_email(db: Session, email: str) -> Optional[Lead]:
        """Get lead by email"""
        return db.query(Lead).filter(Lead.email == email).first()
    
    @staticmethod
    def get_leads(db: Session, skip: int = 0, limit: int = 100, status: LeadStatus = None) -> List[Lead]:
        """Get leads with pagination and optional status filter"""
        query = db.query(Lead).filter(Lead.is_active == True)
        if status:
            query = query.filter(Lead.status == status)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_lead(db: Session, lead_id: int, lead_data: dict) -> Optional[Lead]:
        """Update lead"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            for key, value in lead_data.items():
                setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(lead)
        return lead
    
    @staticmethod
    def delete_lead(db: Session, lead_id: int) -> bool:
        """Soft delete lead"""
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.is_active = False
            lead.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

# CRUD operations for NotificationLog
class NotificationRepository:
    @staticmethod
    def create_notification(db: Session, notification_data: dict) -> NotificationLog:
        """Create a new notification log"""
        notification = NotificationLog(**notification_data)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_notification(db: Session, notification_id: int) -> Optional[NotificationLog]:
        """Get notification by ID"""
        return db.query(NotificationLog).filter(NotificationLog.id == notification_id).first()
    
    @staticmethod
    def get_notifications_by_lead(db: Session, lead_id: int) -> List[NotificationLog]:
        """Get all notifications for a lead"""
        return db.query(NotificationLog).filter(NotificationLog.lead_id == lead_id).order_by(NotificationLog.timestamp.desc()).all()
    
    @staticmethod
    def update_notification_status(db: Session, notification_id: int, status: NotificationStatus, error_message: str = None) -> Optional[NotificationLog]:
        """Update notification status"""
        notification = db.query(NotificationLog).filter(NotificationLog.id == notification_id).first()
        if notification:
            notification.status = status
            notification.attempts += 1
            if error_message:
                notification.error_message = error_message
            if status == NotificationStatus.SENT:
                notification.sent_at = datetime.utcnow()
            elif status == NotificationStatus.DELIVERED:
                notification.delivered_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
        return notification

# Initialize database on module import
if __name__ != "__main__":
    try:
        create_database_engine()
    except Exception as e:
        logger.warning(f"Could not initialize database on import: {str(e)}")
# Import ConversationState model
from conversation_schema import ConversationState
from conversation_schema import ConversationState

# Export for easy importing
__all__ = ['Base', 'Lead', 'LeadStatus', 'NotificationLog', 'NotificationType', 'NotificationStatus', 'ConversationState', 'get_db_session', 'create_database_engine']
# Import ConversationState from conversation_schema to register it with Base
# This ensures conversation_states table is created when init_database() is called
try:
    from conversation_schema import ConversationState
    # Register the conversation model with the main Base
    ConversationState.__table__.metadata = Base.metadata
    ConversationState.__table__._set_parent_with_dispatch(Base.metadata)
except ImportError:
    logger.warning("conversation_schema module not found - conversation tables will not be created")


class UserToken(Base):
    """OAuth token storage."""
    __tablename__ = 'user_tokens'
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), unique=True, nullable=False)
    access_token = Column(String(2048))
    refresh_token = Column(String(2048))
    token_expires_at = Column(String(50))
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())
