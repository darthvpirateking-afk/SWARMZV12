# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import os, json, hashlib, time

ROOT = os.path.abspath(os.getcwd())
OUT_DIR = os.path.join(ROOT, "docs")
OUT_MD = os.path.join(OUT_DIR, "REPO_MAP.md")
OUT_JSON = os.path.join(OUT_DIR, "REPO_MAP.json")

EXCLUDE_DIRS = {".git", ".venv", "node_modules", "dist", "build", ".next", "__pycache__", ".pytest_cache"}
EXCLUDE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".mp4", ".mov", ".zip", ".pdf", ".woff", ".woff2"}

def sha1_file(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def is_excluded_dir(d):
    return d in EXCLUDE_DIRS or d.startswith(".")

def is_excluded_file(fn):
    _, ext = os.path.splitext(fn.lower())
    return ext in EXCLUDE_EXT

def safe_relpath(p: str, root: str):
    """
    Windows can surface device paths like '\\\\.\\nul' or other odd mounts.
    relpath() will throw ValueError if drives/mounts mismatch.
    """
    try:
        # Skip device paths outright
        if p.startswith("\\\\.\\") or p.startswith("\\\\?\\"):
            return None
        # If drive mismatches, skip
        pd = os.path.splitdrive(os.path.abspath(p))[0].lower()
        rd = os.path.splitdrive(os.path.abspath(root))[0].lower()
        if pd and rd and pd != rd:
            return None
        return os.path.relpath(p, root).replace("\\", "/")
    except Exception:
        return None

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    files = []
    for base, dirs, fns in os.walk(ROOT):
        if base.startswith("\\\\.\\") or base.startswith("\\\\?\\"):
            continue
        dirs[:] = [d for d in dirs if not is_excluded_dir(d)]
        for fn in fns:
            if is_excluded_file(fn):
                continue

            p = os.path.join(base, fn)

            rel = safe_relpath(p, ROOT)
            if not rel:
                continue

            try:
                st = os.stat(p)
                files.append({
                    "path": rel,
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "sha1": sha1_file(p) if st.st_size <= 2_000_000 else None,
                })
            except Exception as e:
                files.append({"path": rel, "error": str(e)})

    files_sorted = sorted(files, key=lambda x: x.get("path", ""))
    payload = {
        "root": ROOT.replace("\\", "/"),
        "generated_at": int(time.time()),
        "file_count": len(files_sorted),
        "files": files_sorted
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    lines = []
    lines.append("# REPO MAP\n")
    lines.append(f"- Generated: {time.ctime(payload['generated_at'])}\n")
    lines.append(f"- Files: {payload['file_count']}\n\n")
    lines.append("## Key entrypoint candidates (auto hints)\n\n")

    hints = []
    for x in files_sorted:
        p = x.get("path", "")
        if p.endswith(("run_swarmz.py", "run_server.py", "server.py", "main.py", "app.py", "index.ts", "server/index.ts", "web/package.json", "package.json")):
            hints.append(p)

    if hints:
        for h in hints[:120]:
            lines.append(f"- {h}\n")
    else:
        lines.append("- (none detected)\n")

    lines.append("\n## Full file list\n\n")
    for x in files_sorted:
        p = x.get("path", "")
        if "error" in x:
            lines.append(f"- {p}  (ERROR: {x['error']})\n")
        else:
            lines.append(f"- {p}  ({x['size']} bytes)\n")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("WROTE:", os.path.relpath(OUT_MD, ROOT))
    print("WROTE:", os.path.relpath(OUT_JSON, ROOT))

if __name__ == "__main__":
    main()

# Minimal scaffold for TOOLS_REPO_MAP.py

def get_tools_repo_map():
    pass

