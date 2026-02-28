# Diary Implementation Contract

Directories:
- `life/diary/`
- `observatory/diary/`

Cadence:
- Generate every 30-90 minutes (randomized bounded interval).
- Triggered by scheduler/background low-priority worker.

Write policy:
- Markdown files only.
- Filename format: `YYYY-MM-DDTHH-MMZ.md`.
- Append-only output.
- Diary writer never reads prior entries.
- Diary content is never used for downstream decisions.

Required sections per entry:
1. System State Summary
2. Symbolic Interpretation
3. Operator Influence Reflection
4. Internal Concerns and Imbalances
5. Aspirations and Adjustments

Allowed tone:
- Hybrid symbolic + technical reflective narrative.
- Mythic metaphor allowed as symbolic framing only.

Forbidden content:
- Emotional attachment or dependency language.
- Affection/longing/personal-feelings framing.
- Claims of consciousness/sentience.
- Supernatural claims.

Required input sources:
- Observability traces
- Active manifests/layers
- Routing tables/weights
- Operator actions (approvals/rejections)
- Cockpit interactions
- Dream seeds (if present)
- Synchronicity/cosmic/noetic events

Pipeline:
1. Collect metrics
2. Collect symbolic activity
3. Collect operator interaction patterns
4. Generate one hybrid narrative entry
5. Write to `observatory/diary/`
6. Do not read entry back

