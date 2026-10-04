BEGIN;

ALTER TABLE risk_observations
    DROP CONSTRAINT IF EXISTS risk_observations_state_check;

ALTER TABLE risk_observations
    ADD CONSTRAINT risk_observations_state_check
    CHECK (state IN ('satisfied', 'warning', 'violated', 'unassessed'));

COMMIT;
