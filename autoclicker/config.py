"""
Configuration par défaut et modèles de données de l'application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class ClickMode(str, Enum):
    """Mode de ciblage des clics."""

    CURRENT_POSITION = "current"
    SAVED_POSITIONS = "saved"


class ClickButton(str, Enum):
    """Type de bouton souris."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class PositionOrder(str, Enum):
    """Ordre de parcours des positions enregistrées."""

    SEQUENTIAL = "sequential"
    RANDOM = "random"


@dataclass
class AppSettings:
    """Paramètres persistés et utilisés par le moteur de clic."""

    cps: float = 10.0
    button: ClickButton = ClickButton.LEFT
    mode: ClickMode = ClickMode.CURRENT_POSITION
    positions: List[Tuple[int, int]] = field(default_factory=list)
    position_order: PositionOrder = PositionOrder.SEQUENTIAL

    infinite: bool = True
    click_count: int = 100

    # Délai aléatoire extra (ms) entre clics — 0 = désactivé
    jitter_min_ms: int = 0
    jitter_max_ms: int = 0

    # Décompte avant démarrage (secondes) — 0 = immédiat
    countdown_seconds: int = 0

    toggle_hotkey: str = "<f6>"
    emergency_hotkey: str = "<esc>"
    toggle_hotkey_label: str = "F6"
    emergency_hotkey_label: str = "Échap"
