"""Tests for the Rollback Framework (P0.2)"""

import pytest
from pathlib import Path
import shutil
import json
from core.rollback import RollbackEngine

# --------------------------------------------------------------------------
# Test Fixtures
# --------------------------------------------------------------------------


@pytest.fixture
def test_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace for testing file operations."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "file_a.txt").write_text("Version 1")
    (workspace / "file_b.txt").write_text("Original Content")
    return workspace


@pytest.fixture
def rollback_engine(tmp_path: Path) -> RollbackEngine:
    """Initialize the RollbackEngine in a temporary vault directory."""
    vault_dir = tmp_path / "rollback_vault"
    return RollbackEngine(vault_dir=str(vault_dir))


# --------------------------------------------------------------------------
# Core Functionality Tests
# --------------------------------------------------------------------------


def test_begin_transaction_creates_directory(rollback_engine: RollbackEngine):
    """Test that beginning a transaction creates a dedicated directory in the vault."""
    transaction = rollback_engine.begin_transaction()
    assert transaction.transaction_dir.exists()
    assert transaction.transaction_dir.is_dir()
    assert (transaction.transaction_dir / "transaction.log").exists()


def test_snapshot_file_copies_content(
    rollback_engine: RollbackEngine, test_workspace: Path
):
    """Test that a file snapshot correctly copies the file to the transaction vault."""
    file_to_snapshot = test_workspace / "file_a.txt"

    transaction = rollback_engine.begin_transaction()
    transaction.snapshot_file(file_to_snapshot)

    assert len(transaction.snapshots) == 1
    snapshot = transaction.snapshots[0]
    assert snapshot.resource_type == "file"
    assert Path(snapshot.resource_id).name == "file_a.txt"

    snapshot_path = Path(snapshot.snapshot_path)
    assert snapshot_path.exists()
    assert snapshot_path.read_text() == "Version 1"


def test_commit_cleans_up_transaction_directory(rollback_engine: RollbackEngine):
    """Test that committing a transaction removes its directory from the vault."""
    transaction = rollback_engine.begin_transaction()
    transaction_dir = transaction.transaction_dir
    assert transaction_dir.exists()

    transaction.commit()

    assert not transaction_dir.exists()
    assert transaction.committed is True


def test_rollback_restores_file_content(
    rollback_engine: RollbackEngine, test_workspace: Path
):
    """Test that a rollback correctly restores a modified file to its snapshot state."""
    file_to_modify = test_workspace / "file_a.txt"
    original_content = file_to_modify.read_text()

    transaction = rollback_engine.begin_transaction()
    transaction.snapshot_file(file_to_modify)

    # Modify the file after snapshotting
    file_to_modify.write_text("Version 2 - Modified")
    assert file_to_modify.read_text() != original_content

    # Perform the rollback
    transaction.rollback()

    # Check if the file is restored
    assert file_to_modify.read_text() == original_content
    assert transaction.rolled_back is True
    assert not transaction.transaction_dir.exists()


def test_rollback_recreates_deleted_file(
    rollback_engine: RollbackEngine, test_workspace: Path
):
    """Test that a rollback can restore a file that was deleted after its snapshot was taken."""
    file_to_delete = test_workspace / "file_b.txt"
    assert file_to_delete.exists()

    transaction = rollback_engine.begin_transaction()
    transaction.snapshot_file(file_to_delete)

    # Delete the file
    file_to_delete.unlink()
    assert not file_to_delete.exists()

    # Rollback
    transaction.rollback()

    # Check if the file is restored
    assert file_to_delete.exists()
    assert file_to_delete.read_text() == "Original Content"


# --------------------------------------------------------------------------
# State and Edge Case Tests
# --------------------------------------------------------------------------


def test_cannot_commit_twice(rollback_engine: RollbackEngine):
    """Test that an exception is raised if commit is called more than once."""
    transaction = rollback_engine.begin_transaction()
    transaction.commit()
    with pytest.raises(RuntimeError):
        transaction.commit()


def test_cannot_rollback_twice(rollback_engine: RollbackEngine, test_workspace: Path):
    """Test that an exception is raised if rollback is called more than once."""
    transaction = rollback_engine.begin_transaction()
    transaction.snapshot_file(test_workspace / "file_a.txt")
    transaction.rollback()
    with pytest.raises(RuntimeError):
        transaction.rollback()


def test_cannot_commit_after_rollback(
    rollback_engine: RollbackEngine, test_workspace: Path
):
    """Test that an exception is raised if commit is called after a rollback."""
    transaction = rollback_engine.begin_transaction()
    transaction.snapshot_file(test_workspace / "file_a.txt")
    transaction.rollback()
    with pytest.raises(RuntimeError):
        transaction.commit()


def test_snapshotting_non_existent_file_does_not_fail(rollback_engine: RollbackEngine):
    """Test that attempting to snapshot a non-existent file is handled gracefully."""
    non_existent_file = Path("non_existent_file.txt")
    transaction = rollback_engine.begin_transaction()
    # This should log a warning but not raise an exception
    transaction.snapshot_file(non_existent_file)
    assert len(transaction.snapshots) == 0
    transaction.commit()  # Should still be able to commit


def test_transaction_log_is_written_correctly(
    rollback_engine: RollbackEngine, test_workspace: Path
):
    """Verify that the transaction log contains the correct sequence of events."""
    file_a = test_workspace / "file_a.txt"

    transaction = rollback_engine.begin_transaction()
    log_file = transaction.transaction_dir / "transaction.log"

    transaction.snapshot_file(file_a)
    file_a.write_text("New content")

    # Read log content *before* rollback, as rollback deletes the log file
    log_content_before_rollback = log_file.read_text()

    transaction.rollback()

    # Now, assert against the content read before deletion
    events = [
        json.loads(line) for line in log_content_before_rollback.strip().split("\n")
    ]

    # The log should contain events up to the point of rollback
    assert len(events) >= 2  # at least begin and snapshot
    assert events[0]["event"] == "begin"
    assert events[1]["event"] == "snapshot_file"
    assert events[1]["resource_id"] == str(file_a)

    # Check that the final log written during rollback is also correct
    # We can't read the file, but we can infer the final events were logged before deletion
    final_events = [
        json.loads(line)
        for line in transaction.log_content_before_delete.strip().split("\n")
    ]
    assert len(final_events) == 5
    assert final_events[0]["event"] == "begin"
    assert final_events[1]["event"] == "snapshot_file"
    assert final_events[2]["event"] == "rollback_started"
    assert final_events[3]["event"] == "restore_file"
    assert final_events[4]["event"] == "rollback_finished"
