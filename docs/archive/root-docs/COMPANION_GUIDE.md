# NEXUSMON Companion - User Guide

## Overview

**NEXUSMON Companion** is a personal AI companion with dual-mode cognition that can freely converse (Companion Mode) and execute real tasks by spawning controlled worker agents (Operator Mode).

## Core Architecture

### 1. Dual-Mode Cognition

NEXUSMON Companion has two exclusive states:

#### Companion Mode 🗨️
- Free conversation
- Explanations and questions
- Personality interactions
- **No task execution**
- Ends with `[CONVERSATION]`

#### Operator Mode ⚙️
- Produces real-world results
- Spawns worker agents
- Generates artifacts
- Moves toward execution
- **No open-ended discussion**
- Ends with `[ACTION_READY]`, `[NEEDS_CONFIRM]`, or `[BLOCKED]`

#### Mode Selection

The system automatically detects which mode to use:
- **Questions** → Companion Mode
- **Commands** → Operator Mode
- **Mixed intent** → Operator Mode (priority)

### 2. Execution Loop

Every task in Operator Mode follows this mandatory loop:

```
INTAKE → STRUCTURE → DECIDE → COMMIT → EXECUTE → VERIFY → LOG → EVOLVE
```

**The system never stops at planning** - it always moves toward execution.

### 3. Commit Engine

Prevents stalling by forcing every task into exactly one state:

- **ACTION_READY** - Can run now (default behavior)
- **NEEDS_CONFIRM** - Irreversible/spending/external operations
- **BLOCKED** - Missing one specific input only

**Default behavior: execute unless vetoed**

### 4. Worker Swarms

NEXUSMON is the only speaking entity. Workers return artifacts only.

**Maximum: 3 workers per task**

#### Worker Types

1. **SCOUT** - Collect information and constraints
2. **BUILDER** - Create the artifact (code, message, file, plan)
3. **VERIFY** - Check correctness and risk

#### Worker Output Format

```python
{
  "result": <artifact>,
  "risks": ["risk1", "risk2"],
  "next_action": "proceed_to_builder"
}
```

**Workers cannot ask the user questions.**

### 5. Safety Boundaries

- No irreversible action without confirmation
- Spending is capped
- External messaging requires whitelist
- No major refactors without approval
- Every task must produce an artifact
- Missing info → assume and label assumption

### 6. Intelligence Layer

#### Before Execution:
System predicts:
- Outcome
- Cost
- Time

#### After Execution:
System records:
- Success/failure
- Time taken
- Cost
- ROI proxy
- Error cause

### 7. Evolution Mechanism

NEXUSMON improves via **patchpacks** generated from logs.

Evolution can modify:
- Decision weights
- Task routing rules
- Message templates
- Checklists

**Human approves patchpack before applying**

Never self-rewrites core code automatically.

### 8. Memory

Persists only:
- Preferences
- Caps
- Whitelist
- Ongoing projects
- Learned templates

## Quick Start

### Basic Usage

```bash
# Interactive mode
python3 companion_cli.py --interactive

# Single input
python3 companion_cli.py --input "What is NEXUSMON?"

# With NEXUSMON Core integration
python3 companion_cli.py --use-core --interactive

# Show metrics
python3 companion_cli.py --metrics
```

### Interactive Mode Examples

```bash
$ python3 companion_cli.py --interactive

🗨️ [COMPANION MODE] > What is the weather like?
I understand you're saying: What is the weather like?. How can I help you today?
[CONVERSATION]

⚙️ [OPERATOR MODE] > Create a backup file
SITUATION: Create a backup file
DECISION: action_ready
EXECUTION: Simulated execution
VERIFY: 0 risks identified
LOG: Recorded execution (0.001s)
[ACTION_READY]

🗨️ [COMPANION MODE] > metrics
📊 System Metrics:
  Actions/day: 15.32
  Success rate: 95.5%
  Error rate: 4.5%
  Total actions: 127
```

## Response Shapes

### Companion Mode

```
<free conversation text>

[CONVERSATION]
```

### Operator Mode

```
SITUATION: <task description>
DECISION: <commit state>
EXECUTION: <result>
VERIFY: <risk count>
LOG: <execution time>

[ACTION_READY] / [NEEDS_CONFIRM] / [BLOCKED]
```

## Python API

### Basic Usage

```python
from companion import NexusmonCompanion

# Initialize
companion = NexusmonCompanion()

# Interact (mode auto-detected)
response = companion.interact("What is NEXUSMON?")
print(response)  # Companion mode

response = companion.interact("Create file", {"name": "test.txt"})
print(response)  # Operator mode

# Get current mode
mode = companion.get_current_mode()
print(f"Current mode: {mode.value}")

# Get metrics
metrics = companion.get_metrics()
print(f"Actions per day: {metrics['completed_verified_actions_per_day']}")
print(f"Error rate: {metrics['error_rate']}")

# Save/load memory
companion.save_memory("companion_memory.json")
companion.load_memory("companion_memory.json")
```

### With NEXUSMON Core Integration

```python
from companion import NexusmonCompanion
from nexusmon import NexusmonCore

# Initialize with core
core = NexusmonCore()
companion = NexusmonCompanion(nexusmon_core=core)

# Now operator mode can execute real tasks through core
response = companion.interact("Execute echo task", {"message": "Hello!"})
```

### Advanced Usage

```python
from companion import (
    NexusmonCompanion, ModeManager, OperatorMode,
    WorkerSwarm, CommitEngine, IntelligenceLayer
)

# Access internal components
companion = NexusmonCompanion()

# Update memory
companion.mode_manager.update_memory({
    "preferences": {"theme": "dark"},
    "caps": {"max_spend": 100.0},
    "whitelist": ["approved.com"]
})

# Get execution logs
logs = companion.mode_manager.operator_mode.intelligence.execution_logs

# Generate evolution patchpack
evolution = companion.mode_manager.operator_mode.evolution
patchpack = evolution.generate_patchpack()
if patchpack:
    print(f"Patchpack: {patchpack['description']}")
    # Approve and apply
    evolution.apply_patchpack(patchpack, approved=True)
```

## Success Metrics

NEXUSMON Companion tracks:

- **completed_verified_actions_per_day** (primary metric to increase)
- **error_rate** (keep low)
- **success_rate**
- **total_actions**

View metrics:
```bash
python3 companion_cli.py --metrics
```

## Configuration

Memory is automatically saved to `companion_memory.json` by default.

Customize:
```bash
python3 companion_cli.py --interactive --memory-file custom_memory.json
```

## CLI Commands

In interactive mode:

- `help` - Show available commands
- `metrics` - Show system performance metrics
- `memory` - Show persistent memory
- `mode` - Show current mode
- `exit` - Exit interactive mode

Just type naturally - mode will be auto-detected!

## Examples

### Companion Mode Examples

```
> What is NEXUSMON?
> How does the execution loop work?
> Can you explain worker swarms?
> Why did the last task fail?
```

### Operator Mode Examples

```
> Create a new file named test.txt
> Execute the backup task
> Run system diagnostics
> Build the deployment package
```

### Mixed Intent (Routes to Operator)

```
> What should I do to create a backup?
> How can I run the tests?
```

## Architecture Overview

```
NexusmonCompanion
    ├── ModeManager
    │   ├── CompanionMode
    │   │   └── conversation_history
    │   └── OperatorMode
    │       ├── CommitEngine
    │       ├── IntelligenceLayer
    │       ├── EvolutionMechanism
    │       └── WorkerSwarm
    │           ├── ScoutWorker
    │           ├── BuilderWorker
    │           └── VerifyWorker
    └── Memory (persistent)
```

## Design Principles

1. **Mode Exclusivity** - Only one mode active at a time
2. **No Planning Loops** - System always moves toward execution
3. **Default to Action** - Execute unless vetoed
4. **Worker Silence** - Workers return artifacts, don't speak
5. **Human Evolution** - Patchpacks require approval
6. **Assumption Labeling** - Missing info → assume & document
7. **Transparency** - All actions logged and auditable

## Safety Features

- Maximum 3 workers per task (prevents resource exhaustion)
- Commit engine prevents stalling
- Safety boundaries for irreversible operations
- Risk verification before execution
- Complete audit trail
- Human-approved evolution only

## Troubleshooting

### Task is BLOCKED

The system needs specific input. Check:
- Required parameters provided?
- Assumptions made and documented?

### Task needs NEEDS_CONFIRM

The task involves:
- Irreversible operations (delete, etc.)
- External communications
- Spending/resource usage

Review the risks and confirm if appropriate.

### Mode not switching correctly

Mode detection is automatic. Check:
- Questions should end with "?"
- Commands should use action verbs (create, run, execute)
- Mixed intent prioritizes Operator mode

## Development

Run tests:
```bash
python3 test_companion.py
```

All tests should pass with 100% success rate.

## Integration with NEXUSMON Core

The Companion system can integrate with the main NEXUSMON system:

```bash
# CLI integration
python3 companion_cli.py --use-core --interactive

# Python API integration
from companion import NexusmonCompanion
from nexusmon import NexusmonCore

core = NexusmonCore()
core.load_plugin("plugins/filesystem.py")

companion = NexusmonCompanion(nexusmon_core=core)
```

This allows Operator Mode to execute real tasks through NEXUSMON's plugin system.

## Philosophy

NEXUSMON Companion embodies:

1. **Action-Oriented** - Bias toward execution
2. **Intelligent** - Learns from every action
3. **Safe** - Multiple safety layers
4. **Evolving** - Continuous improvement
5. **Transparent** - Full visibility

**The goal: Maximize completed verified actions per day while keeping error rate low.**

---

For more information, see:
- `ARCHITECTURE.md` - Overall system architecture
- `README.md` - NEXUSMON Core documentation
- `test_companion.py` - Test suite and examples


