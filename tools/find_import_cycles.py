#!/usr/bin/env python3
"""
Static import-cycle scanner for a Python source tree.

- Walks a directory, parses .py files with ast (no imports executed)
- Builds a directed graph of internal-module dependencies
- Reports strongly connected components (import cycles)
- Optionally writes a Graphviz .dot file for visualization
"""

from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__",
    ".venv", "venv", "env",
    "build", "dist", ".tox",
    ".mypy_cache", ".pytest_cache",
    ".ruff_cache",
    "site-packages",
}


def iter_py_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [dn for dn in dirnames if dn not in EXCLUDE_DIRS and not dn.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(d / fn)
    return files


def module_name_for_file(file: Path, root: Path) -> str:
    rel = file.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]  # strip .py
    return ".".join(parts)


def resolve_from_import(current_mod: str, module: Optional[str], level: int) -> Optional[str]:
    """
    Resolve `from ...module import X` to an absolute-ish module name string.
    """
    if level == 0:
        return module
    cur_parts = current_mod.split(".")
    # If current_mod points to a module (not a package __init__), it still behaves like package context.
    # Dropping `level` segments from the end:
    if level > len(cur_parts):
        base_parts: List[str] = []
    else:
        base_parts = cur_parts[:-level]
    if module:
        base_parts += module.split(".")
    return ".".join(base_parts) if base_parts else None


def collect_imports(file: Path, root: Path, modname: str) -> Set[str]:
    imports: Set[str] = set()
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"))
    except Exception:
        # If a file can’t parse, skip it (or you can choose to fail)
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            resolved = resolve_from_import(modname, node.module, node.level or 0)
            if resolved:
                imports.add(resolved)
    return imports


def build_graph(root: Path) -> Tuple[Dict[str, Set[str]], Set[str]]:
    py_files = iter_py_files(root)
    modules = {module_name_for_file(f, root) for f in py_files}

    graph: Dict[str, Set[str]] = {m: set() for m in modules}

    for f in py_files:
        src_mod = module_name_for_file(f, root)
        deps = collect_imports(f, root, src_mod)

        for dep in deps:
            # Keep only internal edges:
            # 1) direct match: dep is a module in our tree
            # 2) prefix match: dep imports a package/module prefix that exists internally
            if dep in modules:
                graph[src_mod].add(dep)
            else:
                # If someone does "import pkg.sub", we still want edge to pkg if pkg exists
                parts = dep.split(".")
                for i in range(len(parts), 0, -1):
                    prefix = ".".join(parts[:i])
                    if prefix in modules:
                        graph[src_mod].add(prefix)
                        break

    return graph, modules


def tarjans_scc(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Tarjan's algorithm for strongly connected components.
    Returns a list of SCCs (each SCC is a list of nodes).
    """
    index = 0
    stack: List[str] = []
    on_stack: Set[str] = set()
    indices: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph.get(v, ()): 
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            scc: List[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in graph.keys():
        if v not in indices:
            strongconnect(v)

    return sccs


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    sccs = tarjans_scc(graph)
    cycles: List[List[str]] = []
    for scc in sccs:
        if len(scc) > 1:
            cycles.append(sorted(scc))
        elif len(scc) == 1:
            n = scc[0]
            if n in graph.get(n, set()):  # self-loop
                cycles.append([n])
    # stable-ish output
    cycles.sort(key=lambda c: (len(c), c))
    return cycles


def write_dot(graph: Dict[str, Set[str]], out: Path) -> None:
    lines = ["digraph imports {", '  rankdir="LR";']
    for src, deps in graph.items():
        if not deps:
            continue
        for dst in deps:
            lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".", help="Root directory of source tree to scan")
    ap.add_argument("--dot", default=None, help="Optional path to write Graphviz .dot output")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph, _modules = build_graph(root)
    cycles = find_cycles(graph)

    if args.dot:
        write_dot(graph, Path(args.dot).resolve())

    if not cycles:
        print("✅ No import cycles found.")
        return 0

    print(f"❌ Found {len(cycles)} import cycle(s):")
    for i, cyc in enumerate(cycles, 1):
        print(f"\nCycle #{i} ({len(cyc)} modules):")
        for m in cyc:
            print(f"  - {m}")

    return 2


if __name__ == "__main__":
    raise SystemExit(main())