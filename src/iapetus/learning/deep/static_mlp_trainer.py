from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from iapetus.learning.deep.training_feature_encoding import (
    STATIC_FEATURE_NAMES,
    apply_normalization,
    build_classification_index,
    encode_classification_labels,
    encode_example_row,
    encode_feature_matrix,
    feature_schema_document,
    prepare_training_batch,
    split_examples_by_entity_kind,
)
from iapetus.learning.deep.feature_attribution import first_layer_feature_importance
from iapetus.learning.deep.training_metrics_helpers import (
    binary_confusion_matrix,
    binary_precision_recall,
    per_class_accuracy,
)
from iapetus.learning.deep.neural_network_models import PurePythonMLP, torch_available, train_torch_mlp
from iapetus.learning.quality_gated_training_corpus import build_training_corpus

BackendName = Literal["pure_python", "torch"]
HIDDEN_SIZE = 16


def _accuracy(predictions: list[int], labels: list[int]) -> float:
    if not labels:
        return 0.0
    correct = sum(1 for pred, label in zip(predictions, labels, strict=True) if pred == label)
    return correct / len(labels)


def _training_hyperparams(output_size: int, sample_count: int) -> tuple[int, float]:
    if output_size <= 2:
        return 200, 0.08
    epochs = max(500, 80 * output_size)
    learning_rate = 0.01 if output_size >= 4 else 0.03
    if sample_count <= output_size + 2:
        epochs = max(epochs, 600)
        learning_rate = min(learning_rate, 0.01)
    return epochs, learning_rate


def _train_model(
    matrix: list[list[float]],
    labels: list[int],
    *,
    output_size: int,
    backend: BackendName,
    seed: int,
    epochs: int | None = None,
    learning_rate: float | None = None,
) -> tuple[PurePythonMLP | Any, list[float]]:
    default_epochs, default_lr = _training_hyperparams(output_size, len(matrix))
    epochs = default_epochs if epochs is None else epochs
    learning_rate = default_lr if learning_rate is None else learning_rate
    if backend == "torch" and torch_available():
        return train_torch_mlp(
            matrix,
            labels,
            hidden_size=HIDDEN_SIZE,
            output_size=output_size,
            seed=seed,
            epochs=max(epochs, 120),
            learning_rate=learning_rate,
        )
    model = PurePythonMLP.initialize(len(matrix[0]), hidden_size=HIDDEN_SIZE, output_size=output_size, seed=seed)
    loss_history = model.train(matrix, labels, epochs=epochs, learning_rate=learning_rate)
    return model, loss_history


def _predict_all(model: PurePythonMLP | Any, matrix: list[list[float]], backend: BackendName) -> list[int]:
    if backend == "torch" and torch_available():
        import torch

        logits = model(torch.tensor(matrix, dtype=torch.float32))
        return torch.argmax(logits, dim=1).tolist()
    assert isinstance(model, PurePythonMLP)
    return [model.predict_class(row) for row in matrix]


def leave_one_out_cv(
    matrix: list[list[float]],
    labels: list[int],
    *,
    output_size: int = 2,
    backend: BackendName = "pure_python",
    seed: int = 42,
    index_to_label: dict[int, str] | None = None,
    epochs: int | None = None,
    learning_rate: float | None = None,
) -> dict[str, Any]:
    if len(matrix) < 3:
        raise ValueError("Need at least 3 training examples for leave-one-out cross-validation.")

    loocv_epochs, loocv_lr = epochs, learning_rate
    if loocv_epochs is None and output_size > 2:
        default_epochs, default_lr = _training_hyperparams(output_size, len(matrix))
        loocv_epochs = min(default_epochs, 400)
        loocv_lr = default_lr

    predictions: list[int] = []
    for holdout_index in range(len(matrix)):
        train_x = [row for index, row in enumerate(matrix) if index != holdout_index]
        train_y = [label for index, label in enumerate(labels) if index != holdout_index]
        test_x = matrix[holdout_index]
        model, _ = _train_model(
            train_x,
            train_y,
            output_size=output_size,
            backend=backend,
            seed=seed + holdout_index,
            epochs=loocv_epochs,
            learning_rate=loocv_lr,
        )
        if backend == "torch" and torch_available():
            import torch

            pred = int(torch.argmax(model(torch.tensor([test_x], dtype=torch.float32)), dim=1).item())
        else:
            pred = model.predict_class(test_x)
        predictions.append(pred)

    result: dict[str, Any] = {
        "method": "leave_one_out",
        "folds": len(matrix),
        "accuracy": round(_accuracy(predictions, labels), 4),
        "predictions": predictions,
        "labels": labels,
        "confusion": binary_confusion_matrix(predictions, labels) if output_size == 2 else {},
        "precision_recall": binary_precision_recall(predictions, labels) if output_size == 2 else {},
    }
    label_map = index_to_label or {}
    if output_size > 2 and label_map:
        result["per_class"] = per_class_accuracy(
            predictions,
            labels,
            index_to_label=label_map,
        )
    return result


def classification_subgroup_loocv(
    matrix: list[list[float]],
    labels: list[int],
    *,
    output_size: int,
    backend: BackendName,
    seed: int,
    index_to_label: dict[int, str],
    subgroup: str,
) -> dict[str, Any] | None:
    if len(matrix) < 3:
        return None
    loocv = leave_one_out_cv(
        matrix,
        labels,
        output_size=output_size,
        backend=backend,
        seed=seed,
        index_to_label=index_to_label,
    )
    loocv["subgroup"] = subgroup
    return loocv


def train_static_mlp(
    *,
    backend: BackendName | None = None,
    seed: int = 42,
    min_loocv_accuracy: float = 0.75,
) -> tuple[dict[str, Any], PurePythonMLP | Any, PurePythonMLP | Any | None, PurePythonMLP | Any | None]:
    corpus = build_training_corpus()
    examples = corpus["training_examples"]
    if len(examples) < 4:
        raise ValueError("Training corpus too small for static MLP v2 (need >= 4 eligible examples).")

    matrix, entity_labels, _, norm_stats, _, _ = prepare_training_batch(examples)
    chosen_backend: BackendName
    if backend == "torch" and torch_available():
        chosen_backend = "torch"
    elif backend == "pure_python":
        chosen_backend = "pure_python"
    else:
        chosen_backend = "torch" if torch_available() else "pure_python"

    entity_loocv = leave_one_out_cv(
        matrix,
        entity_labels,
        output_size=2,
        backend=chosen_backend,
        seed=seed,
    )

    entity_model, entity_loss = _train_model(matrix, entity_labels, output_size=2, backend=chosen_backend, seed=seed)

    malware_examples, benign_examples = split_examples_by_entity_kind(examples)
    malware_matrix = apply_normalization(encode_feature_matrix(malware_examples), norm_stats)
    benign_matrix = apply_normalization(encode_feature_matrix(benign_examples), norm_stats)
    malware_class_to_index, malware_index_to_class = build_classification_index(malware_examples)
    benign_class_to_index, benign_index_to_class = build_classification_index(benign_examples)

    malware_class_labels = encode_classification_labels(malware_examples, malware_class_to_index)
    benign_class_labels = encode_classification_labels(benign_examples, benign_class_to_index)

    malware_loocv = classification_subgroup_loocv(
        malware_matrix,
        malware_class_labels,
        output_size=len(malware_class_to_index),
        backend=chosen_backend,
        seed=seed + 100,
        index_to_label=malware_index_to_class,
        subgroup="malware",
    )
    benign_loocv = classification_subgroup_loocv(
        benign_matrix,
        benign_class_labels,
        output_size=len(benign_class_to_index),
        backend=chosen_backend,
        seed=seed + 200,
        index_to_label=benign_index_to_class,
        subgroup="benign",
    )

    malware_class_model, malware_class_loss = _train_model(
        malware_matrix,
        malware_class_labels,
        output_size=len(malware_class_to_index),
        backend=chosen_backend,
        seed=seed + 7,
    )
    benign_class_model, benign_class_loss = _train_model(
        benign_matrix,
        benign_class_labels,
        output_size=len(benign_class_to_index),
        backend=chosen_backend,
        seed=seed + 11,
    )

    train_entity_preds = _predict_all(entity_model, matrix, chosen_backend)
    train_accuracy = _accuracy(train_entity_preds, entity_labels)

    def _predict_classification_name(example: dict[str, Any]) -> str:
        row = encode_example_row(example, norm_stats)
        if example["entity_kind"] == "malware":
            pred = _predict_all(malware_class_model, [row], chosen_backend)[0]
            return malware_index_to_class[pred]
        pred = _predict_all(benign_class_model, [row], chosen_backend)[0]
        return benign_index_to_class[pred]

    malware_train_preds = _predict_all(malware_class_model, malware_matrix, chosen_backend)
    benign_train_preds = _predict_all(benign_class_model, benign_matrix, chosen_backend)
    malware_train_accuracy = _accuracy(malware_train_preds, malware_class_labels)
    benign_train_accuracy = _accuracy(benign_train_preds, benign_class_labels)

    predicted_class_names = [_predict_classification_name(example) for example in examples]
    class_train_accuracy = _accuracy(
        [1 if predicted == str(example["expected_classification"]) else 0 for predicted, example in zip(predicted_class_names, examples, strict=True)],
        [1] * len(examples),
    )
    status = "PASS" if entity_loocv["accuracy"] >= min_loocv_accuracy else "WARN"

    entity_payload = (
        {
            "backend": "torch",
            "hidden_size": HIDDEN_SIZE,
            "output_size": 2,
            "state_dict_keys": list(entity_model.state_dict().keys()),
        }
        if chosen_backend == "torch"
        else entity_model.to_dict()
    )

    prediction_rows: list[dict[str, Any]] = []
    for index, example in enumerate(examples):
        entity_pred = train_entity_preds[index]
        entity_label = entity_labels[index]
        predicted_class = predicted_class_names[index]
        prediction_rows.append(
            {
                "fixture_slug": example["fixture_slug"],
                "expected_entity_kind": example["entity_kind"],
                "predicted_entity_kind": "malware" if entity_pred == 1 else "normal_app",
                "entity_kind_correct": entity_pred == entity_label,
                "expected_classification": example["expected_classification"],
                "predicted_classification": predicted_class,
                "classification_correct": predicted_class == example["expected_classification"],
                "top_features": (
                    first_layer_feature_importance(entity_model, matrix[index])
                    if isinstance(entity_model, PurePythonMLP)
                    else []
                ),
            }
        )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model_name": "static_mlp_v2",
        "backend": chosen_backend,
        "feature_schema": feature_schema_document(),
        "feature_count": len(STATIC_FEATURE_NAMES),
        "hidden_size": HIDDEN_SIZE,
        "training_example_count": len(examples),
        "train_accuracy": round(train_accuracy, 4),
        "classification_train_accuracy": round(class_train_accuracy, 4),
        "loocv": entity_loocv,
        "classification_subgroup_loocv": {
            "malware": malware_loocv,
            "benign": benign_loocv,
        },
        "classification_subgroup_train_accuracy": {
            "malware": round(malware_train_accuracy, 4),
            "benign": round(benign_train_accuracy, 4),
        },
        "classification_per_class_train_accuracy": {
            name: (
                1.0
                if all(
                    predicted_class_names[i] == name
                    for i, example in enumerate(examples)
                    if example["expected_classification"] == name
                )
                else 0.0
            )
            for name in sorted({str(example["expected_classification"]) for example in examples})
        },
        "status": status,
        "loss_tail": {
            "entity_kind": [round(item, 6) for item in entity_loss[-5:]],
            "malware_classification": [round(item, 6) for item in malware_class_loss[-5:]],
            "benign_classification": [round(item, 6) for item in benign_class_loss[-5:]],
        },
        "model": entity_payload,
        "malware_classification_model": (
            malware_class_model.to_dict() if isinstance(malware_class_model, PurePythonMLP) else {"backend": "torch"}
        ),
        "benign_classification_model": (
            benign_class_model.to_dict() if isinstance(benign_class_model, PurePythonMLP) else {"backend": "torch"}
        ),
        "normalization": norm_stats.to_dict(),
        "malware_class_to_index": malware_class_to_index,
        "benign_class_to_index": benign_class_to_index,
        "predictions": prediction_rows,
        "notes": [
            "Dual-head static MLP: entity_kind (LOOCV) + split malware/benign classification heads.",
            "Subgroup LOOCV scores classification heads within malware-only and benign-only folds.",
            "Normalization stats are persisted for inference — required for learn predict.",
            "Install optional ML deps with: pip install -e \".[ml]\"",
        ],
    }
    return report, entity_model, malware_class_model, benign_class_model


def write_training_artifacts(
    report: dict[str, Any],
    run_dir: Path,
    *,
    entity_model: PurePythonMLP | Any | None = None,
    malware_classification_model: PurePythonMLP | Any | None = None,
    benign_classification_model: PurePythonMLP | Any | None = None,
) -> dict[str, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "model_config": run_dir / "model_config.json",
        "training_metrics": run_dir / "training_metrics.json",
        "predictions": run_dir / "predictions.json",
        "feature_schema": run_dir / "feature_schema.json",
        "normalization": run_dir / "normalization.json",
        "classification_index": run_dir / "classification_index.json",
        "malware_classification_weights": run_dir / "malware_classification_weights.json",
        "benign_classification_weights": run_dir / "benign_classification_weights.json",
        "feature_importance": run_dir / "feature_importance.json",
    }
    config = {
        "model_name": report["model_name"],
        "backend": report["backend"],
        "feature_count": report["feature_count"],
        "hidden_size": report.get("hidden_size", HIDDEN_SIZE),
        "training_example_count": report["training_example_count"],
        "generated_at": report["generated_at"],
    }
    paths["model_config"].write_text(json.dumps(config, indent=2), encoding="utf-8")
    paths["feature_schema"].write_text(json.dumps(report["feature_schema"], indent=2), encoding="utf-8")
    paths["normalization"].write_text(json.dumps(report["normalization"], indent=2), encoding="utf-8")
    paths["classification_index"].write_text(
        json.dumps(
            {
                "malware_class_to_index": report["malware_class_to_index"],
                "benign_class_to_index": report["benign_class_to_index"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    importance_rows = [
        {
            "fixture_slug": row["fixture_slug"],
            "top_features": row.get("top_features", []),
        }
        for row in report["predictions"]
    ]
    paths["feature_importance"].write_text(json.dumps(importance_rows, indent=2), encoding="utf-8")

    metrics = {
        "train_accuracy": report["train_accuracy"],
        "classification_train_accuracy": report["classification_train_accuracy"],
        "loocv": report["loocv"],
        "classification_subgroup_loocv": report["classification_subgroup_loocv"],
        "classification_subgroup_train_accuracy": report["classification_subgroup_train_accuracy"],
        "classification_per_class_train_accuracy": report["classification_per_class_train_accuracy"],
        "status": report["status"],
        "loss_tail": report["loss_tail"],
        "notes": report["notes"],
    }
    paths["training_metrics"].write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    paths["predictions"].write_text(json.dumps(report["predictions"], indent=2), encoding="utf-8")

    if report["backend"] == "pure_python":
        if isinstance(entity_model, PurePythonMLP):
            entity_model.save_json(run_dir / "model_weights.json")
        else:
            (run_dir / "model_weights.json").write_text(json.dumps(report["model"], indent=2), encoding="utf-8")
        paths["model_weights"] = run_dir / "model_weights.json"
        if isinstance(malware_classification_model, PurePythonMLP):
            malware_classification_model.save_json(run_dir / "malware_classification_weights.json")
            paths["malware_classification_weights"] = run_dir / "malware_classification_weights.json"
        if isinstance(benign_classification_model, PurePythonMLP):
            benign_classification_model.save_json(run_dir / "benign_classification_weights.json")
            paths["benign_classification_weights"] = run_dir / "benign_classification_weights.json"
    elif report["backend"] == "torch" and torch_available():
        import torch

        if entity_model is not None:
            torch.save(entity_model.state_dict(), run_dir / "model_torch.pt")
            paths["model_torch"] = run_dir / "model_torch.pt"
        if malware_classification_model is not None:
            torch.save(malware_classification_model.state_dict(), run_dir / "classification_malware_torch.pt")
            paths["classification_malware_torch"] = run_dir / "classification_malware_torch.pt"
        if benign_classification_model is not None:
            torch.save(benign_classification_model.state_dict(), run_dir / "classification_benign_torch.pt")
            paths["classification_benign_torch"] = run_dir / "classification_benign_torch.pt"

    from iapetus.database import register_learning_run  # noqa: PLC0415

    register_learning_run(run_dir)
    return paths
