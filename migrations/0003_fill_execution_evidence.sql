BEGIN;

ALTER TABLE fills
    ADD COLUMN reference_price NUMERIC(38, 18),
    ADD COLUMN slippage_quote NUMERIC(38, 18);

COMMIT;
