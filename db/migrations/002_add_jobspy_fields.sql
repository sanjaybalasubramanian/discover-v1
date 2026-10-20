-- Migration: Add JobSpy fields to jobs table
-- Date: 2026-10-13
-- Description: Add job_source, job_type, is_remote, salary_info, company_url fields for JobSpy integration

-- Add new columns
ALTER TABLE jobs 
  ADD COLUMN IF NOT EXISTS job_source VARCHAR(50),
  ADD COLUMN IF NOT EXISTS job_type VARCHAR(50),
  ADD COLUMN IF NOT EXISTS is_remote BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS salary_info VARCHAR(255),
  ADD COLUMN IF NOT EXISTS company_url VARCHAR(500);

-- Add comments for documentation
COMMENT ON COLUMN jobs.job_source IS 'Job board source: linkedin, naukri, indeed, glassdoor, ziprecruiter';
COMMENT ON COLUMN jobs.job_type IS 'Employment type: fulltime, parttime, contract, internship, temporary';
COMMENT ON COLUMN jobs.is_remote IS 'Whether the job is remote';
COMMENT ON COLUMN jobs.salary_info IS 'Formatted salary range (e.g., ₹1200000-1800000/yearly)';
COMMENT ON COLUMN jobs.company_url IS 'Direct URL to company website';

-- Create index for job_source for filtering by source
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(job_source);
CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(is_remote);
