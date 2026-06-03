"""Feuille de style sombre pour l'interface Qt."""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}
QPushButton {
    background-color: #45475a;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    color: #cdd6f4;
}
QPushButton:hover {
    background-color: #585b70;
}
QPushButton:pressed {
    background-color: #313244;
}
QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #313244;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    margin: -5px 0;
    background: #89b4fa;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #89b4fa;
    border-radius: 3px;
}
QListWidget {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QListWidget::item:selected {
    background-color: #45475a;
    border-radius: 4px;
}
QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 60px;
}
QCheckBox, QRadioButton {
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background: #313244;
    text-align: center;
    color: #cdd6f4;
    height: 18px;
}
QProgressBar::chunk {
    background: #a6e3a1;
    border-radius: 4px;
}
"""

COLOR_ACTIVE = "#a6e3a1"
COLOR_STOPPED = "#f38ba8"
COLOR_ACCENT = "#89b4fa"
COLOR_WARN = "#fab387"
