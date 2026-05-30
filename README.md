# Iapetus

Iapetus is a Fedora-oriented prototype kernel for a future Android security deep-learning platform.

Iapetus is the clean seed for a future Android security deep-learning platform.
It is intentionally focused on a local seed kernel and orchestration layer first.
Windows and other hosts are supported for seed usage, with Fedora still the intended long-term deployment target.
It is not replacing ObsidianDroid, Erebus, ScytaleDroid, or Permission Intel yet.

ObsidianDroid should remain focused on existing malware ML research and publications.
Iapetus is intentionally small and self-contained so it can grow later without coupling.

The long-term goal is to build a learning layer that can consume governed Android security
data from:

- Erebus
- Permission Intel
- ScytaleDroid
- ObsidianDroid
- Web review and triage exports
- Physical-device and emulator-based dynamic analysis sessions

## Early design goals

- Fedora-oriented target environment (seed currently runs on Windows/Fedora/Ubuntu for local development)
- Local development database owned by Iapetus
- Read-only integration with upstream platform databases later
- No writes to upstream systems
- Malware and normal-app label rendering
- Snapshot manifest design
- Future physical-device and emulator dynamic-analysis support

## Status

Seed repository. M0 is the seed kernel. M1 is the demo snapshot milestone. M2 adds smoke learning lifecycle.
M3/M3.5 add concept training over curated static-analysis fixtures and per-entity learning artifacts.
Not production-ready.

## Commands

- `iapetus probe` - prints host OS/version/Python.
- `iapetus probe --check-device` - includes a seed device probe state.
- `iapetus device` - prints the quick adb probe state.
- `iapetus labels demo` - prints example malware and normal app labels.
- `iapetus snapshot demo` - prints a sample demo snapshot manifest and rendered labels.
- `iapetus snapshot demo --write` - writes demo snapshot JSON files.
- `iapetus status` - prints seed host and pipeline status.
- `iapetus learn run --mode smoke [--use-curated] [--write]` - run smoke learning.
- `iapetus learn train` / `learn predict` / `learn evaluate` - static MLP v2 train, inference, and corpus re-score (see `docs/deep_learning_seed.md`).
- `iapetus learn run --mode static-v1 --use-curated --write` - train and write a full learning run.
- `iapetus learn list` / `iapetus learn last` - list or inspect learning runs (per-entity artifacts when curated).
- `iapetus learn absorb` - write `data/generated/` knowledge summaries and `training_corpus.json` from curated seeds.
- `iapetus learn corpus` - preview quality-gated training examples (scores, classifications, feature vectors).
- `iapetus learn explain-fixture --fixture malware_banker` - explain a curated fixture.
- `iapetus learn compare-fixtures --left benign_social_app --right malware_banker` - compare fixtures.
- `iapetus android tokens --fixture malware_banker` - grouped static-analysis tokens for a fixture.
- `iapetus snapshot demo --use-curated [--write]` - curated snapshot to `output/curated_snapshot/`.
- `iapetus connectors` - seed connector registry (planned entity artifact targets).
- `iapetus roadmap` - milestone status.
- `iapetus dataset shape` - dataset contract preview with example `entity_features` row.
- `iapetus bad-data list` / `validate` / `explain` / `compare-good` / `probe` / `regex-audit` / `edge-cases` / `gaps` - adversarial fixture hardening (not training truth; see `docs/bad_data_hardening.md`).
- `iapetus knowledge concepts` - list built-in knowledge concepts.
- `iapetus knowledge teach` - show a seed learning topic list.
- `iapetus knowledge teach android_fundamentals` - print a focused Android teaching module.
- `iapetus knowledge data` - list synthetic seed Android datasets.
- `iapetus knowledge data android_apps` - print fake app entities for training.
- `iapetus knowledge data permission_levels` - print fake permission taxonomy examples.
- `iapetus knowledge data dataset_rows` - print synthetic dataset-shape rows.

## Milestones

- M0 - Seed kernel: local package skeleton, label renderer, probe, tests.
- M1 - Demo snapshot: built-in fixtures, snapshot manifest builder, and optional JSON output to `output/demo_snapshot/`.
- M2 - Smoke learning engine: fixture-based smoke summary/artifact writer, list, and last-run preview.
- M3.5 - Rich curated fixtures (12 training-eligible samples), per-entity learning artifacts, quality-scored training corpus, android token groups, fixture explain/compare.
- M4 (seed) - Connector registry stubs referencing future entity artifact adapters.
- M5 (seed) - Static MLP v1 deep learning on curated `entity_features` (pure Python or optional PyTorch).

## Quick Start (Windows for dev, Fedora for deployment target)

```powershell
python -m pip install -U pip
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
python -m pytest
```

Deploy and run on Fedora with the same command shape after provisioning dependencies.

## M1 demo files

- `output/demo_snapshot/manifest.json`
- `output/demo_snapshot/entities.json`
- `output/demo_snapshot/labels.json`

These are written only when `--write` is provided.
