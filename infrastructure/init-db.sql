-- Database initialization script for test environment
-- This script creates the necessary tables and initial data for testing

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    subject TEXT,
    content TEXT,
    status VARCHAR(50) DEFAULT 'new',
    source VARCHAR(50) DEFAULT 'email',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    thread_id VARCHAR(255),
    message_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    sender VARCHAR(255),
    recipient VARCHAR(255),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create contractors table
CREATE TABLE IF NOT EXISTS contractors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    services TEXT,
    active BOOLEAN DEFAULT true,
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id),
    contractor_id UUID REFERENCES contractors(id),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    content JSONB,
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_thread_id ON conversations(thread_id);
CREATE INDEX IF NOT EXISTS idx_contractors_email ON contractors(email);
CREATE INDEX IF NOT EXISTS idx_contractors_active ON contractors(active);
CREATE INDEX IF NOT EXISTS idx_notifications_lead_id ON notifications(lead_id);
CREATE INDEX IF NOT EXISTS idx_notifications_contractor_id ON notifications(contractor_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);

-- Insert test contractors
INSERT INTO contractors (name, email, phone, services, active) VALUES 
('John Smith Plumbing', 'john@smithplumbing.com', '555-0101', 'plumbing,emergency repairs,water heaters', true),
('ABC Electrical Services', 'info@abcelectrical.com', '555-0102', 'electrical,wiring,panel upgrades', true),
('Perfect HVAC Solutions', 'service@perfecthvac.com', '555-0103', 'hvac,heating,cooling,maintenance', true),
('Reliable Roofing Co', 'contact@reliableroofing.com', '555-0104', 'roofing,gutters,repairs', true),
('Pro Handyman Services', 'help@prohandyman.com', '555-0105', 'general repairs,carpentry,painting', true)
ON CONFLICT (email) DO NOTHING;

-- Insert test leads
INSERT INTO leads (name, email, phone, subject, content, status, source) VALUES 
('Alice Johnson', 'alice@example.com', '555-1001', 'Kitchen sink repair needed', 'My kitchen sink is leaking and I need someone to fix it ASAP', 'new', 'email'),
('Bob Wilson', 'bob@example.com', '555-1002', 'Electrical outlet installation', 'Need to install 3 new outlets in my home office', 'contacted', 'email'),
('Carol Davis', 'carol@example.com', '555-1003', 'HVAC system maintenance', 'Annual maintenance for my heating and cooling system', 'qualified', 'email'),
('David Brown', 'david@example.com', '555-1004', 'Roof leak repair', 'Water is coming through the roof in my bedroom', 'new', 'email'),
('Emma White', 'emma@example.com', '555-1005', 'Bathroom renovation', 'Looking for help with complete bathroom remodel', 'new', 'email')
ON CONFLICT DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_contractors_updated_at BEFORE UPDATE ON contractors FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO test_user;
-- OAuth tokens table for secure token storage
-- Designed with encryption, security, and data retention in mind

-- Create extension for encryption if not exists
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum for token types
CREATE TYPE oauth_token_type AS ENUM ('access_token', 'refresh_token', 'id_token');
CREATE TYPE oauth_token_status AS ENUM ('active', 'expired', 'revoked', 'invalid');

-- Create oauth_tokens table with security considerations
CREATE TABLE IF NOT EXISTS oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_email VARCHAR(255) NOT NULL,
    service_provider VARCHAR(50) NOT NULL DEFAULT 'gmail',
    client_id VARCHAR(255) NOT NULL,
    token_type oauth_token_type NOT NULL,
    encrypted_token TEXT NOT NULL, -- Encrypted using pgcrypto
    token_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for quick lookups
    scope TEXT, -- Comma-separated OAuth scopes
    expires_at TIMESTAMP WITH TIME ZONE,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status oauth_token_status NOT NULL DEFAULT 'active',
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    auto_delete_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > issued_at),
    CONSTRAINT valid_usage CHECK (usage_count >= 0)
);

-- Create indexes for performance and security
CREATE INDEX idx_oauth_tokens_user_service ON oauth_tokens(user_email, service_provider);
CREATE INDEX idx_oauth_tokens_status ON oauth_tokens(status);
CREATE INDEX idx_oauth_tokens_expires_at ON oauth_tokens(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_oauth_tokens_token_hash ON oauth_tokens(token_hash);
CREATE INDEX idx_oauth_tokens_auto_delete ON oauth_tokens(auto_delete_at) WHERE auto_delete_at IS NOT NULL;

-- Create unique constraint to prevent duplicate active tokens
CREATE UNIQUE INDEX idx_oauth_tokens_unique_active 
ON oauth_tokens(user_email, service_provider, token_type) 
WHERE status = 'active';

-- Row Level Security (RLS) policies
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;
