# Iapetus — project agendas

Living agenda for planning sessions, reviews, and handoffs. Update this file when priorities shift or milestones close.

**Related docs:** [README.md](README.md) · [docs/architecture_wiring.md](docs/architecture_wiring.md) · [docs/platform_vision.md](docs/platform_vision.md) · [docs/future_integration_notes.md](docs/future_integration_notes.md)

---

## How to use

1. Copy the **Standing session agenda** into a meeting note or issue.
2. Refresh **Status snapshot** after each milestone or release-style merge.
3. Move items from **Backlog** → **In progress** → **Done** (with date).
4. Record outcomes in **Decision log** so wiring and scope stay explicit.

---

## Standing session agenda (30–45 min)

| Time | Topic | Owner |
|------|--------|--------|
| 5 min | Status since last session (tests green? blockers?) | — |
| 10 min | Demo: one CLI path (`learn train`, `bad-data gaps`, `status`) | — |
| 10 min | Active work stream review (see below) | — |
| 10 min | Backlog grooming — pick next 1–2 items | — |
| 5 min | Decisions, risks, assignees | — |

**Always verify**

- `python -m pytest` passes on the target host (Windows dev / Fedora target).
- `iapetus roadmap` matches reality (or update `cli/host_platform_probe_commands.py` + this file).
- No new path literals outside `iapetus.project_filesystem_paths` / `config/local.toml`.

---

## Status snapshot

*Last updated: 2026-05-30*

| Area | State |
|------|--------|
| **Phase** | Seed kernel — not production |
| **Tests** | 173 passing (`pytest`) |
| **CLI** | Package layout under `src/iapetus/cli/`; entry `iapetus.cli:app` |
| **Paths** | Canonical `iapetus.project_filesystem_paths`; optional `config/local.toml` |
| **Deep learning** | Static MLP v2 (entity + split classification heads); optional PyTorch |
| **Database** | `iapetus.database.core` + `repositories/` — SQLite kernel DB (`LEARNING_INDEX_DB_PATH`) |
| **Upstream** | Not connected (read-only adapters planned M7+) |

---

## Milestone agenda

Aligned with `iapetus roadmap` and [README.md](README.md#milestones).

| ID | Milestone | Status | Notes |
|----|-----------|--------|--------|
| M0 | Seed kernel (labels, probe, tests) | Done | |
| M1 | Demo snapshot | Done | `output/demo_snapshot/` |
| M2 | Smoke learning lifecycle | Done | list / last / write |
| M3 | Concept trainer (curated seed) | Done | absorb, explain, compare |
| M3.5 | Rich fixtures + per-entity artifacts | Done | 12 training-eligible fixtures |
| M4 | Connector registry (stubs) | Done | seed only |
| M5 | Static MLP v2 | Done | see [docs/deep_learning_seed.md](docs/deep_learning_seed.md) |
| M6 | Learning-run SQLite index | Seed | see [docs/m6_learning_index.md](docs/m6_learning_index.md) |
| M7 | Read-only upstream connectors | Planned | Erebus, Permission Intel, ScytaleDroid, ObsidianDroid |
| M8 | Device / emulator runtime | Planned | adb beyond probe |
| M9 | Production-scale DL pipelines | Planned | |

**M6 seed follow-ups (when scheduling M6 “done”)**

- [ ] Document operator workflow: fresh clone → `learn absorb` → `learn train --write` → `db status`
- [ ] Confirm index rebuild is idempotent across partial/corrupt run dirs
- [ ] Fedora packaging smoke (venv + `pip install -e .`)

---

## Work streams

### A — Code health and maintainability

*Goal: small modules, clear dependency direction (CLI → domain → paths). See [docs/architecture_wiring.md](docs/architecture_wiring.md#scaling-roadmap-target-package-layout).*

- [x] Split monolithic CLI into `cli/` package
- [x] Central paths (`iapetus.project_filesystem_paths`) + `config/local.toml.example`
- [x] Curated artifact writer (`learning/curated_artifacts.py`)
- [x] Console dispatch + registry ops shared by `db` / `learn index`
- [ ] `iapetus doctor` — print resolved paths, registry status, torch availability
- [ ] Trim / split `learning/deep/trainer.py` if it grows past ~500 lines again
- [x] Phase 1: `learning/models.py` + `learning/runs.py` (move out of `learning/__init__.py`)
- [x] Phase 2: `data/` subpackage (split `curated_seed_library_exports.py` / legacy `data_library` API)
- [x] `iapetus doctor` diagnostics command
- [ ] Phase 3: `features/` subpackage (split `curated_fixture_analysis.py`)
- [ ] Phase 4: `connectors.protocol` + adapter entry points (M7)

### B — Data and training quality

*Goal: trustworthy curated corpus and honest metrics on seed scale.*

- [ ] Expand curated fixtures (beyond 12) with documented quality gates
- [ ] Subgroup LOOCV: document as stress metric vs train accuracy for gating
- [ ] More `bad-data` edge cases when new failure modes appear
- [ ] Gap report (`bad-data gaps --write`) reviewed each hardening pass

### C — Operator experience

*Goal: one obvious path for new contributors.*

- [ ] README quick-start validated on Fedora
- [ ] Menu / learning console parity with documented commands
- [ ] Learning console: any missing routes → add to `console_dispatch.py` + help text

### D — Integration (post-seed)

*Goal: read-only, explicit adapters — no writes to upstream.*

- [ ] Adapter design per source ([docs/future_integration_notes.md](docs/future_integration_notes.md))
- [ ] Connector registry: move from stub to read-only pull POC
- [ ] Snapshot ingestion from external exports (web triage, etc.)

---

## Backlog (prioritized)

1. **`iapetus doctor`** — environment + paths + DB + optional device probe summary  
2. **M6 promotion** — checklist above; mark roadmap “done” when satisfied  
3. **Fixture corpus growth** — new slugs + permission/token seeds + tests  
4. **Torch CI optional job** — `[ml]` extra; keep pure_python as default gate  
5. **Watch mode** (menu deep-learning item 5) — defer until real streaming ingest exists  
6. **Dynamic analysis hook** — design only until M8  

---

## Architecture review agenda

Use when refactoring or onboarding a developer.

- [ ] Walk through [docs/architecture_wiring.md](docs/architecture_wiring.md) layering diagram  
- [ ] Trace one learning run: CLI → handlers → `write_*_artifacts` → `register_learning_run`  
- [ ] Trace one absorb: `learn absorb` → `concept_trainer` → `data/generated/`  
- [ ] Confirm tests patch `iapetus.cli.cli_console_and_path_helpers.*` not scattered modules  
- [ ] Validation split: `fixture_quality_rules` vs `fixture_quality` — where to add new issue types  

---

## Release / handoff checklist (informal)

No formal releases yet; use before declaring a milestone “closed”.

- [ ] Full pytest on Windows and (if possible) Fedora  
- [ ] `iapetus status` sane on clean tree (no stale run required)  
- [ ] Docs updated: README commands, relevant `docs/*.md`, this file  
- [ ] No secrets in `data/` or `output/` committed  
- [ ] `config/local.toml` in `.gitignore` (operator-specific)  

---

## Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-30 | Canonical paths in `iapetus.project_filesystem_paths`; CLI aliases via `cli.cli_console_and_path_helpers` | Single override surface for tests and `local.toml` |
| 2026-05-30 | Curated JSON bundles in `learning/curated_artifacts.py` | Remove duplicate write logic across smoke / static MLP / snapshot |
| 2026-05-30 | Lazy `register_learning_run` after artifact write | Avoid `learning` ↔ `storage` import cycles |
| 2026-05-30 | Split-head static MLP (malware/benign classification) | Seed corpus too small for one global classification head |
| — | Upstream integrations remain read-only | Protect Erebus / ObsidianDroid / etc. from kernel writes |

*Add a row when a non-obvious wiring or scope choice is made.*

---

## Open questions

- When is M6 “done” vs “seed” on the public roadmap string?  
- Which upstream system is the first read-only adapter (M7)?  
- Fedora deployment: system Python vs venv vs container?  
- Minimum curated fixture count before seed metrics are marketed internally?  

---

## Session notes (template)

```text
Date:
Attendees:

Done since last time:
-

Discussed:
-

Decisions:
-

Next actions:
- [ ] …
```
