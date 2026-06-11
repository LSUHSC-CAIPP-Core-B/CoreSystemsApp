"""
Back up MySQL/MariaDB schemas to timestamped .sql dumps.

One dump file per schema (CoreB_<stamp>.sql, CoreC_<stamp>.sql)

Safety:
  - Credentials come from a chmod 600 file (MYSQL_CNF)
  - Each dump is checked: mysqldump must exit 0 AND the file must be non-empty.
    A failed/partial dump is deleted and counted as a failure, so you never
    keep a truncated .sql that looks like a real backup.
  - Old dumps are pruned only AFTER all dumps succeed (see prune call).

Per-machine config is via environment variables (set them in the crontab):
  MYSQLDUMP_BIN  - dump binary. Default "mysqldump". MariaDB boxes that lack
                   the mysqldump symlink set this to "mariadb-dump".
  MYSQL_CNF      - path to the credentials options file (see below).
  DB_BACKUP_DEST - directory the .sql files go into.

Example MYSQL_CNF file (chmod 600!):
    [client]
    user=backupuser
    password=secret
    host=localhost

Run via cron.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from backup_common import prune

# === config ================================================================
# Schemas to back up. Same on every machine, so a constant rather than env var.
DATABASES = ["CoreB", "CoreC"]

# Delete dumps older than this many days (~2 months).
KEEP_DAYS = 60

MYSQLDUMP_BIN = os.environ.get("MYSQLDUMP_BIN", "mysqldump")
MYSQL_CNF = os.environ.get("MYSQL_CNF")
DB_BACKUP_DEST = os.environ.get("DB_BACKUP_DEST")

if not MYSQL_CNF or not DB_BACKUP_DEST:
    raise SystemExit("Set MYSQL_CNF and DB_BACKUP_DEST environment variables.")

DB_BACKUP_DEST = Path(DB_BACKUP_DEST)
# ==========================================================================


def dump_one(db: str, snapshot: Path, stamp: str) -> bool:
    """
    Dump a single schema. Returns True on success, False on failure.

    A dump counts as successful only if mysqldump exits 0 and produces a
    non-empty file; otherwise the partial file is removed.
    """
    out_path = snapshot / f"{db}_{stamp}.sql"

    cmd = [
        MYSQLDUMP_BIN,
        f"--defaults-extra-file={MYSQL_CNF}",  # credentials, kept off the CLI
        "--single-transaction",  # consistent snapshot of InnoDB without locking writers
        "--databases",
        db,  # records CREATE DATABASE so a restore recreates the schema
    ]

    try:
        with open(out_path, "wb") as out_file:
            result = subprocess.run(
                cmd,
                stdout=out_file,  # dump goes straight to the file
                stderr=subprocess.PIPE,  # capture errors for the log
            )
    except FileNotFoundError:
        print(f"  ! dump binary not found: {MYSQLDUMP_BIN}")
        return False

    if result.returncode != 0:
        err = result.stderr.decode(errors="replace").strip()
        print(f"  ! {db}: mysqldump failed (exit {result.returncode}): {err}")
        out_path.unlink(missing_ok=True)  # don't keep a partial dump
        return False

    if out_path.stat().st_size == 0:
        print(f"  ! {db}: dump was empty, discarding")
        out_path.unlink(missing_ok=True)
        return False

    print(f"  + {db}: {out_path.stat().st_size} bytes -> {out_path.name}")
    return True


def backup() -> None:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    snapshot = DB_BACKUP_DEST / stamp
    snapshot.mkdir(parents=True, exist_ok=True)

    print(f"[{stamp}] dumping {', '.join(DATABASES)} -> {snapshot}")

    results = {db: dump_one(db, snapshot, stamp) for db in DATABASES}
    succeeded = [db for db, ok in results.items() if ok]
    failed = [db for db, ok in results.items() if not ok]

    print(f"[{stamp}] {len(succeeded)} ok, {len(failed)} failed")

    # Only prune when EVERYTHING succeeded. If any dump failed this run, keep
    # all old backups - they may be the only good copy of the failed schema.
    if failed:
        print(f"[{stamp}] skipping prune; failed: {', '.join(failed)}")
        raise SystemExit(1)  # non-zero so cron logs/alerts see the failure

    removed = prune(DB_BACKUP_DEST, KEEP_DAYS)
    if removed:
        print(f"[{stamp}] pruned {removed} dump set(s) older than {KEEP_DAYS} days")


if __name__ == "__main__":
    backup()
