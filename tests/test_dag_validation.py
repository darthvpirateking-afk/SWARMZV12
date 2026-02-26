# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_dag_validation.py — DAG Cycle Detection Tests
"""

import pytest
from core.dag_validation import is_dag


def test_valid_dag_linear():
    """Linear dependency chain should pass."""
    tasks = [
        {"id": "t1", "dependencies": []},
        {"id": "t2", "dependencies": ["t1"]},
        {"id": "t3", "dependencies": ["t2"]},
    ]
    assert is_dag(tasks) is True


def test_valid_dag_parallel():
    """Parallel tasks with common dependency should pass."""
    tasks = [
        {"id": "t1", "dependencies": []},
        {"id": "t2", "dependencies": ["t1"]},
        {"id": "t3", "dependencies": ["t1"]},
        {"id": "t4", "dependencies": ["t2", "t3"]},
    ]
    assert is_dag(tasks) is True


def test_cyclic_dependency_simple():
    """Simple cycle should be detected."""
    tasks = [
        {"id": "t1", "dependencies": ["t2"]},
        {"id": "t2", "dependencies": ["t1"]},
    ]
    assert is_dag(tasks) is False


def test_cyclic_dependency_complex():
    """Complex cycle should be detected."""
    tasks = [
        {"id": "t1", "dependencies": []},
        {"id": "t2", "dependencies": ["t1", "t4"]},
        {"id": "t3", "dependencies": ["t2"]},
        {"id": "t4", "dependencies": ["t3"]},
    ]
    assert is_dag(tasks) is False


def test_self_dependency():
    """Self-dependency should be detected."""
    tasks = [
        {"id": "t1", "dependencies": ["t1"]},
    ]
    assert is_dag(tasks) is False


def test_empty_task_list():
    """Empty task list should be a valid DAG."""
    tasks = []
    assert is_dag(tasks) is True


def test_no_dependencies():
    """Tasks with no dependencies should be a valid DAG."""
    tasks = [
        {"id": "t1", "dependencies": []},
        {"id": "t2", "dependencies": []},
        {"id": "t3", "dependencies": []},
    ]
    assert is_dag(tasks) is True


def test_missing_dependency():
    """A dependency on a non-existent node should be detected as invalid."""
    tasks = [
        {"id": "t1", "dependencies": ["t99"]},
    ]
    assert is_dag(tasks) is False


def test_diamond_dependency():
    """Diamond dependency structure should pass."""
    tasks = [
        {"id": "t1", "dependencies": []},
        {"id": "t2", "dependencies": ["t1"]},
        {"id": "t3", "dependencies": ["t1"]},
        {"id": "t4", "dependencies": ["t2", "t3"]},
    ]
    assert is_dag(tasks) is True
