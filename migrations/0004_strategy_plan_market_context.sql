BEGIN;

ALTER TABLE strategy_plans
    ADD COLUMN venue TEXT,
    ADD COLUMN base_asset TEXT,
    ADD COLUMN quote_asset TEXT;

COMMIT;
