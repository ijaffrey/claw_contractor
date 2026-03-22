from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import db


class NotificationLog(db.Model):
    """
    Model for tracking notification logs sent to leads.
    
    This model stores information about all notifications sent,
    including email notifications, SMS notifications, etc.
    """
    
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    message_content = Column(Text, nullable=True)
    
    # Relationship to Lead model
    lead = relationship("Lead", back_populates="notification_logs")
    
    def __init__(self, lead_id, notification_type, recipient_email, status='pending', message_content=None):
        """
        Initialize a new NotificationLog instance.
        
        Args:
            lead_id (int): ID of the associated lead
            notification_type (str): Type of notification (email, sms, etc.)
            recipient_email (str): Email address of the recipient
            status (str): Status of the notification (pending, sent, failed, etc.)
            message_content (str): Content of the notification message
        """
        self.lead_id = lead_id
        self.notification_type = notification_type
        self.recipient_email = recipient_email
        self.status = status
        self.message_content = message_content
    
    def __repr__(self):
        """String representation of the NotificationLog instance."""
        return f'<NotificationLog {self.id}: {self.notification_type} to {self.recipient_email} ({self.status})>'
    
    def to_dict(self):
        """
        Convert the NotificationLog instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the notification log
        """
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'notification_type': self.notification_type,
            'recipient_email': self.recipient_email,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'message_content': self.message_content
        }
    
    def update_status(self, status):
        """
        Update the status of the notification log.
        
        Args:
            status (str): New status for the notification
        """
        self.status = status
        db.session.commit()
    
    @classmethod
    def create(cls, lead_id, notification_type, recipient_email, status='pending', message_content=None):
        """
        Create a new notification log entry.
        
        Args:
            lead_id (int): ID of the associated lead
            notification_type (str): Type of notification
            recipient_email (str): Email address of the recipient
            status (str): Status of the notification
            message_content (str): Content of the notification message
            
        Returns:
            NotificationLog: The created notification log instance
        """
        notification_log = cls(
            lead_id=lead_id,
            notification_type=notification_type,
            recipient_email=recipient_email,
            status=status,
            message_content=message_content
        )
        db.session.add(notification_log)
        db.session.commit()
        return notification_log
    
    @classmethod
    def get_by_lead_id(cls, lead_id):
        """
        Get all notification logs for a specific lead.
        
        Args:
            lead_id (int): ID of the lead
            
        Returns:
            list: List of NotificationLog instances
        """
        return cls.query.filter_by(lead_id=lead_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_status(cls, status):
        """
        Get all notification logs with a specific status.
        
        Args:
            status (str): Status to filter by
            
        Returns:
            list: List of NotificationLog instances
        """
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_type(cls, notification_type):
        """
        Get all notification logs of a specific type.
        
        Args:
            notification_type (str): Type of notification to filter by
            
        Returns:
            list: List of NotificationLog instances
        """
        return cls.query.filter_by(notification_type=notification_type).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent_logs(cls, limit=100):
        """
        Get the most recent notification logs.
        
        Args:
            limit (int): Number of logs to retrieve
            
        Returns:
            list: List of NotificationLog instances
        """
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()