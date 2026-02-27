#!/usr/bin/env python
"""Initialize the database for testing."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def init_database():
    """Initialize database for testing."""
    try:
        # Initialize JSONL-based storage
        from swarmz_runtime.storage.db import Database

        db = Database(data_dir="data")
        print("✓ Database initialized successfully")

        # Run any pending migrations
        try:
            from addons.schema_version import run_migrations

            applied = run_migrations(data_dir="data")
            if applied:
                print(f"✓ Applied migrations: {', '.join(applied)}")
            else:
                print("✓ No pending migrations")
        except ImportError:
            print("✓ No migration system available (optional)")
        except Exception as e:
            print(f"⚠ Migration failed (non-fatal): {e}")

        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
