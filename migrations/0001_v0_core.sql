BEGIN;

CREATE TABLE opportunities (
    id UUID PRIMARY KEY,
    opportunity_key TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('discovered', 'qualified', 'expired')),
    discovered_at TIMESTAMPTZ NOT NULL,
    qualified_at TIMESTAMPTZ,
    expired_at TIMESTAMPTZ,
    latest_observation_id UUID,
    version BIGINT NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX opportunities_active_key_idx
    ON opportunities (opportunity_key)
    WHERE expired_at IS NULL;

CREATE TABLE opportunity_observations (
    id UUID PRIMARY KEY,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id),
    observed_at TIMESTAMPTZ NOT NULL,
    return_character TEXT NOT NULL CHECK (return_character IN ('variable', 'convergent')),
    expected_net_return NUMERIC(38, 18),
    annualized_equivalent NUMERIC(38, 18),
    expected_cost NUMERIC(38, 18),
    capacity_5bps NUMERIC(38, 8),
    capacity_10bps NUMERIC(38, 8),
    raw_metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE opportunities
    ADD CONSTRAINT opportunities_latest_observation_fk
    FOREIGN KEY (latest_observation_id)
    REFERENCES opportunity_observations(id);

CREATE INDEX opportunity_observations_history_idx
    ON opportunity_observations (opportunity_id, observed_at DESC);

CREATE TABLE strategy_plans (
    id UUID PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    opportunity_observation_id UUID NOT NULL REFERENCES opportunity_observations(id),
    capital_amount NUMERIC(38, 8) NOT NULL,
    capital_currency TEXT NOT NULL,
    execution_mode TEXT NOT NULL CHECK (execution_mode = 'paper'),
    current_revision INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE strategy_plan_revisions (
    strategy_plan_id UUID NOT NULL REFERENCES strategy_plans(id),
    revision INTEGER NOT NULL,
    document JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (strategy_plan_id, revision)
);

CREATE TABLE executions (
    id UUID PRIMARY KEY,
    strategy_plan_id UUID NOT NULL REFERENCES strategy_plans(id),
    state TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode = 'paper'),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);

CREATE TABLE fills (
    id UUID PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES executions(id),
    instrument_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity NUMERIC(38, 18) NOT NULL,
    price NUMERIC(38, 18) NOT NULL,
    notional NUMERIC(38, 8) NOT NULL,
    fee NUMERIC(38, 18) NOT NULL,
    slippage_bps NUMERIC(38, 18) NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('simulated', 'exchange')),
    filled_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE positions (
    id UUID PRIMARY KEY,
    strategy_plan_id UUID NOT NULL REFERENCES strategy_plans(id),
    state TEXT NOT NULL,
    capital NUMERIC(38, 8) NOT NULL,
    current_delta NUMERIC(38, 18) NOT NULL,
    current_delta_pct NUMERIC(38, 18) NOT NULL,
    realized_pnl NUMERIC(38, 18) NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC(38, 18) NOT NULL DEFAULT 0,
    opened_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    version BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE position_legs (
    position_id UUID NOT NULL REFERENCES positions(id),
    instrument_id TEXT NOT NULL,
    quantity NUMERIC(38, 18) NOT NULL,
    notional NUMERIC(38, 8) NOT NULL,
    PRIMARY KEY (position_id, instrument_id)
);

CREATE TABLE return_attributions (
    id UUID PRIMARY KEY,
    position_id UUID NOT NULL REFERENCES positions(id),
    observed_at TIMESTAMPTZ NOT NULL,
    funding NUMERIC(38, 18) NOT NULL DEFAULT 0,
    basis_convergence NUMERIC(38, 18) NOT NULL DEFAULT 0,
    trading_fees NUMERIC(38, 18) NOT NULL DEFAULT 0,
    slippage NUMERIC(38, 18) NOT NULL DEFAULT 0,
    rebalancing_cost NUMERIC(38, 18) NOT NULL DEFAULT 0,
    residual_directional_pnl NUMERIC(38, 18) NOT NULL DEFAULT 0
);

CREATE TABLE risk_observations (
    id UUID PRIMARY KEY,
    position_id UUID NOT NULL REFERENCES positions(id),
    observed_at TIMESTAMPTZ NOT NULL,
    invariant_name TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('satisfied', 'warning', 'violated')),
    observed JSONB NOT NULL,
    limit_value JSONB NOT NULL,
    explanation JSONB
);

CREATE TABLE domain_events (
    id UUID PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_version BIGINT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);

CREATE UNIQUE INDEX domain_events_aggregate_version_idx
    ON domain_events (aggregate_type, aggregate_id, aggregate_version);

CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    domain_event_id UUID NOT NULL UNIQUE REFERENCES domain_events(id),
    topic TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    published_at TIMESTAMPTZ
);

CREATE INDEX outbox_events_pending_idx
    ON outbox_events (created_at)
    WHERE published_at IS NULL;

COMMIT;
