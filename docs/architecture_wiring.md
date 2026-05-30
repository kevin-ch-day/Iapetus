# Iapetus seed — architecture wiring

This document describes how modules connect so new work stays maintainable.

## Layering (dependency direction)

```
Typer CLI (iapetus.cli.*)
    → handlers / dispatch / sqlite_learning_index_cli_output
    → domain (learning, validation, snapshots, curated_seed_library_exports, storage)
    → project_filesystem_paths, labels, probes
```

**Rule:** Domain code must not import `iapetus.cli`. CLI may call domain and storage.

## Path constants (`iapetus.project_filesystem_paths`)

| Constant | Purpose |
|----------|---------|
| `DATA_DIR`, `CURATED_DIR`, `GENERATED_DIR`, … | Seed JSON and absorb output |
| `LEARNING_RUNS_DIR` | `output/learning_runs/<run_id>/` |
| `DEMO_OUTPUT_DIR`, `CURATED_SNAPSHOT_DIR` | Snapshot `--write` targets |

- **Canonical module:** `iapetus.project_filesystem_paths`
- **Re-exports:** `iapetus.curated_seed_library_exports` (seed file paths), `iapetus.cli.cli_console_and_path_helpers` (CLI + tests)
- **SQLite index DB:** `paths.LEARNING_INDEX_DB_PATH` via `iapetus.database` (`storage` re-exports for compatibility)

CLI tests monkeypatch `iapetus.cli.cli_console_and_path_helpers.LEARNING_RUNS_DIR` (and siblings). Library code should take explicit `Path` arguments or read `iapetus.project_filesystem_paths`.

## CLI package map

| Module | Role |
|--------|------|
| `typer_application.py` | Registers Typer sub-apps |
| `cli_console_and_path_helpers.py` | Rich console, path aliases, probe helpers |
| `typer_*_command_group.py` / `*_commands.py` | Thin `@app.command` wrappers |
| `*_handlers.py` | Print results, call domain, `typer.Exit` |
| `interactive_learning_console_router.py` | Learning-console command router (menu item 2) |
| `sqlite_learning_index_cli_output.py` | Shared `db status` / index output (used by `db` and `learn index`) |
| `host_platform_probe_commands.py` | `probe`, `status`, `roadmap`, `device` |

## Learning run lifecycle

1. **Train / smoke** — `learning_subcommand_handler_bridge` → `build_smoke_result` / `build_static_v1_result`
2. **Write artifacts** — `write_learning_artifacts` or `write_static_v1_artifacts` → files under `LEARNING_RUNS_DIR/<run_id>/`
3. **Auto-index** — lazy import `iapetus.database.register_learning_run` after write (avoids import cycles)
4. **Read results** — `learning.learning_result_reader.read_learning_result_file` (used by storage and `learn last`)

Artifact names for `learn last` live in `learning.learning_run_artifacts` (single list for smoke vs static MLP).

## Database (`iapetus.database`)

- **`database/core/`** — `KernelDatabase`, connections, registry, migrations, `kernel_database_health`
- **`database/schemas/`** — domain DDL registered via `register_domain_schema`
- **`database/repositories/`** — `LearningRunRepository` and future repos
- **`database/models/`** — Typed row shapes (e.g. `LearningRunIndexRow`)
- **`storage/`** — backward-compatible re-exports (`registry_status` → `learning_index_status`)

## Validation

- `validation.fixture_quality_heuristics` — issue detection heuristics
- `validation.fixture_quality_report` — `FixtureQualityResult`, public re-exports
- `validation.__init__` — stable imports for CLI and tests

## Extension checklist

When adding a feature:

1. Add paths only in `iapetus.project_filesystem_paths` (if new on-disk location).
2. Add domain logic under `learning/`, `validation/`, etc. — no Typer in domain.
3. Add handler in `*_handlers.py` or extend `interactive_learning_console_router.py` for console-only commands.
4. Add a thin command in the matching `typer_*` module or `*_commands.py`.
5. Register sub-app in `typer_application.py` if it is a new top-level group.
6. Patch `iapetus.cli.cli_console_and_path_helpers.*` in tests for filesystem isolation.

## Optional config

Copy `config/local.toml.example` to `config/local.toml` and set `[paths]` keys (`data_dir`, `output_dir`, `generated_dir`, `learning_runs_dir`, etc.). Values are loaded at import via `iapetus.project_filesystem_paths` and mirrored on `iapetus.cli.cli_console_and_path_helpers`. Call `iapetus.project_filesystem_paths.reload_paths()` after editing config in a long-running process.

## Curated artifact writes

`iapetus.learning.curated_learning_artifacts` centralizes JSON bundles for:

- **smoke** curated runs (`kind="smoke"`) — via `write_learning_artifacts(..., write_curated_entities=True)`
- **static MLP** supplements (`kind="static_mlp"`) — after `write_static_v1_artifacts`
- **smoke supplements** — `write_curated_smoke_supplements` (vocabulary, token summary, contract)
- **curated snapshots** — `write_curated_snapshot_supplement`

Artifact names expected by `learn last` remain in `learning.learning_run_artifacts`.

## Scaling roadmap (target package layout)

Current seed layout is fine for ~60 modules and 173 tests. The items below reduce friction as fixtures, connectors, and model code grow.

### Today (strengths)

- Clear CLI vs domain split; `paths` and `curated_artifacts` are single sources of truth.
- `learning/deep/`, `validation/`, `storage/` are already subpackages.
- Lazy registry registration avoids import cycles.

### Growth limits (watch these)

| Module | ~Lines | Risk as you scale |
|--------|--------|-------------------|
| `data_library.py` | 400 | Mixes Pydantic models, JSON I/O, downloads, vocabulary — hard to test in isolation |
| `curated_fixture_analysis.py` | 395 | Fixture resolution + entity features + explain payloads in one file |
| `learning/__init__.py` | 160 | Public API + smoke run I/O — importers pull in snapshots |
| `learning/deep/static_mlp_trainer.py` | 410 | Training + metrics + artifact JSON in one module |
| `console_dispatch.py` | 160 | Grows linearly with every console command |

### Target layout (incremental, not a big-bang rename)

```text
iapetus/
  paths.py, config.py          # kernel config (keep)
  data/                        # split from data_library
    seed_data_models.py        # SeedFixtureSample, SourceManifest
    seeds.py                   # load_*_seed, fixture_seed_as_labels
    vocabulary.py              # build_feature_vocabulary, build_token_summary
    sources.py                 # manifests, download_reference_sources
  features/                    # split from curated_fixture_analysis
    fixtures.py                # resolve_fixture, slug helpers
    entities.py                # build_curated_entity_artifacts, token groups
    explain.py                 # explain/compare payload builders (optional)
  learning/
    learning_run_models.py     # LearningRunResult, LearningRunManifest (from __init__)
    runs.py                    # list/read/write smoke artifacts, generate_run_id
    curated_artifacts.py       # (exists)
    corpus.py                  # alias or move training_corpus.py
    static_v1.py
    deep/                      # (exists)
  validation/                  # (exists)
  storage/                     # (exists)
  connectors/
    protocol.py                # ConnectorAdapter Protocol (read-only pull)
    registry.py                # (exists) — register adapters by id
  cli/                         # Typer only; handlers call domain services
  services/                    # optional thin orchestration (M7+)
    ingest.py                  # absorb + index + validate pipeline
    train_static.py            # train + write + register one call for CLI
```

Keep **backward-compatible re-exports** on old module names (`data_library`, `learning`) for one release cycle when splitting.

### Connector scaling (M7)

Define a small protocol instead of growing `connectors/registry.py` stubs only:

```python
class SnapshotConnector(Protocol):
    connector_id: str
    def pull_entity_bundle(self, *, since: datetime | None = None) -> EntityBundle: ...
```

CLI `connectors show` reads registry metadata; real adapters live in `connectors/adapters/erebus.py` etc., registered at import or via entry points (`[project.entry-points."iapetus.connectors"]` in pyproject).

### CLI scaling

- Prefer **domain services** (`services.train_static.run(...)`) so handlers stay &lt;30 lines.
- Optional **command registry** for `console_dispatch` (dict of name → callable) instead of a long `if` chain.
- Add `iapetus doctor` early — documents effective paths, DB, torch, fixture count.

### Tests and packaging

- Move `pytest` to optional `[dev]` dependency in `pyproject.toml` when you add CI matrices.
- Mirror packages under `tests/` only when a domain package splits (`tests/data/`, `tests/learning/`).
- Consider `src/iapetus/py.typed` and explicit `__all__` on public packages for library consumers.

### Suggested migration phases

1. **Phase 1** — Extract `learning_run_models.py` + `smoke_learning_runs.py` from `learning/__init__.py` — **done**.
2. **Phase 2** — Split `data_library` → `data/` subpackage with re-exports — **done** (`iapetus.data`; `data_library` is a shim).
3. **Phase 3** — Split `curated_fixture_analysis` → `features/`.
4. **Phase 4** — `connectors.protocol` + first real adapter behind feature flag.
5. **Phase 5** — `services/` orchestration + slim CLI handlers.

See also [agendas.md](../agendas.md) work stream A and backlog.
