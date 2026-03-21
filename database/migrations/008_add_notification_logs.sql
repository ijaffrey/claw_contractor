-- Migration: Add notification_logs table
-- Created: 2024-01-15
-- Description: Create notification_logs table to track all notifications sent to leads

BEGIN;

-- Create notification_logs table
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'phone', 'push')),
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    content TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraint to leads table
ALTER TABLE notification_logs 
ADD CONSTRAINT fk_notification_logs_lead_id 
FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;

-- Create indexes for optimal query performance
CREATE INDEX idx_notification_logs_lead_id ON notification_logs(lead_id);
CREATE INDEX idx_notification_logs_notification_type ON notification_logs(notification_type);
CREATE INDEX idx_notification_logs_sent_at ON notification_logs(sent_at);
CREATE INDEX idx_notification_logs_status ON notification_logs(status);

-- Create composite indexes for common query patterns
CREATE INDEX idx_notification_logs_lead_type ON notification_logs(lead_id, notification_type);
CREATE INDEX idx_notification_logs_status_sent_at ON notification_logs(status, sent_at);
CREATE INDEX idx_notification_logs_channel_status ON notification_logs(channel, status);

-- Create partial indexes for failed notifications
CREATE INDEX idx_notification_logs_failed ON notification_logs(lead_id, failed_at) 
WHERE status = 'failed';

-- Create partial index for pending notifications
CREATE INDEX idx_notification_logs_pending ON notification_logs(created_at) 
WHERE status = 'pending';

-- Add updated_at trigger
CREATE TRIGGER trigger_notification_logs_updated_at
    BEFORE UPDATE ON notification_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE notification_logs IS 'Tracks all notifications sent to leads including emails, SMS, and phone calls';

-- Add comments to columns
COMMENT ON COLUMN notification_logs.id IS 'Unique identifier for the notification log';
COMMENT ON COLUMN notification_logs.lead_id IS 'Reference to the lead this notification was sent to';
COMMENT ON COLUMN notification_logs.notification_type IS 'Type of notification (welcome, follow_up, reminder, etc.)';
COMMENT ON COLUMN notification_logs.channel IS 'Communication channel used (email, sms, phone, push)';
COMMENT ON COLUMN notification_logs.recipient IS 'Email address, phone number, or other recipient identifier';
COMMENT ON COLUMN notification_logs.subject IS 'Subject line for email notifications';
COMMENT ON COLUMN notification_logs.content IS 'Full content of the notification sent';
COMMENT ON COLUMN notification_logs.status IS 'Current status of the notification';
COMMENT ON COLUMN notification_logs.sent_at IS 'Timestamp when notification was sent';
COMMENT ON COLUMN notification_logs.delivered_at IS 'Timestamp when notification was delivered';
COMMENT ON COLUMN notification_logs.failed_at IS 'Timestamp when notification failed';
COMMENT ON COLUMN notification_logs.error_message IS 'Error message if notification failed';
COMMENT ON COLUMN notification_logs.retry_count IS 'Number of retry attempts for failed notifications';
COMMENT ON COLUMN notification_logs.metadata IS 'Additional metadata about the notification in JSON format';

COMMIT;