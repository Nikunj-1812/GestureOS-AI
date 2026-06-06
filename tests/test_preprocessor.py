"""Unit tests for the Preprocessor module."""

import numpy as np
import pytest
from modules.preprocessor import Preprocessor


@pytest.fixture
def preprocessor():
    return Preprocessor(target_size=(224, 224))


def test_process_output_shape(preprocessor):
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    result = preprocessor.process(frame)
    assert result.shape == (224, 224, 3)


def test_process_normalized_range(preprocessor):
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = preprocessor.process(frame)
    assert result.min() >= 0.0
    assert result.max() <= 1.0
    assert result.dtype == np.float32


def test_to_tensor_shape(preprocessor):
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    tensor = preprocessor.to_tensor(frame)
    assert tensor.shape == (1, 3, 224, 224)
