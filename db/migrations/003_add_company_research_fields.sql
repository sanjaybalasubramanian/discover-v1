-- Migration: Add research_attempts and researched_at to companies table
-- Date: 2026-10-15
-- Description: Add tracking fields for research agent retry logic and completion timestamp

-- Add new columns to companies table
ALTER TABLE companies 
  ADD COLUMN IF NOT EXISTS research_attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS researched_at TIMESTAMP;

-- Add comments for documentation
COMMENT ON COLUMN companies.research_attempts IS 'Number of times AI agent has attempted to research this company';
COMMENT ON COLUMN companies.researched_at IS 'Timestamp when company research was completed';

-- Update existing companies to have research_attempts = 0
UPDATE companies SET research_attempts = 0 WHERE research_attempts IS NULL;
