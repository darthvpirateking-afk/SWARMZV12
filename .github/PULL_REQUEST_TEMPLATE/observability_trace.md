# PR: Observability / Trace Schema Change

## Type
- [ ] New log event type
- [ ] Log field renamed/removed (breaking - ADR required)
- [ ] Sampling or retention policy changed
- [ ] Status endpoint changed
- [ ] Redaction rule added

## Log event checklist
- [ ] New event includes all base fields: `ts, agent_id, trace_id, event, decision, inputs_hash, outcome`
- [ ] `inputs_hash` used instead of raw inputs
- [ ] No PII in non-redacted fields
- [ ] Sensitive fields added to `REDACTED_FIELDS` if needed

## Sampling checklist
- [ ] Failures sampled at 100% - never reduced
- [ ] Success sample rate is configurable
- [ ] High-volume event: estimated log volume documented

## CI gates
- [ ] `pytest tests/test_observability.py` green
- [ ] `pytest tests/test_replay_harness.py` green
- [ ] `mypy --strict` zero errors
- [ ] Branch coverage >= 85%
- [ ] No raw PII in test fixtures
