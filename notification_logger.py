import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import logging
from contextlib import contextmanager

from database import DatabaseManager


class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    READ = "read"


class NotificationType(Enum):
    CONTRACTOR_ASSIGNMENT = "contractor_assignment"
    CONTRACTOR_REMINDER = "contractor_reminder"
    CONTRACTOR_CANCELLATION = "contractor_cancellation"
    CUSTOMER_HANDOFF = "customer_handoff"
    CUSTOMER_REMINDER = "customer_reminder"
    CUSTOMER_CONFIRMATION = "customer_confirmation"
    SYSTEM_ALERT = "system_alert"


class DeliveryMethod(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationLogger:
    """Handles logging and tracking of all notifications sent during the handoff process."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create notification logging tables if they don't exist."""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handoff_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            delivery_method TEXT NOT NULL,
            recipient_type TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            recipient_contact TEXT NOT NULL,
            subject TEXT,
            message_body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            delivered_at TIMESTAMP,
            read_at TIMESTAMP,
            failed_at TIMESTAMP,
            error_message TEXT,
            metadata TEXT,
            FOREIGN KEY (handoff_id) REFERENCES handoffs (id)
        );
        
        CREATE TABLE IF NOT EXISTS notification_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_log_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            response_code TEXT,
            response_message TEXT,
            error_details TEXT,
            metadata TEXT,
            FOREIGN KEY (notification_log_id) REFERENCES notification_logs (id)
        );
        
        CREATE TABLE IF NOT EXISTS notification_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL UNIQUE,
            notification_type TEXT NOT NULL,
            delivery_method TEXT NOT NULL,
            subject_template TEXT,
            body_template TEXT NOT NULL,
            variables TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_notification_logs_handoff_id 
            ON notification_logs (handoff_id);
        CREATE INDEX IF NOT EXISTS idx_notification_logs_status 
            ON notification_logs (status);
        CREATE INDEX IF NOT EXISTS idx_notification_logs_type 
            ON notification_logs (notification_type);
        CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at 
            ON notification_logs (created_at);
        CREATE INDEX IF NOT EXISTS idx_notification_attempts_log_id 
            ON notification_attempts (notification_log_id);
        """
        
        with self.db_manager.get_connection() as conn:
            conn.executescript(create_tables_sql)
    
    def log_contractor_notification(
        self,
        handoff_id: int,
        contractor_id: str,
        notification_type: NotificationType,
        delivery_method: DeliveryMethod,
        recipient_contact: str,
        subject: Optional[str],
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a notification sent to a contractor.
        
        Args:
            handoff_id: ID of the handoff
            contractor_id: ID of the contractor
            notification_type: Type of notification
            delivery_method: Method of delivery (email, SMS, etc.)
            recipient_contact: Contact information (email, phone, etc.)
            subject: Subject line (for emails)
            message_body: Message content
            metadata: Additional metadata
            
        Returns:
            ID of the created notification log entry
        """
        return self._create_notification_log(
            handoff_id=handoff_id,
            notification_type=notification_type,
            delivery_method=delivery_method,
            recipient_type="contractor",
            recipient_id=contractor_id,
            recipient_contact=recipient_contact,
            subject=subject,
            message_body=message_body,
            metadata=metadata
        )
    
    def log_customer_handoff_message(
        self,
        handoff_id: int,
        customer_id: str,
        notification_type: NotificationType,
        delivery_method: DeliveryMethod,
        recipient_contact: str,
        subject: Optional[str],
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a handoff message sent to a customer.
        
        Args:
            handoff_id: ID of the handoff
            customer_id: ID of the customer
            notification_type: Type of notification
            delivery_method: Method of delivery
            recipient_contact: Contact information
            subject: Subject line
            message_body: Message content
            metadata: Additional metadata
            
        Returns:
            ID of the created notification log entry
        """
        return self._create_notification_log(
            handoff_id=handoff_id,
            notification_type=notification_type,
            delivery_method=delivery_method,
            recipient_type="customer",
            recipient_id=customer_id,
            recipient_contact=recipient_contact,
            subject=subject,
            message_body=message_body,
            metadata=metadata
        )
    
    def _create_notification_log(
        self,
        handoff_id: int,
        notification_type: NotificationType,
        delivery_method: DeliveryMethod,
        recipient_type: str,
        recipient_id: str,
        recipient_contact: str,
        subject: Optional[str],
        message_body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Create a new notification log entry."""
        metadata_json = json.dumps(metadata) if metadata else None
        
        query = """
        INSERT INTO notification_logs (
            handoff_id, notification_type, delivery_method, recipient_type,
            recipient_id, recipient_contact, subject, message_body, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            handoff_id,
            notification_type.value,
            delivery_method.value,
            recipient_type,
            recipient_id,
            recipient_contact,
            subject,
            message_body,
            metadata_json
        )
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            notification_id = cursor.lastrowid
            
        self.logger.info(
            f"Created notification log {notification_id} for {recipient_type} "
            f"{recipient_id} (handoff {handoff_id})"
        )
        
        return notification_id
    
    def update_notification_status(
        self,
        notification_id: int,
        status: NotificationStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a notification.
        
        Args:
            notification_id: ID of the notification log
            status: New status
            error_message: Error message if failed
            metadata: Additional metadata
            
        Returns:
            True if updated successfully
        """
        timestamp_field = None
        if status == NotificationStatus.SENT:
            timestamp_field = "sent_at"
        elif status == NotificationStatus.DELIVERED:
            timestamp_field = "delivered_at"
        elif status == NotificationStatus.READ:
            timestamp_field = "read_at"
        elif status == NotificationStatus.FAILED:
            timestamp_field = "failed_at"
        
        metadata_json = json.dumps(metadata) if metadata else None
        current_time = datetime.now(timezone.utc).isoformat()
        
        if timestamp_field:
            query = f"""
            UPDATE notification_logs 
            SET status = ?, error_message = ?, metadata = ?, {timestamp_field} = ?
            WHERE id = ?
            """
            params = (status.value, error_message, metadata_json, current_time, notification_id)
        else:
            query = """
            UPDATE notification_logs 
            SET status = ?, error_message = ?, metadata = ?
            WHERE id = ?
            """
            params = (status.value, error_message, metadata_json, notification_id)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            success = cursor.rowcount > 0
            
        if success:
            self.logger.info(f"Updated notification {notification_id} status to {status.value}")
        else:
            self.logger.warning(f"Failed to update notification {notification_id} status")
            
        return success
    
    def log_notification_attempt(
        self,
        notification_id: int,
        status: NotificationStatus,
        response_code: Optional[str] = None,
        response_message: Optional[str] = None,
        error_details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log an attempt to send a notification.
        
        Args:
            notification_id: ID of the notification log
            status: Status of the attempt
            response_code: Response code from delivery service
            response_message: Response message
            error_details: Error details if failed
            metadata: Additional metadata
            
        Returns:
            ID of the created attempt log entry
        """
        # Get current attempt number
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(attempt_number), 0) + 1 FROM notification_attempts WHERE notification_log_id = ?",
                (notification_id,)
            )
            attempt_number = cursor.fetchone()[0]
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        query = """
        INSERT INTO notification_attempts (
            notification_log_id, attempt_number, status, response_code,
            response_message, error_details, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            notification_id,
            attempt_number,
            status.value,
            response_code,
            response_message,
            error_details,
            metadata_json
        )
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            attempt_id = cursor.lastrowid
            
            # Update attempts counter in notification log
            conn.execute(
                "UPDATE notification_logs SET attempts = ? WHERE id = ?",
                (attempt_number, notification_id)
            )
        
        # Update notification status
        self.update_notification_status(notification_id, status, error_details)
        
        self.logger.info(
            f"Logged attempt {attempt_number} for notification {notification_id} "
            f"with status {status.value}"
        )
        
        return attempt_id
    
    def get_notification_history(
        self,
        handoff_id: Optional[int] = None,
        recipient_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query notification history with filters.
        
        Args:
            handoff_id: Filter by handoff ID
            recipient_id: Filter by recipient ID
            notification_type: Filter by notification type
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Limit number of results
            
        Returns:
            List of notification log entries
        """
        query = "SELECT * FROM notification_logs WHERE 1=1"
        params = []
        
        if handoff_id is not None:
            query += " AND handoff_id = ?"
            params.append(handoff_id)
            
        if recipient_id is not None:
            query += " AND recipient_id = ?"
            params.append(recipient_id)
            
        if notification_type is not None:
            query += " AND notification_type = ?"
            params.append(notification_type.value)
            
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
            
        if start_date is not None:
            query += " AND created_at >= ?"
            params.append(start_date.isoformat())
            
        if end_date is not None:
            query += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY created_at DESC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_notification_attempts(self, notification_id: int) -> List[Dict[str, Any]]:
        """
        Get all attempts for a specific notification.
        
        Args:
            notification_id: ID of the notification log
            
        Returns:
            List of attempt records
        """
        query = """
        SELECT * FROM notification_attempts 
        WHERE notification_log_id = ? 
        ORDER BY attempt_number
        """
        
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (notification_id,))
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_failed_notifications(
        self,
        max_attempts: int = 3,
        hours_old: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get notifications that have failed and may need retry.
        
        Args:
            max_attempts: Maximum attempts before considering permanently failed
            hours_old: Only consider notifications older than this many hours
            
        Returns:
            List of failed notification records
        """
        query = """
        SELECT * FROM notification_logs 
        WHERE status IN ('failed', 'pending') 
        AND attempts < ? 
        AND datetime(created_at) <= datetime('now', '-{} hours')
        ORDER BY created_at
        """.format(hours_old)
        
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (max_attempts,))
            rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_notification_statistics(
        self,
        handoff_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Args:
            handoff_id: Filter by handoff ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary of statistics
        """
        where_clause = "WHERE 1=1"
        params = []
        
        if handoff_id is not None:
            where_clause += " AND handoff_id = ?"
            params.append(handoff_id)
            
        if start_date is not None:
            where_clause += " AND created_at >= ?"
            params.append(start_date.isoformat())
            
        if end_date is not None:
            where_clause += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        queries = {
            'total': f"SELECT COUNT(*) FROM notification_logs {where_clause}",
            'by_status': f"""
                SELECT status, COUNT(*) as count 
                FROM notification_logs {where_clause} 
                GROUP BY status
            """,
            'by_type': f"""
                SELECT notification_type, COUNT(*) as count 
                FROM notification_logs {where_clause} 
                GROUP BY notification_type
            """,
            'by_method': f"""
                SELECT delivery_method, COUNT(*) as count 
                FROM notification_logs {where_clause} 
                GROUP BY delivery_method
            """,
            'success_rate': f"""
                SELECT 
                    ROUND(
                        CAST(SUM(CASE WHEN status IN ('sent', 'delivered', 'read') THEN 1 ELSE 0 END) AS FLOAT) 
                        / COUNT(*) * 100, 2
                    ) as success_rate
                FROM notification_logs {where_clause}
            """
        }
        
        stats = {}
        
        with self.db_manager.get_connection() as conn:
            # Total count
            cursor = conn.execute(queries['total'], params)
            stats['total'] = cursor.fetchone()[0]
            
            # By status
            cursor = conn.execute(queries['by_status'], params)
            stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # By type
            cursor = conn.execute(queries['by_type'], params)
            stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # By method
            cursor = conn.execute(queries['by_method'], params)
            stats['by_method'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Success rate
            cursor = conn.execute(queries['success_rate'], params)
            result = cursor.fetchone()[0]
            stats['success_rate'] = result if result is not None else 0.0
        
        return stats
    
    def cleanup_old_notifications(self, days_old: int = 90) -> int:
        """
        Clean up old notification logs.
        
        Args:
            days_old: Delete notifications older than this many days
            
        Returns:
            Number of records deleted
        """
        query = """
        DELETE FROM notification_logs 
        WHERE datetime(created_at) <= datetime('now', '-{} days')
        """.format(days_old)
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query)
            deleted_count = cursor.rowcount
        
        self.logger.info(f"Cleaned up {deleted_count} old notification records")
        return deleted_count
    
    def save_notification_template(
        self,
        template_name: str,
        notification_type: NotificationType,
        delivery_method: DeliveryMethod,
        subject_template: Optional[str],
        body_template: str,
        variables: Optional[List[str]] = None
    ) -> int:
        """
        Save a notification template.
        
        Args:
            template_name: Unique name for the template
            notification_type: Type of notification
            delivery_method: Delivery method
            subject_template: Subject template with placeholders
            body_template: Body template with placeholders
            variables: List of available variables
            
        Returns:
            ID of the created template
        """
        variables_json = json.dumps(variables) if variables else None
        
        query = """
        INSERT OR REPLACE INTO notification_templates (
            template_name, notification_type, delivery_method,
            subject_template, body_template, variables, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            template_name,
            notification_type.value,
            delivery_method.value,
            subject_template,
            body_template,
            variables_json,
            datetime.now(timezone.utc).isoformat()
        )
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, params)
            template_id = cursor.lastrowid
            
        self.logger.info(f"Saved notification template '{template_name}' with ID {template_id}")
        return template_id
    
    def get_notification_template(
        self,
        template_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a notification template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template data or None if not found
        """
        query = """
        SELECT * FROM notification_templates 
        WHERE template_name = ? AND is_active = TRUE
        """
        
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (template_name,))
            row = cursor.fetchone()
        
        return dict(row) if row else None