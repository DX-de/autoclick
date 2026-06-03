"""
Sauvegarde et chargement des paramètres au format JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from autoclicker.config import AppSettings, ClickButton, ClickMode, PositionOrder

_CONFIG_NAME = "autoclicker_config.json"


def _config_path() -> Path:
    base = Path.home() / ".autoclicker"
    base.mkdir(parents=True, exist_ok=True)
    return base / _CONFIG_NAME


def settings_to_dict(settings: AppSettings) -> Dict[str, Any]:
    return {
        "cps": settings.cps,
        "button": settings.button.value,
        "mode": settings.mode.value,
        "positions": [list(p) for p in settings.positions],
        "position_order": settings.position_order.value,
        "infinite": settings.infinite,
        "click_count": settings.click_count,
        "jitter_min_ms": settings.jitter_min_ms,
        "jitter_max_ms": settings.jitter_max_ms,
        "countdown_seconds": settings.countdown_seconds,
        "toggle_hotkey": settings.toggle_hotkey,
        "emergency_hotkey": settings.emergency_hotkey,
        "toggle_hotkey_label": settings.toggle_hotkey_label,
        "emergency_hotkey_label": settings.emergency_hotkey_label,
    }


def dict_to_settings(data: Dict[str, Any]) -> AppSettings:
    positions = [tuple(p) for p in data.get("positions", [])]
    return AppSettings(
        cps=float(data.get("cps", 10.0)),
        button=ClickButton(data.get("button", ClickButton.LEFT.value)),
        mode=ClickMode(data.get("mode", ClickMode.CURRENT_POSITION.value)),
        positions=positions,
        position_order=PositionOrder(
            data.get("position_order", PositionOrder.SEQUENTIAL.value)
        ),
        infinite=bool(data.get("infinite", True)),
        click_count=int(data.get("click_count", 100)),
        jitter_min_ms=int(data.get("jitter_min_ms", 0)),
        jitter_max_ms=int(data.get("jitter_max_ms", 0)),
        countdown_seconds=int(data.get("countdown_seconds", 0)),
        toggle_hotkey=str(data.get("toggle_hotkey", "<f6>")),
        emergency_hotkey=str(data.get("emergency_hotkey", "<esc>")),
        toggle_hotkey_label=str(data.get("toggle_hotkey_label", "F6")),
        emergency_hotkey_label=str(
            data.get("emergency_hotkey_label", "Échap")
        ),
    )


def load_settings() -> AppSettings:
    path = _config_path()
    if not path.exists():
        return AppSettings()
    try:
        with path.open("r", encoding="utf-8") as f:
            return dict_to_settings(json.load(f))
    except (json.JSONDecodeError, OSError, ValueError):
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    path = _config_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings_to_dict(settings), f, indent=2, ensure_ascii=False)
