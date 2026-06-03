#!/usr/bin/env python3
"""
Auto Clicker Pro — point d'entrée principal.

Usage :
    python main.py

Compatible Windows et Linux, Python 3.12+.
"""

def main() -> None:
    """Lance l'interface (CustomTkinter ou PySide6 selon le système)."""
    try:
        import tkinter  # noqa: F401

        from autoclicker.gui import run_app

        run_app()
    except ImportError:
        from autoclicker.gui_qt import run_app_qt

        run_app_qt()


if __name__ == "__main__":
    main()
