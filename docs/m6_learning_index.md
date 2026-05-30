# M6 seed: learning run index (SQLite)

Iapetus keeps a lightweight **SQLite index** of local learning runs under
`data/generated/iapetus_learning.db` (see **`iapetus.database`**). This is seed-mode
persistence only — not a full orchestration database.

## What is indexed

Each run directory with `learning_result.json` registers:

- Run metadata (`run_id`, `mode`, `status`, `model_name`, …)
- Optional training metrics when `training_metrics.json` exists (static MLP v2 LOOCV, class train accuracy, subgroup train scores)
- `backend` from `model_config.json` when present

Registration happens automatically when you write a run via `learn run`, `learn train`, or smoke/static artifact writers.

## Commands

```bash
# Index status
python -m iapetus.cli db status

# Rebuild index from output/learning_runs/
python -m iapetus.cli db index
python -m iapetus.cli learn index   # same scan, learn namespace alias

# List runs (shows LOOCV/class metrics when indexed)
python -m iapetus.cli learn list
```

## Related backlog (still later)

- Full kernel metadata schema and job orchestration (M6+)
- Read-only upstream connector ingest (M7)
