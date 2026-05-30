# Bad-data hardening (adversarial fixtures)

Iapetus includes a controlled adversarial fixture set for **data-quality hardening only**.
These records are fake, malformed, spoofed, or contradictory inputs used to test what the seed
kernel accepts too easily and what it fails to explain.

## Location

- `tests/fixtures/android_bad_fixture_samples_seed.json`
- Loader: `iapetus.validation.adversarial_fixtures`

The JSON wrapper marks `fixture_set: adversarial_test` and `not_training_truth: true`.

## Not training truth

Adversarial fixtures must **never** be treated as malware labels or Android ground truth.
They exist to:

- surface validation gaps before real connectors arrive
- harden explain/compare/permission checks
- document issue categories for future dataset guards

## Default learning exclusion

`iapetus learn run` uses curated good fixtures only. Bad fixtures are excluded unless you pass
`--include-bad-data`, which writes `bad_data_validation.json` beside the run **without** merging
bad rows into `entities.json` or entity counts.

## CLI

```bash
python -m iapetus.cli bad-data list
python -m iapetus.cli bad-data validate
python -m iapetus.cli bad-data show --fixture spoofed_windows_as_android
python -m iapetus.cli bad-data explain --fixture normal_app_with_malware_label
python -m iapetus.cli bad-data compare-good --bad spoofed_windows_as_android --good malware_banker
python -m iapetus.cli bad-data probe
python -m iapetus.cli bad-data regex-audit
python -m iapetus.cli bad-data edge-cases
python -m iapetus.cli bad-data gaps
```

## Issue categories

- `platform_extension_conflict`
- `entity_kind_label_conflict`
- `malformed_permission`
- `malformed_label`
- `suspicious_overclaim`
- `android_platform_conflict`
- `windows_artifact_in_android_context`
- `contradictory_context`
- `unknown_or_unsupported_platform`
- `missing_required_identity`
- `invalid_package_name` (paths, mixed case, non–applicationId shape)
- `low_confidence_unknown`

## Training eligibility gates

Shared rules live in `iapetus.validation.fixture_quality`:

- Curated good fixtures must be `training_eligible` before `learn run --use-curated` writes artifacts.
- `entity_features.json` rows include `training_eligible`, `quality_issues`, and `training_blockers`.
- `data validate` fails if any curated fixture is blocked.

Bad adversarial fixtures should always have `training_eligible=false`.

Additional seed rules closed from stress testing:

- Permissions must appear in `android_permissions_seed.json`, not only match `android.permission.*` syntax.
- `normal_app` rows with `contradictory_context` or `suspicious_overclaim` are training blockers (not warn-only).
- Malware rows with empty or incomplete `labels` raise `entity_kind_label_conflict`.
- Package names must be lowercase Android applicationId form (mixed case like `Com.Example.Bad` is rejected).

## Audit and remediation

```bash
python -m iapetus.cli bad-data audit
python -m iapetus.cli bad-data check-good
```

`learn absorb` writes `data/generated/training_quality_contract.json` and
`data/generated/adversarial_coverage_audit.json` for review.

`bad-data explain` includes remediation hints describing how to fix rows before any
future training pipeline would accept them.

## What this teaches us

When validation misses an issue, the adversarial suite should gain a new case and a matching rule.
That loop keeps the future Android deep-learning dataset contract conservative and explicit.
Run `bad-data audit` to see expected-vs-detected coverage gaps.
Run `bad-data probe` for synthetic wrong-data rows that must never slip into training.
Run `bad-data regex-audit` to validate label/permission/package regexes against known-good and known-bad strings.
Run `bad-data edge-cases` to exercise borderline rows in `tests/fixtures/android_edge_case_samples_seed.json` and compare detected vs expected behavior.
Run `bad-data gaps` for a single summary of audit + probe + regex + wrongly-eligible adversarial fixtures.

Edge-case seed (`fixture_set: edge_case_test`) documents intentional lenient rows too, e.g. very long package names and apk rows identified by `file_name` only.

## Regex rules (seed)

- **Malware labels** must match `platform:primary.family-variant:[subtype]` with exactly one dot in the body.
- **Normal labels** must match `platform:app_name-build_ref:[category]` with no dot in `app_name`.
- **Permissions** must be lowercase `android.permission.*` with an uppercase suffix token present in the permission seed.
- **Package names** must be lowercase applicationId form with non-empty `[a-z]` segments (no `..`, no numeric-only segments).
