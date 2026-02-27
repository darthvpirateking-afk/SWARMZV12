# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Claude MD Management Plugin for SWARMZ
Source: claude-md-management@claude-plugins-official

Provides Markdown file management capabilities including reading, writing,
parsing headings, extracting sections, and generating tables of contents.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def register(executor):
    """Register Markdown management tasks with the executor."""

    def read_markdown(filepath: str) -> str:
        """Read a Markdown file and return its contents."""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def write_markdown(filepath: str, content: str) -> str:
        """Write content to a Markdown file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote Markdown to {filepath}"

    def list_markdown_files(directory: str = ".") -> List[str]:
        """List all Markdown files in a directory (recursively)."""
        md_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".md") or file.endswith(".markdown"):
                    md_files.append(os.path.join(root, file))
        return md_files

    def extract_headings(filepath: str) -> List[Dict[str, Any]]:
        """Extract all headings from a Markdown file with their levels and text."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        headings = []
        for line in content.splitlines():
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                headings.append({
                    "level": len(match.group(1)),
                    "text": match.group(2).strip(),
                    "anchor": re.sub(r"[^\w\s-]", "", match.group(2).lower()).strip().replace(" ", "-"),
                })
        return headings

    def generate_toc(filepath: str) -> str:
        """Generate a Table of Contents for a Markdown file."""
        headings = extract_headings(filepath)
        toc_lines = ["## Table of Contents\n"]
        for h in headings:
            indent = "  " * (h["level"] - 1)
            toc_lines.append(f"{indent}- [{h['text']}](#{h['anchor']})")
        return "\n".join(toc_lines)

    def extract_section(filepath: str, heading_text: str) -> str:
        """Extract the content of a specific section by heading text."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        in_section = False
        section_level = 0
        section_lines = []
        for line in lines:
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                if text.lower() == heading_text.lower():
                    in_section = True
                    section_level = level
                    section_lines.append(line)
                elif in_section and level <= section_level:
                    break
                elif in_section:
                    section_lines.append(line)
            elif in_section:
                section_lines.append(line)
        return "\n".join(section_lines) if section_lines else f"Section '{heading_text}' not found."

    def insert_section(filepath: str, heading_text: str, content: str, level: int = 2) -> str:
        """Append a new section to a Markdown file."""
        prefix = "#" * level
        new_section = f"\n{prefix} {heading_text}\n\n{content}\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(new_section)
        return f"Section '{heading_text}' appended to {filepath}"

    def replace_section(filepath: str, heading_text: str, new_content: str) -> str:
        """Replace the content of an existing section in a Markdown file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines(keepends=True)
        result = []
        in_section = False
        section_level = 0
        replaced = False
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r"^(#{1,6})\s+(.+)$", line.rstrip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                if text.lower() == heading_text.lower() and not replaced:
                    in_section = True
                    section_level = level
                    result.append(line)
                    result.append(new_content.rstrip() + "\n")
                    replaced = True
                elif in_section and level <= section_level:
                    in_section = False
                    result.append(line)
                elif not in_section:
                    result.append(line)
            elif not in_section:
                result.append(line)
            i += 1
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(result)
        if replaced:
            return f"Section '{heading_text}' replaced in {filepath}"
        return f"Section '{heading_text}' not found in {filepath}"

    def markdown_summary(filepath: str) -> Dict[str, Any]:
        """Return a summary of a Markdown file: word count, heading count, link count."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        words = len(content.split())
        headings = len(re.findall(r"^#{1,6}\s+.+", content, re.MULTILINE))
        links = len(re.findall(r"\[.+?\]\(.+?\)", content))
        code_blocks = len(re.findall(r"```", content)) // 2
        return {
            "filepath": filepath,
            "word_count": words,
            "heading_count": headings,
            "link_count": links,
            "code_block_count": code_blocks,
        }

    # Register all tasks
    executor.register_task(
        "md_read",
        read_markdown,
        {
            "description": "Read a Markdown file and return its contents",
            "params": {"filepath": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_write",
        write_markdown,
        {
            "description": "Write content to a Markdown file",
            "params": {"filepath": "string", "content": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_list",
        list_markdown_files,
        {
            "description": "List all Markdown files in a directory recursively",
            "params": {"directory": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_headings",
        extract_headings,
        {
            "description": "Extract all headings from a Markdown file with level and anchor",
            "params": {"filepath": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_toc",
        generate_toc,
        {
            "description": "Generate a Table of Contents for a Markdown file",
            "params": {"filepath": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_extract_section",
        extract_section,
        {
            "description": "Extract the content of a specific section by heading text",
            "params": {"filepath": "string", "heading_text": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_insert_section",
        insert_section,
        {
            "description": "Append a new section to a Markdown file",
            "params": {"filepath": "string", "heading_text": "string", "content": "string", "level": "int"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_replace_section",
        replace_section,
        {
            "description": "Replace the content of an existing section in a Markdown file",
            "params": {"filepath": "string", "heading_text": "string", "new_content": "string"},
            "category": "md_management",
        },
    )

    executor.register_task(
        "md_summary",
        markdown_summary,
        {
            "description": "Return a summary of a Markdown file including word count, headings, and links",
            "params": {"filepath": "string"},
            "category": "md_management",
        },
    )
