-- PostgreSQL Complete Schema for Job Outreach Pipeline
-- Run this to set up the entire database from scratch

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================
-- CORE TABLES
-- ============================================

-- Runs table
CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    phase VARCHAR(50) DEFAULT 'discovery',
    jobs_found INTEGER DEFAULT 0,
    jobs_filtered INTEGER DEFAULT 0,
    companies_eligible INTEGER DEFAULT 0,
    companies_researched INTEGER DEFAULT 0,
    companies_contacted INTEGER DEFAULT 0,
    contacts_found INTEGER DEFAULT 0,
    personal_contacts_found INTEGER DEFAULT 0,
    emails_queued INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    shortfall_reason TEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    company_domain VARCHAR(255),
    role_title VARCHAR(500) NOT NULL,
    location VARCHAR(255) NOT NULL,
    location_matched BOOLEAN DEFAULT FALSE,
    experience_years INTEGER,
    posted_date DATE,
    source_url TEXT NOT NULL,
    snippet TEXT,
    fit_score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'discovered',
    filter_reason TEXT,
    fetched_text TEXT,
    embedding vector(1536),
    -- JobSpy fields
    job_source VARCHAR(50),  -- 'linkedin', 'naukri', 'indeed', 'glassdoor', 'ziprecruiter'
    job_type VARCHAR(50),  -- 'fulltime', 'parttime', 'contract', 'internship', 'temporary'
    is_remote BOOLEAN DEFAULT FALSE,
    salary_info VARCHAR(255),
    company_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_company ON jobs(company_name);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_run ON jobs(run_id);

-- Companies table
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    domain VARCHAR(255),
    industry VARCHAR(255),
    notes TEXT,
    research_status VARCHAR(50) DEFAULT 'pending',
    research_attempts INTEGER DEFAULT 0,
    researched_at TIMESTAMP,
    last_contacted_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_companies_research_status ON companies(research_status);

-- Contacts table
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    title VARCHAR(255),
    email_type VARCHAR(50) DEFAULT 'unknown',
    priority INTEGER DEFAULT 3,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    source_type VARCHAR(50),
    linkedin_url TEXT,
    tracking_token UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_score INTEGER,
    mx_valid BOOLEAN,
    source_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'discovered',
    inferred BOOLEAN DEFAULT FALSE,
    approved BOOLEAN DEFAULT FALSE,
    outreach_status VARCHAR(50) DEFAULT 'pending',
    template_used VARCHAR(50),
    job_experience_years INTEGER,
    last_contacted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_token ON contacts(tracking_token);
CREATE INDEX idx_contacts_priority ON contacts(priority);
CREATE INDEX idx_contacts_outreach_status ON contacts(outreach_status);

-- Evidence table
CREATE TABLE evidence (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    evidence_type VARCHAR(50) DEFAULT 'page_mention',
    confidence_contribution DECIMAL(3,2) DEFAULT 0.1,
    surrounding_text TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evidence_contact ON evidence(contact_id);

-- Validations table
CREATE TABLE validations (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    validator VARCHAR(50) NOT NULL,
    result VARCHAR(50),
    score INTEGER,
    details JSONB,
    validated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Outreach table
CREATE TABLE outreach (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    subject VARCHAR(500) NOT NULL,
    resume_file VARCHAR(255) NOT NULL,
    template_used VARCHAR(50),
    status VARCHAR(50) DEFAULT 'queued',
    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP,
    bounced_at TIMESTAMP,
    replied_at TIMESTAMP,
    reply_type VARCHAR(50),
    reply_notes TEXT,
    message_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_outreach_contact ON outreach(contact_id);
CREATE INDEX idx_outreach_status ON outreach(status);
CREATE INDEX idx_outreach_scheduled ON outreach(scheduled_for);

-- Opens table
CREATE TABLE opens (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    outreach_id INTEGER REFERENCES outreach(id) ON DELETE CASCADE,
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    user_agent TEXT,
    ip_hash TEXT,
    is_machine_open BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_opens_contact ON opens(contact_id);
CREATE INDEX idx_opens_outreach ON opens(outreach_id);

-- Schedules table
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT 'Daily Run',
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    enabled BOOLEAN DEFAULT TRUE,
    max_jobs INTEGER DEFAULT 50,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schedules (name, cron_expression, timezone, enabled, max_jobs)
VALUES ('Daily Morning Run', '0 3 * * *', 'Asia/Kolkata', TRUE, 50);

-- Settings, suppression, cache, auth tables, etc.
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO settings (key, value) VALUES
    ('send_window_start', '09:00'),
    ('send_window_end', '17:00'),
    ('min_company_delay_seconds', '120'),
    ('max_company_delay_seconds', '300'),
    ('cooldown_days', '90');

CREATE TABLE suppression (
    id SERIAL PRIMARY KEY,
    email_hash TEXT NOT NULL UNIQUE,
    reason VARCHAR(100) NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE provider_usage (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    calls INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    estimated_cost DECIMAL(10, 2) DEFAULT 0.00,
    UNIQUE(provider, date)
);

CREATE TABLE cache_search (
    id SERIAL PRIMARY KEY,
    query_hash TEXT NOT NULL UNIQUE,
    results TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cache_search_expires ON cache_search(expires_at);

CREATE TABLE cache_pages (
    id SERIAL PRIMARY KEY,
    url_hash TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cache_pages_expires ON cache_pages(expires_at);

CREATE TABLE gmail_auth (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    refresh_token TEXT NOT NULL,
    access_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
