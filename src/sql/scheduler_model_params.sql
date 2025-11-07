CREATE TABLE IF NOT EXISTS scheduler_model_params (
    account TEXT PRIMARY KEY,
    w_engagement FLOAT DEFAULT 0.6,
    w_relevance FLOAT DEFAULT 0.4,
    learning_rate FLOAT DEFAULT 0.05,
    updated_at TIMESTAMPTZ DEFAULT now()
);
