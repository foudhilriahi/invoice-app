
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    document_path TEXT,
    raw_text TEXT,
    structured_data JSONB,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the 'factures' table with similar structure to 'invoices'
-- This allows for handling both English and French invoices
-- while maintaining a unified schema for processing
-- and storage in the database.
-- The 'factures' table will also include a timestamp for when the data was processed.
-- This is useful for tracking the freshness of the data and for auditing purposes.
-- The 'structured_data' field will store parsed and structured information from the invoices.
CREATE TABLE IF NOT EXISTS factures (
    id SERIAL PRIMARY KEY,
    document_path TEXT,
    raw_text TEXT,
    structured_data JSONB,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
-- on the 'created_at' field and for full-text search on the 'raw_text' field.
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at);
CREATE INDEX IF NOT EXISTS idx_factures_created_at ON factures(created_at);
CREATE INDEX IF NOT EXISTS idx_invoices_text_search ON invoices USING gin(to_tsvector('english', raw_text));
CREATE INDEX IF NOT EXISTS idx_factures_text_search ON factures USING gin(to_tsvector('english', raw_text));
