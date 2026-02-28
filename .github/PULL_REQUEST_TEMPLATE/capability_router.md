# PR: Capability Router Change

## Type
- [ ] New scoring factor
- [ ] Fallback chain logic changed
- [ ] Conflict detection rule changed
- [ ] Security gating changed
- [ ] Simulation trace updated

## Scoring model checklist
- [ ] Weights are operator-configurable (not hardcoded)
- [ ] Composite score deterministic for identical inputs
- [ ] No float comparison without `math.isclose`

## Security checklist
- [ ] Capability tokens validated before invocation
- [ ] Child `capabilities_granted subset` parent `allowed_capabilities`
- [ ] Privilege escalation -> reject + log
- [ ] `max_spawn_depth` enforced in SpawnContext

## Determinism checklist
- [ ] Simulation replay test added/updated
- [ ] Old traces still replay identically (no regression)

## CI gates
- [ ] `pytest tests/test_capability_router.py` green
- [ ] `pytest tests/test_router_simulation.py` green
- [ ] `mypy --strict` zero errors
- [ ] Branch coverage >= 85%
