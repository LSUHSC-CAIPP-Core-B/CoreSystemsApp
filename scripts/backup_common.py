"""
Shared helpers for the backup scripts.

prune(): deletes old timestamped snapshot folders from a backup destination.

Safety design — this function deletes directories, so it is deliberately
conservative:
  - It only ever looks at *direct children* of `dest` (no recursion into the
    tree, so it can't wander into unrelated places).
  - It only considers entries whose name parses as a timestamp in the exact
    STAMP_FORMAT below. Anything that doesn't match that format is left
    completely alone; so a stray file, a README, or a mis-set `dest` full of
    unrelated folders won't be touched.
  - It decides age from the *name's* timestamp, not the filesystem mtime, so
    copying/moving a backup (which changes mtime) can't make it look younger
    or older than it really is.
  - The caller is expected to run this only AFTER a successful backup, so a
    failed run never deletes anything.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Must match the strftime format the backup scripts use to name snapshots.
STAMP_FORMAT = "%Y-%m-%d_%H%M%S"


def prune(dest: Path, keep_days: int) -> int:
    """
    Delete snapshot folders directly under `dest` older than `keep_days`.

    Returns the number of folders deleted. Folders whose names don't parse as
    STAMP_FORMAT are ignored entirely.
    """
    dest = Path(dest)
    if not dest.is_dir():
        return 0

    cutoff = datetime.now() - timedelta(days=keep_days)
    deleted = 0

    for child in dest.iterdir():
        if not child.is_dir():
            continue  # only snapshot folders, never loose files

        # The name MUST parse as our timestamp format, or leave it alone.
        # Main guardrail against deleting the wrong thing.
        try:
            stamp = datetime.strptime(child.name, STAMP_FORMAT)
        except ValueError:
            continue

        if stamp < cutoff:
            shutil.rmtree(child)
            deleted += 1

    return deleted
