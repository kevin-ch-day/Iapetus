from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from iapetus.fixture_analysis import (
    build_entity_features,
    extract_fixture_token_groups,
    fixture_record,
    resolve_fixture,
)
from iapetus.learning.deep.features import (
    NormalizationStats,
    apply_normalization,
    encode_row,
)
from iapetus.learning.deep.importance import first_layer_feature_importance
from iapetus.learning.deep.model import PurePythonMLP, torch_available


@dataclass
class ModelBundle:
    run_dir: Path
    backend: str
    entity_kind_model: PurePythonMLP | Any
    malware_classification_model: PurePythonMLP | Any | None
    benign_classification_model: PurePythonMLP | Any | None
    legacy_classification_model: PurePythonMLP | Any | None
    normalization: NormalizationStats
    malware_class_to_index: dict[str, int]
    benign_class_to_index: dict[str, int]
    legacy_class_to_index: dict[str, int]
    config: dict[str, Any]

    @property
    def malware_index_to_class(self) -> dict[int, str]:
        return {index: name for name, index in self.malware_class_to_index.items()}

    @property
    def benign_index_to_class(self) -> dict[int, str]:
        return {index: name for name, index in self.benign_class_to_index.items()}

    @property
    def legacy_index_to_class(self) -> dict[int, str]:
        return {index: name for name, index in self.legacy_class_to_index.items()}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _torch_load_state(path: Path) -> Any:
    import torch

    try:
        return torch.load(path, weights_only=True)
    except TypeError:
        return torch.load(path)


def _load_torch_mlp(path: Path, *, input_size: int, hidden_size: int, output_size: int) -> Any:
    import torch.nn as nn

    model = nn.Sequential(
        nn.Linear(input_size, hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, output_size),
    )
    model.load_state_dict(_torch_load_state(path))
    model.eval()
    return model


def find_static_v1_run_dir(
    output_dir: Path,
    run_id: str | None = None,
) -> Path:
    if run_id:
        candidate = output_dir / run_id
        if not (candidate / "model_config.json").is_file():
            raise FileNotFoundError(f"No model bundle in run directory: {candidate}")
        return candidate

    if not output_dir.exists():
        raise FileNotFoundError(f"Learning runs directory not found: {output_dir}")

    candidates = [
        path
        for path in sorted(output_dir.iterdir(), reverse=True)
        if path.is_dir()
        and (path / "model_config.json").is_file()
        and (path / "normalization.json").is_file()
    ]
    if not candidates:
        raise FileNotFoundError(f"No static-v1 model runs under {output_dir}")
    return candidates[0]


def load_model_bundle(output_dir: Path, run_id: str | None = None) -> ModelBundle:
    run_dir = find_static_v1_run_dir(output_dir, run_id=run_id)
    config = _load_json(run_dir / "model_config.json")
    backend = str(config.get("backend", "pure_python"))
    norm_payload = _load_json(run_dir / "normalization.json")
    normalization = NormalizationStats.from_dict(norm_payload)
    class_map = _load_json(run_dir / "classification_index.json")

    malware_class_to_index = {
        str(key): int(value) for key, value in class_map.get("malware_class_to_index", {}).items()
    }
    benign_class_to_index = {
        str(key): int(value) for key, value in class_map.get("benign_class_to_index", {}).items()
    }
    legacy_class_to_index = {
        str(key): int(value) for key, value in class_map.get("class_to_index", {}).items()
    }

    feature_count = int(config["feature_count"])
    hidden_size = int(config.get("hidden_size", 16))

    malware_classification_model: PurePythonMLP | Any | None = None
    benign_classification_model: PurePythonMLP | Any | None = None
    legacy_classification_model: PurePythonMLP | Any | None = None
    entity_kind_model: PurePythonMLP | Any

    if backend == "torch" and torch_available() and (run_dir / "model_torch.pt").is_file():
        entity_kind_model = _load_torch_mlp(
            run_dir / "model_torch.pt",
            input_size=feature_count,
            hidden_size=hidden_size,
            output_size=2,
        )
        malware_torch = run_dir / "classification_malware_torch.pt"
        benign_torch = run_dir / "classification_benign_torch.pt"
        legacy_torch = run_dir / "classification_torch.pt"
        if malware_torch.is_file() and malware_class_to_index:
            malware_classification_model = _load_torch_mlp(
                malware_torch,
                input_size=feature_count,
                hidden_size=hidden_size,
                output_size=len(malware_class_to_index),
            )
        if benign_torch.is_file() and benign_class_to_index:
            benign_classification_model = _load_torch_mlp(
                benign_torch,
                input_size=feature_count,
                hidden_size=hidden_size,
                output_size=len(benign_class_to_index),
            )
        if legacy_torch.is_file() and legacy_class_to_index:
            legacy_classification_model = _load_torch_mlp(
                legacy_torch,
                input_size=feature_count,
                hidden_size=hidden_size,
                output_size=len(legacy_class_to_index),
            )
    else:
        weights_path = run_dir / "model_weights.json"
        if not weights_path.is_file():
            raise FileNotFoundError(f"Missing model weights: {weights_path}")
        entity_kind_model = PurePythonMLP.from_dict(_load_json(weights_path))
        malware_weights = run_dir / "malware_classification_weights.json"
        benign_weights = run_dir / "benign_classification_weights.json"
        legacy_weights = run_dir / "classification_weights.json"
        if malware_weights.is_file() and malware_class_to_index:
            malware_classification_model = PurePythonMLP.from_dict(_load_json(malware_weights))
        if benign_weights.is_file() and benign_class_to_index:
            benign_classification_model = PurePythonMLP.from_dict(_load_json(benign_weights))
        if legacy_weights.is_file() and legacy_class_to_index:
            legacy_classification_model = PurePythonMLP.from_dict(_load_json(legacy_weights))

    return ModelBundle(
        run_dir=run_dir,
        backend=backend,
        entity_kind_model=entity_kind_model,
        malware_classification_model=malware_classification_model,
        benign_classification_model=benign_classification_model,
        legacy_classification_model=legacy_classification_model,
        normalization=normalization,
        malware_class_to_index=malware_class_to_index,
        benign_class_to_index=benign_class_to_index,
        legacy_class_to_index=legacy_class_to_index,
        config=config,
    )


def encode_fixture_row(fixture_key: str, *, stats: NormalizationStats | None = None) -> list[float]:
    item = resolve_fixture(fixture_key)
    record = fixture_record(item)
    groups = extract_fixture_token_groups(item)
    features = build_entity_features(record, groups, raw_item=item)
    row = encode_row(features)
    if stats is None:
        return row
    return apply_normalization([row], stats)[0]


def _predict_entity_kind(bundle: ModelBundle, row: list[float]) -> tuple[str, list[float]]:
    if bundle.backend == "torch" and torch_available():
        import torch

        model = bundle.entity_kind_model
        logits = model(torch.tensor([row], dtype=torch.float32))
        probs_tensor = torch.softmax(logits, dim=1)[0]
        probs = probs_tensor.tolist()
        pred = int(torch.argmax(logits, dim=1).item())
    else:
        model = bundle.entity_kind_model
        assert isinstance(model, PurePythonMLP)
        probs = model.predict_proba(row)
        pred = model.predict_class(row)
    kind = "malware" if pred == 1 else "normal_app"
    return kind, probs


def _predict_with_model(
    model: PurePythonMLP | Any,
    row: list[float],
    index_to_class: dict[int, str],
    *,
    backend: str,
) -> tuple[str, list[float]]:
    if backend == "torch" and torch_available():
        import torch

        logits = model(torch.tensor([row], dtype=torch.float32))
        probs = torch.softmax(logits, dim=1)[0].tolist()
        pred = int(torch.argmax(logits, dim=1).item())
    else:
        assert isinstance(model, PurePythonMLP)
        probs = model.predict_proba(row)
        pred = model.predict_class(row)
    return index_to_class[pred], probs


def _predict_classification(bundle: ModelBundle, row: list[float], entity_kind: str) -> tuple[str | None, list[float]]:
    if entity_kind == "malware" and bundle.malware_classification_model is not None:
        return _predict_with_model(
            bundle.malware_classification_model,
            row,
            bundle.malware_index_to_class,
            backend=bundle.backend,
        )
    if entity_kind == "normal_app" and bundle.benign_classification_model is not None:
        return _predict_with_model(
            bundle.benign_classification_model,
            row,
            bundle.benign_index_to_class,
            backend=bundle.backend,
        )
    if bundle.legacy_classification_model is not None and bundle.legacy_class_to_index:
        return _predict_with_model(
            bundle.legacy_classification_model,
            row,
            bundle.legacy_index_to_class,
            backend=bundle.backend,
        )
    return None, []


def predict_fixture(bundle: ModelBundle, fixture_key: str) -> dict[str, Any]:
    row = encode_fixture_row(fixture_key, stats=bundle.normalization)
    entity_kind, entity_probs = _predict_entity_kind(bundle, row)
    classification, class_probs = _predict_classification(bundle, row, entity_kind)
    item = resolve_fixture(fixture_key)
    record = fixture_record(item)
    importance: list[dict[str, Any]] = []
    if isinstance(bundle.entity_kind_model, PurePythonMLP):
        importance = first_layer_feature_importance(bundle.entity_kind_model, row)

    return {
        "fixture_slug": record["fixture_slug"],
        "expected_entity_kind": record["entity_kind"],
        "expected_classification": record["expected_classification"],
        "predicted_entity_kind": entity_kind,
        "predicted_classification": classification,
        "entity_kind_probability_malware": round(entity_probs[1] if len(entity_probs) > 1 else 0.0, 4),
        "entity_kind_correct": entity_kind == record["entity_kind"],
        "classification_correct": classification == record["expected_classification"] if classification else None,
        "top_features": importance,
        "classification_probabilities": class_probs,
    }


def evaluate_saved_run(bundle: ModelBundle) -> dict[str, Any]:
    from iapetus.learning.training_corpus import build_training_corpus

    examples = build_training_corpus()["training_examples"]
    rows = [encode_row(example["feature_vector"]) for example in examples]
    matrix = apply_normalization(rows, bundle.normalization)
    predictions: list[dict[str, Any]] = []
    correct_entity = 0
    correct_class = 0
    for example, row in zip(examples, matrix, strict=True):
        entity_kind, _ = _predict_entity_kind(bundle, row)
        classification, _ = _predict_classification(bundle, row, entity_kind)
        entity_ok = entity_kind == example["entity_kind"]
        class_ok = classification == example["expected_classification"] if classification else False
        correct_entity += int(entity_ok)
        correct_class += int(class_ok)
        predictions.append(
            {
                "fixture_slug": example["fixture_slug"],
                "expected_entity_kind": example["entity_kind"],
                "predicted_entity_kind": entity_kind,
                "entity_kind_correct": entity_ok,
                "expected_classification": example["expected_classification"],
                "predicted_classification": classification,
                "classification_correct": class_ok,
            }
        )
    count = len(examples)
    return {
        "run_dir": str(bundle.run_dir),
        "example_count": count,
        "entity_kind_accuracy": round(correct_entity / count, 4) if count else 0.0,
        "classification_accuracy": round(correct_class / count, 4) if count else 0.0,
        "predictions": predictions,
    }
