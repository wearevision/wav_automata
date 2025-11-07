create extension if not exists "uuid-ossp";

CREATE TABLE IF NOT EXISTS scheduler_model_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account TEXT,
    prev_w_engagement FLOAT,
    prev_w_relevance FLOAT,
    new_w_engagement FLOAT,
    new_w_relevance FLOAT,
    learning_rate FLOAT,
    updated_by TEXT,
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT now()
);

create index if not exists scheduler_model_audit_account_idx on scheduler_model_audit(account);
create index if not exists scheduler_model_audit_created_idx on scheduler_model_audit(created_at desc);
