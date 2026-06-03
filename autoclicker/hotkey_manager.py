"""
Gestion des raccourcis globaux (démarrage/arrêt et arrêt d'urgence).
"""

from __future__ import annotations

from typing import Callable, Optional

from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyManager:
    """
    Écoute les touches configurées via pynput.
    toggle : bascule start/stop ; emergency : arrêt immédiat uniquement.
    """

    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_emergency_stop: Callable[[], None],
    ) -> None:
        self._on_toggle = on_toggle
        self._on_emergency_stop = on_emergency_stop
        self._toggle_hotkey = "<f6>"
        self._emergency_hotkey = "<esc>"
        self._listener: Optional[keyboard.Listener] = None
        self._pressed: set = set()
        # Évite les répétitions si la touche reste enfoncée
        self._triggered_combos: set = set()

    def set_hotkeys(self, toggle: str, emergency: str) -> None:
        """Met à jour les raccourcis et redémarre l'écoute si active."""
        self._toggle_hotkey = toggle
        self._emergency_hotkey = emergency
        if self._listener is not None:
            self.restart()

    def start(self) -> None:
        """Démarre l'écoute clavier (sans double démarrage)."""
        if self._listener is not None:
            return
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Arrête l'écoute."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._pressed.clear()
        self._triggered_combos.clear()

    def restart(self) -> None:
        self.stop()
        self.start()

    def _on_press(self, key) -> None:
        self._pressed.add(self._normalize_key(key))
        combo = self._current_combo()
        if combo in self._triggered_combos:
            return
        if combo == self._emergency_hotkey:
            self._triggered_combos.add(combo)
            self._on_emergency_stop()
        elif combo == self._toggle_hotkey:
            self._triggered_combos.add(combo)
            self._on_toggle()

    def _on_release(self, key) -> None:
        self._pressed.discard(self._normalize_key(key))
        if not self._pressed:
            self._triggered_combos.clear()

    def _normalize_key(self, key) -> str:
        """Convertit une touche pynput en identifiant string."""
        if isinstance(key, KeyCode) and key.char:
            return key.char.lower()
        if isinstance(key, Key):
            name = str(key).replace("Key.", "")
            return f"<{name}>"
        return str(key)

    def _current_combo(self) -> str:
        """Construit la combinaison actuelle au format pynput GlobalHotKeys."""
        parts = sorted(self._pressed)
        return "+".join(parts) if parts else ""


def key_to_hotkey_string(key) -> tuple[str, str]:
    """
    Convertit une touche capturée en (hotkey_pynput, label_affiché).
    Ex. Key.f6 → ('<f6>', 'F6')
    """
    if isinstance(key, KeyCode) and key.char:
        c = key.char.upper()
        return (c.lower(), c)
    if isinstance(key, Key):
        name = str(key).replace("Key.", "")
        label_map = {
            "esc": "Échap",
            "space": "Espace",
            "enter": "Entrée",
            "tab": "Tab",
        }
        label = label_map.get(name, name.upper() if len(name) <= 3 else name.capitalize())
        return (f"<{name}>", label)
    s = str(key)
    return (s, s)
