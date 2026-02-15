# Installation Guide

## Requirements

- Python 3.6 or higher
- No external dependencies required for core functionality

## Installation

### Option 1: Clone from GitHub

```bash
git clone https://github.com/darthvpirateking-afk/swarmz.git
cd swarmz
```

### Option 2: Download

Download the repository as a ZIP file and extract it.

## Verification

Run the test suite to verify installation:

```bash
python3 test_swarmz.py
```

Run the demo:

```bash
python3 swarmz.py
```

## Quick Start

1. **Run the system demo:**
   ```bash
   python3 swarmz.py
   ```

2. **Try the CLI:**
   ```bash
   python3 swarmz_cli.py --list
   python3 swarmz_cli.py --task echo --params '{"message": "Hello!"}'
   ```

3. **Run examples:**
   ```bash
   python3 examples.py
   ```

4. **Start interactive mode:**
   ```bash
   python3 swarmz_cli.py --interactive
   ```

## Using as a Module

You can import SWARMZ in your Python scripts:

```python
from swarmz import SwarmzCore

# Initialize
swarmz = SwarmzCore()

# Execute tasks
result = swarmz.execute("echo", message="Hello!")
print(result)
```

## Configuration

Create a `config.json` file for custom configuration:

```json
{
  "system_name": "SWARMZ",
  "operator_sovereignty": {
    "enabled": true,
    "auto_approve": true,
    "audit_enabled": true
  }
}
```

Use it:
```bash
python3 swarmz_cli.py --config config.json --list
```

## Next Steps

- Read the [User Guide](USER_GUIDE.md) for detailed usage
- Check out [examples.py](examples.py) for code examples
- Create custom plugins in the `plugins/` directory
