"""
Moteur de clic automatique — thread dédié, faible consommation CPU.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Callable, Optional

from pynput.mouse import Button, Controller

from autoclicker.config import AppSettings, ClickButton, ClickMode, PositionOrder

_BUTTON_MAP = {
    ClickButton.LEFT: Button.left,
    ClickButton.RIGHT: Button.right,
    ClickButton.MIDDLE: Button.middle,
}


class ClickEngine:
    """
    Exécute les clics dans un thread séparé.
    Utilise Event.wait() + perf_counter pour un timing précis sans busy-wait.
    """

    def __init__(
        self,
        on_running_change: Optional[Callable[[bool], None]] = None,
        on_click_done: Optional[Callable[[int], None]] = None,
    ) -> None:
        self._mouse = Controller()
        self._settings = AppSettings()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._clicks_done = 0
        self._on_running_change = on_running_change
        self._on_click_done = on_click_done

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def clicks_done(self) -> int:
        with self._lock:
            return self._clicks_done

    def update_settings(self, settings: AppSettings) -> None:
        with self._lock:
            self._settings = settings

    def get_settings(self) -> AppSettings:
        with self._lock:
            return self._settings

    def toggle(self) -> bool:
        """Bascule start/stop. Retourne True si démarré, False si arrêté."""
        if self._running:
            self.stop()
            return False
        self.start()
        return True

    def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        with self._lock:
            self._clicks_done = 0
        self._running = True
        self._notify_running(True)
        self._thread = threading.Thread(
            target=self._click_loop,
            name="AutoClickerLoop",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._notify_running(False)

    def _notify_running(self, active: bool) -> None:
        if self._on_running_change:
            try:
                self._on_running_change(active)
            except Exception:
                pass

    def _notify_click(self, count: int) -> None:
        if self._on_click_done:
            try:
                self._on_click_done(count)
            except Exception:
                pass

    def _wait(self, seconds: float) -> bool:
        """Attend jusqu'à seconds ou jusqu'à stop. Retourne True si arrêt demandé."""
        if seconds <= 0:
            return self._stop_event.is_set()
        return self._stop_event.wait(timeout=seconds)

    def _extra_jitter(self, settings: AppSettings) -> None:
        """Pause aléatoire optionnelle entre les clics (effet plus naturel)."""
        lo, hi = settings.jitter_min_ms, settings.jitter_max_ms
        if hi <= 0 or lo < 0:
            return
        lo, hi = min(lo, hi), max(lo, hi)
        if lo == hi == 0:
            return
        delay = random.uniform(lo, hi) / 1000.0
        self._wait(delay)

    def _click_loop(self) -> None:
        position_index = 0
        shuffled: list[int] = []

        while not self._stop_event.is_set():
            with self._lock:
                settings = self._settings
                clicks_done = self._clicks_done

            if not settings.infinite and clicks_done >= settings.click_count:
                break

            cps = max(0.1, min(100.0, settings.cps))
            interval = 1.0 / cps
            cycle_start = time.perf_counter()

            try:
                idx = self._resolve_position_index(
                    settings, position_index, shuffled
                )
                self._perform_click(settings, idx)
            except Exception:
                break

            with self._lock:
                self._clicks_done += 1
                new_count = self._clicks_done

            self._notify_click(new_count)

            if settings.mode == ClickMode.SAVED_POSITIONS and settings.positions:
                n = len(settings.positions)
                if settings.position_order == PositionOrder.RANDOM:
                    if not shuffled or position_index >= n:
                        shuffled = list(range(n))
                        random.shuffle(shuffled)
                        position_index = 0
                    else:
                        position_index += 1
                else:
                    position_index = (position_index + 1) % n

            elapsed = time.perf_counter() - cycle_start
            remaining = interval - elapsed
            if remaining > 0 and self._wait(remaining):
                break

            self._extra_jitter(settings)

            if not self._stop_event.is_set() and remaining <= 0:
                self._wait(0.001)

        self._running = False
        self._notify_running(False)

    def _resolve_position_index(
        self,
        settings: AppSettings,
        position_index: int,
        shuffled: list[int],
    ) -> int:
        if settings.mode != ClickMode.SAVED_POSITIONS or not settings.positions:
            return 0
        n = len(settings.positions)
        if settings.position_order == PositionOrder.RANDOM and shuffled:
            return shuffled[position_index % n]
        return position_index % n

    def _perform_click(self, settings: AppSettings, position_index: int) -> None:
        btn = _BUTTON_MAP[settings.button]

        if settings.mode == ClickMode.SAVED_POSITIONS and settings.positions:
            x, y = settings.positions[position_index]
            self._mouse.position = (x, y)
            time.sleep(0.001)

        self._mouse.click(btn, 1)
