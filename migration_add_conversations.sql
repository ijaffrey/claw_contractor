-- Migration: Add conversations table and qualification_step to leads
-- Run this ONLY if you already have an existing leads table
-- (New installations should use schema.sql instead)

-- Add qualification_step column to leads if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'leads' AND column_name = 'qualification_step'
    ) THEN
        ALTER TABLE leads ADD COLUMN qualification_step INTEGER DEFAULT 1;
        RAISE NOTICE 'Added qualification_step column to leads table';
    ELSE
        RAISE NOTICE 'qualification_step column already exists';
    END IF;
END $$;

-- Create conversations table if it doesn't exist
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'customer' or 'assistant'
    message TEXT NOT NULL,
    email_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for conversations table
CREATE INDEX IF NOT EXISTS idx_leads_thread_id ON leads(email_thread_id);
CREATE INDEX IF NOT EXISTS idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Verify the changes
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('leads', 'conversations')
ORDER BY table_name, ordinal_position;
