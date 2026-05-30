from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def torch_available() -> bool:
    try:
        import torch  # noqa: F401

        return True
    except ImportError:
        return False


def _softmax(logits: list[float]) -> list[float]:
    max_logit = max(logits)
    exps = [math.exp(item - max_logit) for item in logits]
    total = sum(exps)
    return [item / total for item in exps]


@dataclass
class PurePythonMLP:
    input_size: int
    hidden_size: int
    output_size: int
    w1: list[list[float]]
    b1: list[float]
    w2: list[list[float]]
    b2: list[float]

    @classmethod
    def initialize(cls, input_size: int, hidden_size: int = 16, output_size: int = 2, seed: int = 42) -> PurePythonMLP:
        rng = random.Random(seed)
        scale1 = math.sqrt(2.0 / max(input_size, 1))
        scale2 = math.sqrt(2.0 / max(hidden_size, 1))
        w1 = [[rng.uniform(-scale1, scale1) for _ in range(input_size)] for _ in range(hidden_size)]
        b1 = [0.0 for _ in range(hidden_size)]
        w2 = [[rng.uniform(-scale2, scale2) for _ in range(hidden_size)] for _ in range(output_size)]
        b2 = [0.0 for _ in range(output_size)]
        return cls(input_size=input_size, hidden_size=hidden_size, output_size=output_size, w1=w1, b1=b1, w2=w2, b2=b2)

    def _forward_with_cache(self, row: list[float]) -> tuple[list[float], list[float], list[float]]:
        hidden_pre = [
            sum(self.w1[neuron][feature_index] * row[feature_index] for feature_index in range(self.input_size))
            + self.b1[neuron]
            for neuron in range(self.hidden_size)
        ]
        hidden = [max(0.0, value) for value in hidden_pre]
        logits = [
            sum(self.w2[class_index][hidden_index] * hidden[hidden_index] for hidden_index in range(self.hidden_size))
            + self.b2[class_index]
            for class_index in range(self.output_size)
        ]
        probs = _softmax(logits)
        return hidden_pre, hidden, probs

    def forward(self, row: list[float]) -> list[float]:
        return self._forward_with_cache(row)[2]

    def predict_class(self, row: list[float]) -> int:
        probs = self.forward(row)
        best = max(probs)
        return next(index for index, prob in enumerate(probs) if prob == best)

    def predict_proba(self, row: list[float]) -> list[float]:
        return self.forward(row)

    def train(
        self,
        matrix: list[list[float]],
        labels: list[int],
        *,
        epochs: int = 80,
        learning_rate: float = 0.05,
    ) -> list[float]:
        losses: list[float] = []
        for _ in range(epochs):
            epoch_loss = 0.0
            for row, label in zip(matrix, labels, strict=True):
                hidden_pre, hidden, probs = self._forward_with_cache(row)
                target = [0.0] * self.output_size
                if 0 <= label < self.output_size:
                    target[label] = 1.0
                else:
                    continue
                epoch_loss += -sum(
                    target[class_index] * math.log(max(probs[class_index], 1e-9))
                    for class_index in range(self.output_size)
                )

                d_logits = [probs[class_index] - target[class_index] for class_index in range(self.output_size)]
                for class_index in range(self.output_size):
                    d_logit = d_logits[class_index]
                    for hidden_index in range(self.hidden_size):
                        if hidden_pre[hidden_index] > 0:
                            self.w2[class_index][hidden_index] -= learning_rate * d_logit * hidden[hidden_index]
                    self.b2[class_index] -= learning_rate * d_logit

                d_hidden = [0.0 for _ in range(self.hidden_size)]
                for class_index in range(self.output_size):
                    d_logit = d_logits[class_index]
                    for hidden_index in range(self.hidden_size):
                        d_hidden[hidden_index] += d_logit * self.w2[class_index][hidden_index]

                for hidden_index in range(self.hidden_size):
                    if hidden_pre[hidden_index] <= 0:
                        continue
                    for feature_index in range(self.input_size):
                        grad = d_hidden[hidden_index] * row[feature_index]
                        self.w1[hidden_index][feature_index] -= learning_rate * grad
                    self.b1[hidden_index] -= learning_rate * d_hidden[hidden_index]

            losses.append(epoch_loss / max(len(matrix), 1))
        return losses

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": "pure_python",
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "w1": self.w1,
            "b1": self.b1,
            "w2": self.w2,
            "b2": self.b2,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PurePythonMLP:
        return cls(
            input_size=int(payload["input_size"]),
            hidden_size=int(payload["hidden_size"]),
            output_size=int(payload["output_size"]),
            w1=payload["w1"],
            b1=payload["b1"],
            w2=payload["w2"],
            b2=payload["b2"],
        )

    def save_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def train_torch_mlp(
    matrix: list[list[float]],
    labels: list[int],
    *,
    hidden_size: int = 16,
    output_size: int = 2,
    epochs: int = 120,
    learning_rate: float = 0.05,
    seed: int = 42,
) -> tuple[Any, list[float]]:
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    x = torch.tensor(matrix, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)

    model = nn.Sequential(
        nn.Linear(len(matrix[0]), hidden_size),
        nn.ReLU(),
        nn.Linear(hidden_size, output_size),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    losses: list[float] = []
    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.item()))
    return model, losses
