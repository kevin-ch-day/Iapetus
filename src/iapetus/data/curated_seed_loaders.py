"""Load curated JSON seed files and map fixtures to label models."""
from __future__ import annotations

from iapetus import project_filesystem_paths as paths
from iapetus.data.seed_json_reader import load_json_payload
from iapetus.data.seed_data_models import SeedFixtureSample
from iapetus.data.reference_source_manifests import list_source_manifests
from iapetus.labels import MalwareLabel, NormalAppLabel


def load_permission_seed() -> list[dict]:
    payload = load_json_payload(paths.PERMISSIONS_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Permission seed is not a list: {paths.PERMISSIONS_SEED_PATH}")
    return payload


def load_static_token_seed() -> list[dict]:
    payload = load_json_payload(paths.STATIC_TOKEN_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Static token seed is not a list: {paths.STATIC_TOKEN_SEED_PATH}")
    return payload


def load_fixture_seed() -> list[dict]:
    payload = load_json_payload(paths.FIXTURE_SEED_PATH)
    if not isinstance(payload, list):
        raise ValueError(f"Fixture seed is not a list: {paths.FIXTURE_SEED_PATH}")
    return payload


def fixture_seed_as_labels() -> tuple[list[MalwareLabel], list[NormalAppLabel]]:
    items = load_fixture_seed()
    malware_labels: list[MalwareLabel] = []
    normal_labels: list[NormalAppLabel] = []
    for raw in items:
        sample = SeedFixtureSample.model_validate(raw)
        labels_payload = sample.labels or {}
        sample_type = str(sample.sample_type).strip().lower()
        if sample_type in {"malware", "malicious"}:
            malware_labels.append(
                MalwareLabel(
                    platform=labels_payload.get("platform", "AndroidOS"),
                    malware_primary=labels_payload["malware_primary"],
                    family=labels_payload["family"],
                    variant=labels_payload["variant"],
                    subtype=labels_payload["subtype"],
                )
            )
            continue
        if sample_type in {"benign", "normal", "normal_app", "normal-app"}:
            normal_labels.append(
                NormalAppLabel(
                    platform=labels_payload.get("platform", "AndroidOS"),
                    app_name=labels_payload["app_name"],
                    build_ref=labels_payload["build_ref"],
                    app_category=labels_payload["app_category"],
                )
            )
            continue
        raise ValueError(f"Unknown sample type in fixture seed: {sample.sample_type}")

    if not malware_labels and not normal_labels:
        raise ValueError("No label rows parsed from fixture seed file.")
    return malware_labels, normal_labels


def seed_summary() -> dict[str, int]:
    return {
        "permission_seed_count": len(load_permission_seed()),
        "static_token_seed_count": len(load_static_token_seed()),
        "fixture_sample_count": len(load_fixture_seed()),
        "source_manifest_count": len(list_source_manifests()),
    }
