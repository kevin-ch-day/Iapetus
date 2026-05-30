# Deep learning (seed milestone M5)

Iapetus trains **static MLP v2**: dual-head neural networks over curated `entity_features` vectors.
This is seed-mode deep learning, not production APK training.

## What trains today

- **Input**: 19 numeric/boolean features from `training_corpus.json` (permissions, indicators, counts).
- **Targets**:
  - `entity_kind` — binary malware vs normal_app (LOOCV reported).
  - `expected_classification` — split heads: malware-only classes (Banker, RAT, …) and benign-only classes (Utility, Game, …). Inference routes by predicted `entity_kind`.
- **Model**: three 2-layer MLPs — entity head + malware classification head + benign classification head.
- **Normalization**: column maxima saved to `normalization.json` (required for `learn predict`).
- **Backends**:
  - `pure_python` — always available, used in CI.
  - `torch` — optional via `pip install -e ".[ml]"`.

## Commands

```bash
# Train and write a full run under output/learning_runs/<run_id>/
python -m iapetus.cli learn train --backend pure_python

# Score one fixture with the latest saved model
python -m iapetus.cli learn predict --fixture malware_banker

# Re-evaluate the full curated corpus
python -m iapetus.cli learn evaluate

# Same via learn run
python -m iapetus.cli learn run --mode static-v1 --use-curated --write --backend pure_python

# Menu: Run Deep Learning -> [3] train, [4] evaluate
python -m iapetus.cli menu --choice 1 --deep-choice 3
```

## Run artifacts

| File | Purpose |
|------|---------|
| `training_metrics.json` | Train accuracy, LOOCV accuracy, loss tail |
| `predictions.json` | Per-fixture predicted vs expected entity_kind |
| `model_weights.json` | Entity-kind MLP weights (pure Python) |
| `malware_classification_weights.json` | Malware subtype head (pure Python) |
| `benign_classification_weights.json` | Benign subtype head (pure Python) |
| `model_torch.pt` | Entity-kind PyTorch state dict |
| `classification_malware_torch.pt` | Malware-head PyTorch state dict |
| `classification_benign_torch.pt` | Benign-head PyTorch state dict |
| `normalization.json` | Column maxima used at train time |
| `feature_importance.json` | Per-fixture first-layer attributions |
| `feature_schema.json` | Feature name list and targets |
| `training_corpus.json` | Quality-gated training examples |
| `entity_features.json` | Full curated feature rows |

## Metrics honesty

The curated corpus has **12 samples**. Training reports **leave-one-out cross-validation (LOOCV)**
because holdout splits would be too small. LOOCV scores are useful to sanity-check feature
separability in seed mode; they are **not** production generalization metrics.

## Next steps (later milestones)

- Subgroup LOOCV within malware-only and benign-only folds.
- Permission-token embeddings and sequence models.
- APK / dex byte inputs when connectors supply real artifacts.
- Federated ingestion from Erebus, ObsidianDroid, and device runtime windows.
