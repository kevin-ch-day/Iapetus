"""Filesystem layout for the Iapetus seed kernel.

Import path constants from this module (or re-exports on ``iapetus.curated_seed_library_exports`` /
``iapetus.cli.cli_console_and_path_helpers``) instead of hard-coding ``data/`` or ``output/`` in new code.

Optional overrides: ``config/local.toml`` under ``[paths]`` (see ``config/local.toml.example``).

CLI tests may monkeypatch ``iapetus.cli.cli_console_and_path_helpers`` aliases; library code should use
these module-level names or accept explicit ``Path`` arguments.
"""
from __future__ import annotations

from pathlib import Path

from iapetus.application_config import path_overrides_from_config

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_OUTPUT_DIR = Path("output")


def _bootstrap_paths(overrides: dict[str, Path] | None = None) -> dict[str, Path]:
    values = path_overrides_from_config() if overrides is None else overrides

    data_dir = values.get("data_dir", _DEFAULT_DATA_DIR)
    output_dir = values.get("output_dir", _DEFAULT_OUTPUT_DIR)

    generated_dir = values.get("generated_dir", data_dir / "generated")
    learning_index_db_path = values.get(
        "learning_index_db_path",
        generated_dir / "iapetus_learning.db",
    )
    learning_runs_dir = values.get("learning_runs_dir", output_dir / "learning_runs")
    demo_snapshot_dir = values.get("demo_snapshot_dir", output_dir / "demo_snapshot")
    curated_snapshot_dir = values.get("curated_snapshot_dir", output_dir / "curated_snapshot")

    return {
        "DATA_DIR": data_dir,
        "CURATED_DIR": data_dir / "curated",
        "IMPORT_CONTRACTS_DIR": data_dir / "import_contracts",
        "RAW_DIR": data_dir / "raw",
        "GENERATED_DIR": generated_dir,
        "LEARNING_INDEX_DB_PATH": learning_index_db_path,
        "MANIFESTS_DIR": data_dir / "manifests",
        "REFERENCE_RAW_DIR": data_dir / "raw" / "reference",
        "OUTPUT_DIR": output_dir,
        "LEARNING_RUNS_DIR": learning_runs_dir,
        "DEMO_OUTPUT_DIR": demo_snapshot_dir,
        "CURATED_SNAPSHOT_DIR": curated_snapshot_dir,
    }


def _assign_module_paths(mapping: dict[str, Path]) -> None:
    globals().update(mapping)
    g = mapping["GENERATED_DIR"]
    globals().update(
        {
            "KNOWLEDGE_SUMMARY_PATH": g / "knowledge_summary.json",
            "TOKEN_VOCABULARY_PATH": g / "token_vocabulary.json",
            "FIXTURE_COOCCURRENCE_PATH": g / "fixture_cooccurrence.json",
            "TRAINING_CORPUS_PATH": g / "training_corpus.json",
            "SOURCE_MANIFEST_PATH": mapping["MANIFESTS_DIR"] / "android_reference_sources.json",
            "PERMISSIONS_SEED_PATH": mapping["CURATED_DIR"] / "android_permissions_seed.json",
            "STATIC_TOKEN_SEED_PATH": mapping["CURATED_DIR"] / "android_static_tokens_seed.json",
            "FIXTURE_SEED_PATH": mapping["CURATED_DIR"] / "android_fixture_samples_seed.json",
        }
    )


_assign_module_paths(_bootstrap_paths())

# Populated by _assign_module_paths; declared for type checkers and ``from iapetus.project_filesystem_paths import …``.
DATA_DIR: Path
CURATED_DIR: Path
IMPORT_CONTRACTS_DIR: Path
RAW_DIR: Path
GENERATED_DIR: Path
LEARNING_INDEX_DB_PATH: Path
MANIFESTS_DIR: Path
REFERENCE_RAW_DIR: Path
OUTPUT_DIR: Path
LEARNING_RUNS_DIR: Path
DEMO_OUTPUT_DIR: Path
CURATED_SNAPSHOT_DIR: Path
KNOWLEDGE_SUMMARY_PATH: Path
TOKEN_VOCABULARY_PATH: Path
FIXTURE_COOCCURRENCE_PATH: Path
TRAINING_CORPUS_PATH: Path
SOURCE_MANIFEST_PATH: Path
PERMISSIONS_SEED_PATH: Path
STATIC_TOKEN_SEED_PATH: Path
FIXTURE_SEED_PATH: Path


def reload_paths(overrides: dict[str, Path] | None = None) -> None:
    """Re-apply path layout (for tests or after editing local config)."""
    _assign_module_paths(_bootstrap_paths(overrides))
    try:
        from iapetus.cli.cli_console_and_path_helpers import sync_path_aliases

        sync_path_aliases()
    except ImportError:
        pass
