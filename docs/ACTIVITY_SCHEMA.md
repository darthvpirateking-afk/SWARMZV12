# NEXUSMON Activity Schema

## Schema Version: 1.0

### Required Fields
- `schema_version`: The version of the schema used.
- `event_id`: A unique identifier for the event (SHA-256 hash).
- `event_type`: The type of the event (e.g., `process_start`, `file_write`).
- `timestamp`: ISO 8601 timestamp of the event.

### Optional Fields
- `parent_event_id`: The `event_id` of the parent event, if applicable.
- `tags`: A list of tags associated with the event.

### Event ID Generation
The `event_id` is computed as the SHA-256 hash of the canonical JSON representation of the event, excluding the `event_id` field itself.

### Validation
Events must conform to the schema and include all required fields. Use the `validate_event` function in `core/activity_schema.py` to validate events.
