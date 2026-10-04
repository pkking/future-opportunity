BEGIN;

ALTER TABLE executions
    ADD COLUMN purpose TEXT NOT NULL DEFAULT 'open';

ALTER TABLE executions
    ADD CONSTRAINT executions_purpose_check
    CHECK (purpose IN ('open', 'close', 'rebalance'));

CREATE INDEX executions_plan_purpose_idx
    ON executions (strategy_plan_id, purpose, started_at);

COMMIT;
