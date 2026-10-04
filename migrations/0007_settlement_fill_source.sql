BEGIN;

ALTER TABLE fills
    DROP CONSTRAINT IF EXISTS fills_source_check;

ALTER TABLE fills
    ADD CONSTRAINT fills_source_check
    CHECK (source IN ('simulated', 'settlement', 'exchange'));

COMMIT;
