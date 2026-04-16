-- Project enrichments table for additional project data
CREATE TABLE IF NOT EXISTS project_enrichments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    enrichment_type VARCHAR(50) NOT NULL,
    data_source VARCHAR(100),
    enrichment_data JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_project_enrichments_project_id ON project_enrichments(project_id);
CREATE INDEX IF NOT EXISTS idx_project_enrichments_type ON project_enrichments(enrichment_type);
CREATE INDEX IF NOT EXISTS idx_project_enrichments_data_source ON project_enrichments(data_source);