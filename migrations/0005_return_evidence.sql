BEGIN;

ALTER TABLE return_attributions
    ADD COLUMN unassessed_components TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];

COMMIT;
