# Iapetus Platform Vision

Iapetus is a Fedora-oriented, Python-first kernel for a future Android security
deep-learning platform.

The seed kernel is intentionally host-agnostic so it can run on Windows,
Fedora, and Ubuntu for local development and testing. Fedora is the final
deployment orientation.

M0 is the seed kernel. M1 is the demo snapshot milestone. M2 is the smoke learning lifecycle milestone.

It is intentionally small today and does not replace:

- ObsidianDroid
- ScytaleDroid
- Erebus
- Permission Intel

This repo remains a seed and intentionally avoids external integrations:

- label rendering contracts
- snapshot manifest creation and validation
- local probe and learning-run information
- fixture-driven demos
- future dataset-orchestration structure

## Target architecture later

1. consume governed evidence from upstream systems
2. curate clean local snapshots on Fedora (with seed verification on other hosts)
3. train and evaluate security models over static and dynamic artifacts
4. add physical-device and emulator/VM integration later

Iapetus is built to be additive and non-invasive.
Real integrations should wait until upstream outputs are stable and ObsidianDroid is on a reliable release path.
