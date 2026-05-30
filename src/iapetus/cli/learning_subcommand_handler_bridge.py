"""Re-exports learning CLI handlers (train + concept modules)."""
from __future__ import annotations

from iapetus.cli.curated_concept_learning_handlers import (
    _run_learn_absorb,
    _run_learn_compare_fixtures,
    _run_learn_corpus,
    _run_learn_explain_fixture,
    _run_learn_explain_token,
)
from iapetus.cli.static_mlp_smoke_training_handlers import (
    _run_deep_learning_menu,
    _run_learn_evaluate,
    _run_learn_predict,
    _run_learning_last,
    _run_learning_list,
    _run_learning_run,
    _run_smoke_learning_summary,
    _run_static_v1_learning,
    print_label_laboratory,
)

__all__ = [
    "_run_deep_learning_menu",
    "_run_learn_absorb",
    "_run_learn_compare_fixtures",
    "_run_learn_corpus",
    "_run_learn_evaluate",
    "_run_learn_explain_fixture",
    "_run_learn_explain_token",
    "_run_learn_predict",
    "_run_learning_last",
    "_run_learning_list",
    "_run_learning_run",
    "_run_smoke_learning_summary",
    "_run_static_v1_learning",
    "print_label_laboratory",
]
