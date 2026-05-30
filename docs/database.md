# Iapetus database module

Local persistence lives in **`iapetus.database`**. The older **`iapetus.storage`** package re-exports the same API for backward compatibility.

## Package layout

```
iapetus/database/
  core/                              # Kernel foundation
    connection.py                    # open_connection, kernel_connection
    schema_meta.py                   # schema_meta + version keys
    registry.py                      # register_domain_schema, apply_registered_*
    bootstrap.py                     # init_kernel_database, apply_kernel_schema
    migrations.py                    # reconcile_schema_version (v1+ hooks)
    health.py                        # kernel_database_health
    kernel_database.py               # KernelDatabase facade
  schemas/                           # Domain DDL (auto-registers on import)
    learning_runs.py
  models/
    learning_run_index_row.py        # TypedDict row shape
  repositories/
    base.py                          # KernelRepository
    learning_run_repository.py       # LearningRunRepository + module helpers
```

**Rule:** Use **`database.core`** for connections and bootstrap; add tables under **`schemas/`**; add query logic under **`repositories/`**.

## Paths

Default file: `data/generated/iapetus_learning.db` (`paths.LEARNING_INDEX_DB_PATH`).

```toml
[paths]
learning_index_db_path = "data/generated/iapetus_learning.db"
```

## Core

```python
from iapetus.database import KernelDatabase, kernel_database_health

db = KernelDatabase()
db.initialize()
print(db.health())
```

## Repositories

```python
from iapetus.database import LearningRunRepository, register_learning_run

repo = LearningRunRepository()
repo.upsert_from_run_dir(run_dir)
rows = repo.list_all()

# Module-level helpers (same behavior, default repo):
register_learning_run(run_dir)
```

## CLI

| Command | Purpose |
|---------|---------|
| `iapetus db status` | Run count + latest run |
| `iapetus db inspect` | Tables, row counts, integrity, schema version |
| `iapetus db init` | Create / upgrade kernel schema |
| `iapetus db index` | Rebuild learning-run index from disk |
| `iapetus learn index` | Same as `db index` |
| `iapetus doctor` | Paths + index summary |

## Extending the schema

1. Add `database/schemas/<name>.py` with `apply_*_schema(conn)`.
2. Register in `schemas/__init__.py` via `register_domain_schema(...)`.
3. Add `database/repositories/<name>_repository.py`.
4. Bump `KERNEL_SCHEMA_VERSION` and implement `run_pending_migrations` in `core/migrations.py`.

## Future work

- Additional repositories (jobs, connector cursors)
- Read-only upstream DB connectors (M7)

See also [m6_learning_index.md](m6_learning_index.md).
