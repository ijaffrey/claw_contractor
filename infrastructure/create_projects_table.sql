-- Projects table for grouping leads by address/property (SQLite compatible)
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    address TEXT NOT NULL,
    property_type TEXT,
    estimated_value REAL,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for address lookups
CREATE INDEX IF NOT EXISTS idx_projects_address ON projects(address);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);