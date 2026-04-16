-- Projects table for grouping leads by address/property
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address TEXT NOT NULL,
    property_type VARCHAR(50),
    estimated_value DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for address lookups
CREATE INDEX IF NOT EXISTS idx_projects_address ON projects(address);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);