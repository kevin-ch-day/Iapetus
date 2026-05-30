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

Seed repository. M0 is seed kernel. M1 is demo snapshot milestone.
Not production-ready.

## Commands

- `iapetus probe` - prints host OS/version/Python.
- `iapetus probe --check-device` - includes a seed device probe state.
- `iapetus device` - prints the quick adb probe state.
- `iapetus labels demo` - prints example malware and normal app labels.
- `iapetus snapshot demo` - prints a sample demo snapshot manifest and rendered labels.
- `iapetus snapshot demo --write` - writes demo snapshot JSON files.

## Milestones

- M0 - Seed kernel (current): local package skeleton, label renderer, probe, tests.
- M1 - Demo snapshot (this step): built-in fixtures, snapshot manifest builder,
  and optional JSON output to `output/demo_snapshot/`.

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
