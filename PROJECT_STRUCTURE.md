# SWARMZ Project Structure

> 🟢 **Status: SHIP NOW** — See [SWARMZ_RELEASE_READINESS.md](SWARMZ_RELEASE_READINESS.md) for full release decision.  
> 📖 **Vision** — See [SWARMZ_VISION_BRIEF.md](SWARMZ_VISION_BRIEF.md) for platform direction.

This repository contains both the **Python-based SWARMZ** system and the new **TypeScript-based SWARMZ Ultimate Layout**.

## Release & Vision Documents

| Document | Purpose |
|---|---|
| [SWARMZ_RELEASE_READINESS.md](SWARMZ_RELEASE_READINESS.md) | Go / deferred decision summary with per-area gate status |
| [SWARMZ_VISION_BRIEF.md](SWARMZ_VISION_BRIEF.md) | Platform trajectory, architecture rationale, and contributor guide |
| [ROADMAP.md](ROADMAP.md) | v1.0 → v2.0 milestone plan |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Deep-dive technical architecture |

## Repository Overview

### Release Docs Index

- `README.md` - Main project documentation with current "Ship Now Status"
- `SWARMZ_RELEASE_READINESS.md` - Current go/no-go release readiness summary
- `SWARMZ_LIVE_READINESS_TODO.md` - Deferred optional live-infra checklist and resume steps

### Python Implementation (Original)
Located in root directory:
- `swarmz.py` - Core system
- `swarmz_cli.py` - Command-line interface
- `test_swarmz.py` - Test suite (14 tests)
- `plugins/` - Plugin system
- `swarmz_runtime/` - Runtime components

**Documentation:**
- `README.md` - Main documentation
- `ARCHITECTURE.md` - Python architecture details
- `USER_GUIDE.md` - Usage instructions

**Testing:**
```bash
python3 test_swarmz.py
```

### TypeScript Implementation (New)
Located in `src/` directory:
- Implements the 9-layer SWARMZ Ultimate Layout architecture
- 46 TypeScript files across 9 architectural layers
- Comprehensive type definitions
- Working example and tests

**Documentation:**
- `SWARMZ_TYPESCRIPT_LAYOUT.md` - TypeScript architecture

**Building & Testing:**
```bash
npm install        # Install dependencies
npm run build      # Compile TypeScript
npm test           # Run tests (10 tests)
node dist/example.js  # Run example
```

## Browser Smoke Tests

Browser smoke tests validate both main operator-console surfaces using Playwright.

```
frontend/
├── tests/smoke/
│   └── console.spec.ts   ← smoke tests for Command + Status console surfaces
├── playwright.config.ts  ← Playwright configuration (Chromium + Firefox)
```

**Running locally:**
```bash
cd frontend
npm run build          # Build the frontend
npm run test:smoke     # Run browser smoke tests
```

**CI:** The `browser-smoke` job in `.github/workflows/ci.yml` installs Chromium and Firefox,
builds the frontend, then runs the full smoke suite. Reports are uploaded as CI artifacts.

### For Python SWARMZ
```bash
# Run demo
python3 swarmz.py

# Interactive mode
python3 swarmz_cli.py --interactive

# List capabilities
python3 swarmz_cli.py --list
```

### For TypeScript SWARMZ
```bash
# Install and build
npm install
npm run build

# Run example
node dist/example.js

# Run tests
npm test
```

## Key Differences

### Python Implementation
- **Focus**: Operator sovereignty and extensible plugin system
- **Architecture**: 3-layer design (Interface → Core → Capability)
- **Approach**: Dynamic task execution with plugins
- **Best for**: Immediate operational use

### TypeScript Implementation  
- **Focus**: Architectural separation and behavioral control
- **Architecture**: 9-layer design with strict separation
- **Approach**: Structured flow through isolated layers
- **Best for**: Complex systems requiring predictable behavior

## Development Status

### Python System
✅ Fully operational  
✅ 14 tests passing  
✅ Plugin system working  
✅ CLI and API interfaces ready

### TypeScript System
✅ Architecture implemented  
✅ 10 tests passing  
✅ Example demonstrating full flow  
✅ Zero security vulnerabilities  
✅ Type-safe with strict TypeScript

## Future Integration

The two implementations can coexist:
1. **Python** handles rapid prototyping and operator sovereignty
2. **TypeScript** provides structured, predictable execution
3. They could be integrated via APIs or message passing
4. Each serves different operational needs

## Files Added in This PR

### TypeScript Architecture
- `src/types.ts` - Core type definitions
- `src/index.ts` - Main entry point
- `src/example.ts` - Working example
- `src/__tests__/swarmz.test.ts` - Test suite

### Layer Implementations (9 layers)
1. `src/interface/` - Interface layer (4 files)
2. `src/cognition/` - Cognition core (5 files)
3. `src/swarm/` - Swarm orchestrator (4 files)
4. `src/workers/` - Workers (3 files)
5. `src/actions/` - Action layer (4 files)
6. `src/commit/` - Commit engine (3 files)
7. `src/memory/` - Memory layer (5 JSON files)
8. `src/metrics/` - Metrics spine (4 files)
9. `src/evolution/` - Evolution engine (4 files)

### Configuration
- `tsconfig.json` - TypeScript configuration
- `package.json` - Node.js dependencies
- `jest.config.json` - Test configuration

### Documentation
- `SWARMZ_TYPESCRIPT_LAYOUT.md` - Architecture guide

## Testing

Both systems have independent test suites:

```bash
# Python tests (original system)
python3 test_swarmz.py
# Result: 14 tests, all passing

# TypeScript tests (new architecture)
npm test
# Result: 10 tests, all passing
```

## Security

Both implementations have been scanned:
- ✅ Python: No known vulnerabilities
- ✅ TypeScript: CodeQL scan - 0 alerts

## License

MIT License (see LICENSE file)

## Contributing

- Python system: Follow existing plugin architecture
- TypeScript system: Maintain layer separation principles
- Both: Add tests for new features
