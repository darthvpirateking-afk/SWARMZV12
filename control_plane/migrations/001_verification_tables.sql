-- 001_verification_tables.sql
-- Postgres schema for the VerificationRunner persistent scheduler.
--
-- Tables:
--   verification_jobs     – one row per verification job (state-machine driven)
--   verification_outcomes – append-only ledger of final outcomes
--
-- NOTIFY channel: vr_jobs

BEGIN;

-- ── verification_jobs ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verification_jobs (
    job_id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    dedupe_key              TEXT        NOT NULL UNIQUE,

    -- provenance
    decision_id             TEXT        NOT NULL,
    action_id               TEXT        NOT NULL,
    action_type             TEXT        NOT NULL,
    config_hash             TEXT        NOT NULL DEFAULT '',
    trace_id                TEXT,

    -- timing
    selected_at             TIMESTAMPTZ NOT NULL,
    deadline_at             TIMESTAMPTZ NOT NULL,

    -- state reference
    baseline_state_offset   BIGINT      NOT NULL DEFAULT 0,

    -- verification spec
    verify_spec             JSONB       NOT NULL,
    verify_spec_hash        TEXT        NOT NULL,

    -- rollback
    rollback_action_type    TEXT,
    rollback_params         JSONB       DEFAULT '{}'::jsonb,

    -- target
    target                  JSONB       DEFAULT '{}'::jsonb,

    -- state machine
    status                  TEXT        NOT NULL DEFAULT 'QUEUED'
                            CHECK (status IN (
                                'QUEUED', 'WAITING', 'PASSED', 'FAILED',
                                'EXPIRED', 'CANCELLED', 'DEADLETTERED'
                            )),
    attempts                INT         NOT NULL DEFAULT 0,
    max_attempts            INT         NOT NULL DEFAULT 3,
    last_error              TEXT,

    -- lease
    lease_owner             TEXT,
    lease_expires_at        TIMESTAMPTZ,

    -- exactly-once guards
    final_status            TEXT,
    final_outcome_emitted_at TIMESTAMPTZ,
    final_outcome_event_type TEXT,

    -- rollback tracking
    rollback_triggered_at   TIMESTAMPTZ,
    rollback_action_id      TEXT,

    -- housekeeping
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vj_status_deadline
    ON verification_jobs (status, deadline_at);
CREATE INDEX IF NOT EXISTS idx_vj_lease_expires
    ON verification_jobs (lease_expires_at);


-- ── verification_outcomes (append-only) ───────────────────────────────
CREATE TABLE IF NOT EXISTS verification_outcomes (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id                  UUID        NOT NULL REFERENCES verification_jobs(job_id),
    decision_id             TEXT        NOT NULL,
    action_id               TEXT        NOT NULL,
    status                  TEXT        NOT NULL,
    payload                 JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vo_job_id
    ON verification_outcomes (job_id);


-- ── helper: auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION trg_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS verification_jobs_updated ON verification_jobs;
CREATE TRIGGER verification_jobs_updated
    BEFORE UPDATE ON verification_jobs
    FOR EACH ROW EXECUTE FUNCTION trg_update_timestamp();

COMMIT;
