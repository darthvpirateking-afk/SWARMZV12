# Installation Guide

## Requirements

- Python 3.6 or higher
- No external dependencies required for core functionality

## Installation

### Option 1: Clone from GitHub

```bash
git clone https://github.com/darthvpirateking-afk/nexusmon.git
cd nexusmon
```

### Option 2: Download

Download the repository as a ZIP file and extract it.

## Verification

Run the test suite to verify installation:

```bash
python3 test_nexusmon.py
```

Run the demo:

```bash
python3 nexusmon.py
```

## Quick Start

1. **Run the system demo:**
   ```bash
   python3 nexusmon.py
   ```

2. **Try the CLI:**
   ```bash
   python3 nexusmon_cli.py --list
   python3 nexusmon_cli.py --task echo --params '{"message": "Hello!"}'
   ```

3. **Run examples:**
   ```bash
   python3 examples.py
   ```

4. **Start interactive mode:**
   ```bash
   python3 nexusmon_cli.py --interactive
   ```

## Using as a Module

You can import NEXUSMON in your Python scripts:

```python
from nexusmon import NexusmonCore

# Initialize
nexusmon = NexusmonCore()

# Execute tasks
result = nexusmon.execute("echo", message="Hello!")
print(result)
```

## Configuration

Create a `config.json` file for custom configuration:

```json
{
  "system_name": "NEXUSMON",
  "operator_sovereignty": {
    "enabled": true,
    "auto_approve": true,
    "audit_enabled": true
  }
}
```

Use it:
```bash
python3 nexusmon_cli.py --config config.json --list
```

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for detailed usage
- Check out [examples.py](examples.py) for code examples
- Create custom plugins in the `plugins/` directory


