-- Migration: Add notification logs
-- Description: Create tables for tracking notification delivery
-- Date: 2024-01-01

BEGIN;

-- Create enum for notification types
CREATE TYPE notification_type_enum AS ENUM ('contractor', 'customer');

-- Create enum for delivery status
CREATE TYPE delivery_status_enum AS ENUM ('pending', 'sent', 'delivered', 'failed', 'bounced');

-- Create notifications table
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    lead_id BIGINT NOT NULL,
    notification_type notification_type_enum NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivery_status delivery_status_enum DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint to leads table
    CONSTRAINT fk_notifications_lead_id 
        FOREIGN KEY (lead_id) 
        REFERENCES leads(id) 
        ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_recipient_email_format 
        CHECK (recipient_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_subject_length 
        CHECK (LENGTH(TRIM(subject)) > 0),
    CONSTRAINT chk_content_length 
        CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT chk_error_message_when_failed 
        CHECK (
            (delivery_status IN ('failed', 'bounced') AND error_message IS NOT NULL) OR 
            (delivery_status NOT IN ('failed', 'bounced'))
        )
);

-- Create indexes for performance
CREATE INDEX idx_notifications_lead_id ON notifications(lead_id);
CREATE INDEX idx_notifications_notification_type ON notifications(notification_type);
CREATE INDEX idx_notifications_recipient_email ON notifications(recipient_email);
CREATE INDEX idx_notifications_delivery_status ON notifications(delivery_status);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at DESC);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_notifications_lead_type ON notifications(lead_id, notification_type);
CREATE INDEX idx_notifications_status_sent_at ON notifications(delivery_status, sent_at DESC);
CREATE INDEX idx_notifications_type_status ON notifications(notification_type, delivery_status);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_notifications_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_notifications_updated_at();

-- Add comments for documentation
COMMENT ON TABLE notifications IS 'Stores notification delivery logs for contractors and customers';
COMMENT ON COLUMN notifications.id IS 'Primary key identifier';
COMMENT ON COLUMN notifications.lead_id IS 'Foreign key reference to leads table';
COMMENT ON COLUMN notifications.notification_type IS 'Type of notification: contractor or customer';
COMMENT ON COLUMN notifications.recipient_email IS 'Email address of the notification recipient';
COMMENT ON COLUMN notifications.subject IS 'Email subject line';
COMMENT ON COLUMN notifications.content IS 'Email body content';
COMMENT ON COLUMN notifications.sent_at IS 'Timestamp when notification was sent';
COMMENT ON COLUMN notifications.delivery_status IS 'Current delivery status of the notification';
COMMENT ON COLUMN notifications.error_message IS 'Error details if delivery failed';
COMMENT ON COLUMN notifications.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN notifications.updated_at IS 'Timestamp when record was last updated';

-- Create view for notification summary statistics
CREATE VIEW notification_stats AS
SELECT 
    notification_type,
    delivery_status,
    COUNT(*) as count,
    DATE_TRUNC('day', sent_at) as date
FROM notifications
WHERE sent_at IS NOT NULL
GROUP BY notification_type, delivery_status, DATE_TRUNC('day', sent_at);

COMMENT ON VIEW notification_stats IS 'Summary statistics for notification delivery by type and status';

-- Grant permissions (adjust as needed for your application)
-- GRANT SELECT, INSERT, UPDATE ON notifications TO app_user;
-- GRANT USAGE ON SEQUENCE notifications_id_seq TO app_user;
-- GRANT SELECT ON notification_stats TO app_user;

COMMIT;