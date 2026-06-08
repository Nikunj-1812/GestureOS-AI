"""
GestureOS AI — Qt Stylesheets
Provides dark and light theme QSS strings.
"""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel {
    color: #cdd6f4;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #45475a;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #eff1f5;
    color: #4c4f69;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel {
    color: #4c4f69;
}
QPushButton {
    background-color: #dce0e8;
    color: #4c4f69;
    border: 1px solid #bcc0cc;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #ccd0da;
}
"""


def get_stylesheet(theme: str = "dark") -> str:
    return DARK_THEME if theme == "dark" else LIGHT_THEME
