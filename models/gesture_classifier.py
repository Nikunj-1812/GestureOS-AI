"""
GestureOS AI — Gesture Classifier Architecture (PyTorch)
Lightweight MLP trained on flattened MediaPipe hand landmarks (21 × 3 = 63 features).
"""

from __future__ import annotations
import torch
import torch.nn as nn


class GestureClassifier(nn.Module):
    """
    3-layer MLP for gesture classification.
    Input:  (batch, 63)  — 21 landmarks × (x, y, z)
    Output: (batch, num_classes)
    """

    def __init__(self, num_classes: int, dropout: float = 0.3) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(63, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    @classmethod
    def from_checkpoint(cls, path: str, num_classes: int) -> "GestureClassifier":
        model = cls(num_classes=num_classes)
        state = torch.load(path, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        return model

    def export_onnx(self, output_path: str) -> None:
        """Export this model to ONNX for runtime inference."""
        dummy = torch.zeros(1, 63)
        torch.onnx.export(
            self,
            dummy,
            output_path,
            input_names=["landmarks"],
            output_names=["logits"],
            dynamic_axes={"landmarks": {0: "batch"}, "logits": {0: "batch"}},
            opset_version=17,
        )
