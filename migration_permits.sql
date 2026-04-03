-- NYC Permit Scraper Schema Migration
-- Run this in your Supabase SQL Editor

-- Permits table: stores raw permit data from NYC DOB NOW
CREATE TABLE IF NOT EXISTS permits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_filing_number VARCHAR(50) UNIQUE NOT NULL,
    permit_type VARCHAR(100),
    permit_subtype VARCHAR(100),
    permit_status VARCHAR(50),
    filing_date TIMESTAMP WITH TIME ZONE,
    issuance_date TIMESTAMP WITH TIME ZONE,
    expiration_date TIMESTAMP WITH TIME ZONE,
    job_description TEXT,
    building_address TEXT,
    borough VARCHAR(50),
    zip_code VARCHAR(10),
    block VARCHAR(20),
    lot VARCHAR(20),
    bin_number VARCHAR(20),
    community_board VARCHAR(10),
    estimated_job_cost NUMERIC(15, 2),
    owner_name VARCHAR(255),
    owner_phone VARCHAR(50),
    owner_email VARCHAR(255),
    applicant_name VARCHAR(255),
    applicant_license_number VARCHAR(50),
    applicant_license_type VARCHAR(100),
    filing_representative VARCHAR(255),
    work_type VARCHAR(100),
    building_type VARCHAR(100),
    raw_data JSONB,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contractor profiles extracted from permits
CREATE TABLE IF NOT EXISTS contractor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_number VARCHAR(50),
    company_name VARCHAR(255),
    contact_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    license_type VARCHAR(100),
    contractor_role VARCHAR(50) NOT NULL DEFAULT 'general',
    trade_types TEXT[],
    boroughs_active TEXT[],
    total_permits INTEGER DEFAULT 0,
    avg_project_cost NUMERIC(15, 2),
    last_permit_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(license_number, contractor_role)
);

-- Matches between general contractors and subcontractors
CREATE TABLE IF NOT EXISTS permit_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permit_id UUID NOT NULL REFERENCES permits(id) ON DELETE CASCADE,
    gc_profile_id UUID NOT NULL REFERENCES contractor_profiles(id) ON DELETE CASCADE,
    sub_profile_id UUID NOT NULL REFERENCES contractor_profiles(id) ON DELETE CASCADE,
    match_score NUMERIC(5, 2) NOT NULL,
    match_reasons JSONB,
    permit_type_match BOOLEAN DEFAULT FALSE,
    scope_match BOOLEAN DEFAULT FALSE,
    location_match BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(permit_id, gc_profile_id, sub_profile_id)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_permits_filing_number ON permits(job_filing_number);
CREATE INDEX IF NOT EXISTS idx_permits_borough ON permits(borough);
CREATE INDEX IF NOT EXISTS idx_permits_permit_type ON permits(permit_type);
CREATE INDEX IF NOT EXISTS idx_permits_filing_date ON permits(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_permits_status ON permits(permit_status);
CREATE INDEX IF NOT EXISTS idx_permits_scraped_at ON permits(scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_contractor_profiles_license ON contractor_profiles(license_number);
CREATE INDEX IF NOT EXISTS idx_contractor_profiles_role ON contractor_profiles(contractor_role);
CREATE INDEX IF NOT EXISTS idx_contractor_profiles_boroughs ON contractor_profiles USING GIN(boroughs_active);
CREATE INDEX IF NOT EXISTS idx_contractor_profiles_trades ON contractor_profiles USING GIN(trade_types);

CREATE INDEX IF NOT EXISTS idx_permit_matches_permit ON permit_matches(permit_id);
CREATE INDEX IF NOT EXISTS idx_permit_matches_gc ON permit_matches(gc_profile_id);
CREATE INDEX IF NOT EXISTS idx_permit_matches_sub ON permit_matches(sub_profile_id);
CREATE INDEX IF NOT EXISTS idx_permit_matches_score ON permit_matches(match_score DESC);

-- Triggers for updated_at
CREATE TRIGGER update_permits_updated_at
    BEFORE UPDATE ON permits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contractor_profiles_updated_at
    BEFORE UPDATE ON contractor_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify setup
SELECT 'permits table created' AS status, COUNT(*) AS count FROM permits;
SELECT 'contractor_profiles table created' AS status, COUNT(*) AS count FROM contractor_profiles;
SELECT 'permit_matches table created' AS status, COUNT(*) AS count FROM permit_matches;
