"""
GestureOS AI — Dataset Loader
PyTorch Dataset for landmark CSV files produced by the data collection script.
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


class LandmarkDataset(Dataset):
    """
    Loads a CSV where each row is:
        x0, y0, z0, ..., x20, y20, z20, label
    """

    def __init__(self, csv_path: str, label_map: dict[str, int] | None = None) -> None:
        df = pd.read_csv(csv_path)
        self.features = df.iloc[:, :-1].values.astype(np.float32)  # (N, 63)
        labels_raw = df.iloc[:, -1].values

        if label_map is None:
            classes = sorted(set(labels_raw))
            label_map = {c: i for i, c in enumerate(classes)}

        self.label_map = label_map
        self.labels = np.array([label_map[l] for l in labels_raw], dtype=np.int64)
        self.classes = list(label_map.keys())

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = torch.from_numpy(self.features[idx])
        y = torch.tensor(self.labels[idx])
        return x, y

    @staticmethod
    def save_label_map(label_map: dict[str, int], path: str) -> None:
        lines = [k for k, _ in sorted(label_map.items(), key=lambda kv: kv[1])]
        Path(path).write_text("\n".join(lines))
