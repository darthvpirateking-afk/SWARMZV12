# SWARMZ Privacy Guard

## Purpose
The Privacy Guard ensures that sensitive data is redacted from event logs to protect user privacy and security.

## Redaction Rules
- **Tokens**: Strings of 32 or more alphanumeric characters.
- **Emails**: Email addresses.
- **Phones**: Phone numbers (with optional country code).

## Integration
The `redact_event` function in `core/redaction.py` applies redaction rules to events before they are logged.