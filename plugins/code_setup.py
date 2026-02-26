# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Claude Code Setup Plugin for SWARMZ
Source: claude-code-setup@claude-plugins-official

Provides project scaffolding and code setup capabilities including
environment detection, dependency management, project initialization,
and development environment configuration.
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional


def register(executor):
    """Register code setup tasks with the executor."""

    def detect_project_type(directory: str = ".") -> Dict[str, Any]:
        """Detect the type of project in a directory based on config files."""
        path = Path(directory)
        indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "setup.cfg", "Pipfile"],
            "node": ["package.json", "yarn.lock", "package-lock.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod", "go.sum"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "dotnet": ["*.csproj", "*.sln", "*.fsproj"],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        }
        detected = []
        files_found = {}
        for lang, files in indicators.items():
            for f in files:
                if "*" in f:
                    matches = list(path.glob(f))
                    if matches:
                        detected.append(lang)
                        files_found[lang] = str(matches[0].name)
                        break
                elif (path / f).exists():
                    detected.append(lang)
                    files_found[lang] = f
                    break
        return {
            "directory": str(path.absolute()),
            "detected_types": detected,
            "indicator_files": files_found,
            "primary_type": detected[0] if detected else "unknown",
        }

    def check_dependencies(directory: str = ".") -> Dict[str, Any]:
        """Check which package managers and runtimes are available."""
        tools = {
            "python": "python --version",
            "pip": "pip --version",
            "node": "node --version",
            "npm": "npm --version",
            "yarn": "yarn --version",
            "cargo": "cargo --version",
            "go": "go version",
            "docker": "docker --version",
            "git": "git --version",
        }
        results = {}
        for tool, cmd in tools.items():
            try:
                result = subprocess.run(
                    cmd.split(), capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    results[tool] = result.stdout.strip().split("\n")[0]
                else:
                    results[tool] = None
            except (FileNotFoundError, subprocess.TimeoutExpired):
                results[tool] = None
        available = [k for k, v in results.items() if v is not None]
        return {"available": available, "versions": results}

    def init_python_project(directory: str, project_name: str) -> str:
        """Initialize a Python project structure with standard files."""
        path = Path(directory) / project_name
        path.mkdir(parents=True, exist_ok=True)
        (path / project_name.replace("-", "_")).mkdir(exist_ok=True)
        (path / project_name.replace("-", "_") / "__init__.py").write_text(
            f'"""{ project_name } package."""\n__version__ = "0.1.0"\n'
        )
        (path / "requirements.txt").write_text("# Add your dependencies here\n")
        (path / "requirements-dev.txt").write_text(
            "pytest>=7.0\npytest-cov\nblack\nflake8\nmypy\n"
        )
        (path / "README.md").write_text(f"# {project_name}\n\nProject description here.\n")
        (path / ".gitignore").write_text(
            "__pycache__/\n*.py[cod]\n*.egg-info/\ndist/\nbuild/\n.env\nvenv/\n.venv/\n"
        )
        (path / "pyproject.toml").write_text(
            f'[build-system]\nrequires = ["setuptools>=61.0"]\nbuild-backend = "setuptools.backends.legacy:build"\n\n'
            f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n'
        )
        return f"Python project '{project_name}' initialized at {path.absolute()}"

    def init_node_project(directory: str, project_name: str) -> str:
        """Initialize a Node.js project structure with package.json."""
        path = Path(directory) / project_name
        path.mkdir(parents=True, exist_ok=True)
        (path / "src").mkdir(exist_ok=True)
        (path / "src" / "index.js").write_text(
            f'// {project_name} entry point\nconsole.log("Hello from {project_name}");\n'
        )
        package_json = {
            "name": project_name,
            "version": "1.0.0",
            "description": "",
            "main": "src/index.js",
            "scripts": {
                "start": "node src/index.js",
                "test": "jest",
                "lint": "eslint src/"
            },
            "keywords": [],
            "author": "",
            "license": "ISC"
        }
        (path / "package.json").write_text(json.dumps(package_json, indent=2) + "\n")
        (path / "README.md").write_text(f"# {project_name}\n\nProject description here.\n")
        (path / ".gitignore").write_text("node_modules/\ndist/\n.env\n*.log\n")
        return f"Node.js project '{project_name}' initialized at {path.absolute()}"

    def install_python_requirements(directory: str = ".") -> str:
        """Install Python requirements from requirements.txt in a directory."""
        req_file = Path(directory) / "requirements.txt"
        if not req_file.exists():
            return f"No requirements.txt found in {directory}"
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return f"Requirements installed successfully from {req_file}"
        return f"Error installing requirements:\n{result.stderr}"

    def create_virtualenv(directory: str = ".", venv_name: str = "venv") -> str:
        """Create a Python virtual environment in the specified directory."""
        venv_path = Path(directory) / venv_name
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            activate = venv_path / "Scripts" / "activate" if os.name == "nt" else venv_path / "bin" / "activate"
            return f"Virtual environment created at {venv_path.absolute()}\nActivate with: {activate}"
        return f"Error creating virtualenv:\n{result.stderr}"

    def scaffold_env_file(directory: str = ".", variables: Optional[List[str]] = None) -> str:
        """Create a .env.example file with placeholder variables."""
        if variables is None:
            variables = ["API_KEY", "DATABASE_URL", "SECRET_KEY", "DEBUG", "PORT"]
        env_path = Path(directory) / ".env.example"
        lines = [f"{var}=\n" for var in variables]
        env_path.write_text("".join(lines))
        return f".env.example created at {env_path.absolute()} with {len(variables)} variables"

    def list_project_structure(directory: str = ".", max_depth: int = 3) -> Dict[str, Any]:
        """List the project directory structure up to a given depth."""
        path = Path(directory)

        def build_tree(p: Path, depth: int) -> Dict:
            if depth == 0:
                return {}
            tree = {}
            try:
                for item in sorted(p.iterdir()):
                    if item.name.startswith(".") or item.name in ("__pycache__", "node_modules", ".git", "venv", ".venv"):
                        continue
                    if item.is_dir():
                        tree[item.name + "/"] = build_tree(item, depth - 1)
                    else:
                        tree[item.name] = item.suffix
            except PermissionError:
                pass
            return tree

        return {
            "root": str(path.absolute()),
            "structure": build_tree(path, max_depth),
        }

    def run_setup_command(directory: str, command: str) -> Dict[str, Any]:
        """Run a setup command (e.g. npm install, pip install -e .) in a directory."""
        result = subprocess.run(
            command.split(),
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "command": command,
            "directory": directory,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0,
        }

    # Register all tasks
    executor.register_task(
        "setup_detect",
        detect_project_type,
        {
            "description": "Detect the project type in a directory based on config files",
            "params": {"directory": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_check_deps",
        check_dependencies,
        {
            "description": "Check which package managers and runtimes are available on the system",
            "params": {"directory": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_init_python",
        init_python_project,
        {
            "description": "Initialize a Python project structure with standard files",
            "params": {"directory": "string", "project_name": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_init_node",
        init_node_project,
        {
            "description": "Initialize a Node.js project structure with package.json",
            "params": {"directory": "string", "project_name": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_install_requirements",
        install_python_requirements,
        {
            "description": "Install Python requirements from requirements.txt",
            "params": {"directory": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_virtualenv",
        create_virtualenv,
        {
            "description": "Create a Python virtual environment in the specified directory",
            "params": {"directory": "string", "venv_name": "string"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_env_file",
        scaffold_env_file,
        {
            "description": "Create a .env.example file with placeholder environment variables",
            "params": {"directory": "string", "variables": "list"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_structure",
        list_project_structure,
        {
            "description": "List the project directory structure up to a given depth",
            "params": {"directory": "string", "max_depth": "int"},
            "category": "code_setup",
        },
    )

    executor.register_task(
        "setup_run",
        run_setup_command,
        {
            "description": "Run a setup command (e.g. npm install, pip install -e .) in a directory",
            "params": {"directory": "string", "command": "string"},
            "category": "code_setup",
        },
    )
