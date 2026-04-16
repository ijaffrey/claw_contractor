-- Project enrichments table for lead enrichment data (SQLite compatible)
CREATE TABLE IF NOT EXISTS project_enrichments (
    id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
    project_id TEXT NOT NULL,
    lead_id TEXT,
    enrichment_type TEXT NOT NULL,
    enrichment_data TEXT,
    data_source TEXT,
    confidence_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Index for project lookups
CREATE INDEX IF NOT EXISTS idx_project_enrichments_project_id ON project_enrichments(project_id);
CREATE INDEX IF NOT EXISTS idx_project_enrichments_lead_id ON project_enrichments(lead_id);
CREATE INDEX IF NOT EXISTS idx_project_enrichments_type ON project_enrichments(enrichment_type);