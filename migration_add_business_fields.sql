-- Migration: Add owner_name and service_area to businesses table
-- Run this ONLY if you already have an existing businesses table
-- (New installations should use schema.sql instead)

-- Add owner_name column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'businesses' AND column_name = 'owner_name'
    ) THEN
        ALTER TABLE businesses ADD COLUMN owner_name VARCHAR(255);
        RAISE NOTICE 'Added owner_name column';
    ELSE
        RAISE NOTICE 'owner_name column already exists';
    END IF;
END $$;

-- Add service_area column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'businesses' AND column_name = 'service_area'
    ) THEN
        ALTER TABLE businesses ADD COLUMN service_area VARCHAR(255);
        RAISE NOTICE 'Added service_area column';
    ELSE
        RAISE NOTICE 'service_area column already exists';
    END IF;
END $$;

-- Verify the changes
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'businesses'
ORDER BY ordinal_position;
