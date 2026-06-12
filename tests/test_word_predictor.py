import pytest
from modules.word_predictor import get_current_word, get_suggestions

def test_get_current_word():
    assert get_current_word("") == ""
    assert get_current_word("hello") == "hello"
    assert get_current_word("hello ") == ""
    assert get_current_word("hello world") == "world"
    assert get_current_word("hello world-class") == "world-class"
    assert get_current_word("hello world!") == "world"

def test_get_suggestions_matching():
    # Lowercase matches
    assert "gesture" in get_suggestions("ges")
    
    # Titlecase matching
    suggestions_title = get_suggestions("Ges")
    assert all(w[0].isupper() for w in suggestions_title)
    assert "Gesture" in suggestions_title
    
    # Uppercase matching
    suggestions_upper = get_suggestions("GES")
    assert all(w.isupper() for w in suggestions_upper)
    assert "GESTURE" in suggestions_upper

def test_get_suggestions_empty():
    assert get_suggestions("") == []
    assert get_suggestions("xyz") == []
