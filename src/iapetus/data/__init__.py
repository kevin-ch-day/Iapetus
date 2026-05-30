"""Curated seed data loading (models, seeds, vocabulary, sources)."""
from __future__ import annotations

from iapetus import project_filesystem_paths as paths
from iapetus.data.seed_data_models import SeedFixtureSample, SourceManifest, TrustedLevel
from iapetus.data.curated_seed_loaders import (
    fixture_seed_as_labels,
    load_fixture_seed,
    load_permission_seed,
    load_static_token_seed,
    seed_summary,
)
from iapetus.data.reference_source_manifests import download_reference_sources, list_source_manifests
from iapetus.data.seed_payload_validator import validate_seed_payloads
from iapetus.data.aggregated_feature_vocabulary import build_feature_vocabulary, build_token_summary

DATA_DIR = paths.DATA_DIR
CURATED_DIR = paths.CURATED_DIR
RAW_DIR = paths.RAW_DIR
GENERATED_DIR = paths.GENERATED_DIR
KNOWLEDGE_SUMMARY_PATH = paths.KNOWLEDGE_SUMMARY_PATH
TOKEN_VOCABULARY_PATH = paths.TOKEN_VOCABULARY_PATH
FIXTURE_COOCCURRENCE_PATH = paths.FIXTURE_COOCCURRENCE_PATH
TRAINING_CORPUS_PATH = paths.TRAINING_CORPUS_PATH
MANIFESTS_DIR = paths.MANIFESTS_DIR
REFERENCE_RAW_DIR = paths.REFERENCE_RAW_DIR
SOURCE_MANIFEST_PATH = paths.SOURCE_MANIFEST_PATH
PERMISSIONS_SEED_PATH = paths.PERMISSIONS_SEED_PATH
STATIC_TOKEN_SEED_PATH = paths.STATIC_TOKEN_SEED_PATH
FIXTURE_SEED_PATH = paths.FIXTURE_SEED_PATH

__all__ = [
    "DATA_DIR",
    "CURATED_DIR",
    "RAW_DIR",
    "GENERATED_DIR",
    "KNOWLEDGE_SUMMARY_PATH",
    "TOKEN_VOCABULARY_PATH",
    "FIXTURE_COOCCURRENCE_PATH",
    "TRAINING_CORPUS_PATH",
    "MANIFESTS_DIR",
    "REFERENCE_RAW_DIR",
    "SOURCE_MANIFEST_PATH",
    "PERMISSIONS_SEED_PATH",
    "STATIC_TOKEN_SEED_PATH",
    "FIXTURE_SEED_PATH",
    "SeedFixtureSample",
    "SourceManifest",
    "TrustedLevel",
    "build_feature_vocabulary",
    "build_token_summary",
    "download_reference_sources",
    "fixture_seed_as_labels",
    "list_source_manifests",
    "load_fixture_seed",
    "load_permission_seed",
    "load_static_token_seed",
    "seed_summary",
    "validate_seed_payloads",
]
