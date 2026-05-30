# Future Integration Notes

This is a seed repository and does not connect to external systems.
Iapetus is not connected to platform databases yet.

M0 confirms the minimal seed kernel.
M1 adds a demo snapshot with fixtures, rendering, and write output.

Planned future integrations are read-only first:

- Erebus
- Permission Intel
- ScytaleDroid
- ObsidianDroid
- Web review/triage exports

Planned future capabilities:

- local database schema for kernel metadata
- snapshot ingestion adapters
- physical-device and emulator sessions
- orchestration layer for analysis jobs

All integrations should remain explicit adapters from this kernel to avoid coupling.

Real integrations are expected only after upstream and ObsidianDroid outputs are stable.
