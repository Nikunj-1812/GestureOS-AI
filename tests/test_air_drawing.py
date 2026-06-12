"""Unit tests for the Air Drawing Canvas page and state logic."""

import customtkinter as ctk
import pytest
from unittest.mock import MagicMock
from dashboard.pages.air_drawing_page import AirDrawingPage
from dashboard.theme import COLORS


@pytest.fixture(scope="module")
def root():
    r = ctk.CTk()
    r.withdraw()  # Avoid displaying actual window frame
    yield r
    r.destroy()


def test_air_drawing_initialization(root):
    page = AirDrawingPage(root)
    assert page._brush_size == 5
    assert page._brush_color == COLORS["mauve"]
    assert page._brush_color_name == "Mauve"
    assert page._current_state == "Idle"
    assert len(page._undo_stack) == 0
    assert len(page._redo_stack) == 0
    assert page._current_stroke is None
    assert page._lbl_status.cget("text") == "Idle"
    assert page._lbl_brush_size_telemetry.cget("text") == "5 px"
    assert page._lbl_brush_color_telemetry.cget("text") == "Mauve"


def test_air_drawing_brush_updates(root):
    page = AirDrawingPage(root)
    
    # Check slider update
    page._on_size_slider_changed(12)
    assert page._brush_size == 12
    assert page._lbl_brush_size_telemetry.cget("text") == "12 px"

    # Check color update
    page._select_color("Blue", COLORS["blue"])
    assert page._brush_color == COLORS["blue"]
    assert page._brush_color_name == "Blue"
    assert page._lbl_brush_color_telemetry.cget("text") == "Blue"


def test_air_drawing_coordinate_mapping(root):
    page = AirDrawingPage(root)
    
    # Center map when aspect ratios are identical (no cropping)
    # img_w/img_h = 640/360 = 16/9, canvas_w/canvas_h = 640/360 = 16/9
    cx, cy = page._map_landmarks_to_canvas(0.5, 0.5, 640, 360, 640, 360)
    assert cx == pytest.approx(320.0)
    assert cy == pytest.approx(180.0)


def test_air_drawing_stroke_lifecycle_and_undo_redo(root):
    page = AirDrawingPage(root)
    
    # Simulate first drawing stroke
    page._start_new_stroke(100.0, 150.0)
    assert page._current_stroke is not None
    assert page._current_stroke["points"] == [(100.0, 150.0)]
    assert page._stroke_counter == 1
    
    page._continue_stroke(105.0, 155.0)
    assert page._current_stroke["points"] == [(100.0, 150.0), (105.0, 155.0)]
    
    page._end_stroke()
    assert page._current_stroke is None
    assert len(page._undo_stack) == 1
    assert page._undo_stack[0]["tag"] == "stroke_1"
    
    # Try Undo
    page._undo()
    assert len(page._undo_stack) == 0
    assert len(page._redo_stack) == 1
    assert page._redo_stack[0]["tag"] == "stroke_1"
    
    # Try Redo
    page._redo()
    assert len(page._undo_stack) == 1
    assert len(page._redo_stack) == 0
    assert page._undo_stack[0]["tag"] == "stroke_1"

    # Simulate Clear
    page._clear_canvas()
    assert len(page._undo_stack) == 0
    assert len(page._redo_stack) == 0
