"""
Back up every gitignored file from a project into a timestamped snapshot.

Rationale: tracked files are recoverable from git, so the only data at real
risk of loss is the *ignored* stuff (configs, local CSVs, users.db, etc.).
This copies exactly that set.

Run via cron.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from pathspec import PathSpec

# === config ===============================================================
SOURCE = os.environ.get("BACKUP_SOURCE")
# For the server, point this at a different disk / off-machine path.
DEST_ROOT = os.environ.get("BACKUP_DEST")

if not SOURCE or not DEST_ROOT:
    raise SystemExit("Set BACKUP_SOURCE and BACKUP_DEST environment variables.")
DEST_ROOT = Path(DEST_ROOT)

# Files that ARE gitignored but you don't want in the backup anyway:
# regenerable bulk (deps, bytecode, virtualenvs) and noise. Same
# gitignore-style syntax as .gitignore.
SKIP_PATTERNS = [
    "**/__pycache__/",
    "venv/",
    "my_app/",
    "node_modules/",
    "*.log",
    ".DS_Store",
]
# ==========================================================================


def load_spec(source: str):
    """Build a matcher from the project's .gitignore."""
    gitignore = os.path.join(source, ".gitignore")
    with open(gitignore) as f:
        return PathSpec.from_lines("gitwildmatch", f)


def backup() -> None:
    if not os.path.isdir(SOURCE):
        raise SystemExit(f"Source not found: {SOURCE}")

    spec = load_spec(SOURCE)
    skip = PathSpec.from_lines("gitwildmatch", SKIP_PATTERNS)

    # Timestamped snapshot dir so each run is its own copy and we never
    # overwrite a previous good backup.
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    snapshot = DEST_ROOT / stamp
    snapshot.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    # match_tree_files yields ignored files, relative to SOURCE.
    for rel in spec.match_tree_files(SOURCE):
        # Skip anything under .git just in case a pattern reaches into it.
        if rel.startswith(".git/") or rel.startswith("db_config/"):
            continue

        # Skip the regenerable bulk you don't want backed up.
        if skip.match_file(rel):
            skipped += 1
            continue

        src_path = os.path.join(SOURCE, rel)
        if not os.path.isfile(src_path):
            continue  # skip dirs/symlinks/whatever

        dst_path = snapshot / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)  # copy2 preserves mtime/metadata
        copied += 1

    print(f"[{stamp}] backed up {copied} file(s), skipped {skipped} -> {snapshot}")


if __name__ == "__main__":
    backup()
