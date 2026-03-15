-- OpenClaw Trade Assistant Database Schema
-- Run this in your Supabase SQL Editor

-- Create businesses table
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    trade_type VARCHAR(100) NOT NULL,
    brand_voice TEXT,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    phone VARCHAR(50),
    job_type VARCHAR(100),
    description TEXT,
    location TEXT,
    source VARCHAR(50),
    urgency VARCHAR(20),
    status VARCHAR(50) DEFAULT 'new',
    raw_subject TEXT,
    raw_body TEXT,
    email_thread_id VARCHAR(255),
    email_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_leads_business_id ON leads(business_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email_id ON leads(email_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_businesses_updated_at ON businesses;
CREATE TRIGGER update_businesses_updated_at
    BEFORE UPDATE ON businesses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Seed test business (Mike's Plumbing)
INSERT INTO businesses (name, trade_type, brand_voice, email, phone)
VALUES (
    'Mike''s Plumbing',
    'plumbing',
    'Friendly, professional, and reliable. We''re a family-owned plumbing business that treats every customer like family. We respond quickly, explain everything clearly, and always show up on time.',
    'mike@mikesplumbing.com',
    '555-123-4567'
)
ON CONFLICT DO NOTHING;

-- Verify setup
SELECT 'Businesses table created' AS status, COUNT(*) AS count FROM businesses;
SELECT 'Leads table created' AS status, COUNT(*) AS count FROM leads;
