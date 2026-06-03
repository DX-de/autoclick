"""
Interface graphique CustomTkinter — Auto Clicker professionnel.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk
from pynput import keyboard
from pynput.mouse import Controller as MouseController

from autoclicker.click_engine import ClickEngine
from autoclicker.config import AppSettings, ClickButton, ClickMode
from autoclicker.hotkey_manager import HotkeyManager, key_to_hotkey_string
from autoclicker.persistence import load_settings, save_settings

# Thème moderne
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLOR_ACTIVE = "#2ecc71"
COLOR_STOPPED = "#e74c3c"
COLOR_ACCENT = "#3498db"


class KeyCaptureDialog(ctk.CTkToplevel):
    """Fenêtre modale pour capturer une touche de raccourci."""

    def __init__(
        self,
        master,
        title: str,
        on_captured: Callable[[str, str], None],
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("400x140")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._on_captured = on_captured
        self._listener: Optional[keyboard.Listener] = None

        ctk.CTkLabel(
            self,
            text="Appuyez sur la touche souhaitée…",
            font=ctk.CTkFont(size=14),
        ).pack(pady=(24, 8))

        ctk.CTkButton(self, text="Annuler", command=self._cancel).pack(pady=8)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.after(100, self._start_listen)

    def _start_listen(self) -> None:
        self._listener = keyboard.Listener(on_press=self._on_key)
        self._listener.start()

    def _on_key(self, key) -> None:
        hotkey, label = key_to_hotkey_string(key)
        if self._listener:
            self._listener.stop()
        self.after(0, lambda: self._finish(hotkey, label))

    def _finish(self, hotkey: str, label: str) -> None:
        self._on_captured(hotkey, label)
        self.grab_release()
        self.destroy()

    def _cancel(self) -> None:
        if self._listener:
            self._listener.stop()
        self.grab_release()
        self.destroy()


class AutoClickerApp(ctk.CTk):
    """Fenêtre principale de l'application Auto Clicker."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Auto Clicker Pro")
        self.geometry("520x720")
        self.minsize(480, 680)

        self._settings = load_settings()
        self._mouse = MouseController()

        self._engine = ClickEngine(
            on_running_change=self._on_engine_running_change,
            on_click_done=self._on_click_done,
        )
        self._engine.update_settings(self._settings)

        self._hotkeys = HotkeyManager(
            on_toggle=self._toggle_from_hotkey,
            on_emergency_stop=self._emergency_stop,
        )
        self._hotkeys.set_hotkeys(
            self._settings.toggle_hotkey,
            self._settings.emergency_hotkey,
        )
        self._hotkeys.start()

        self._build_ui()
        self._sync_ui_from_settings()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # En-tête + statut
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        ctk.CTkLabel(
            header,
            text="Auto Clicker Pro",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        self._status_label = ctk.CTkLabel(
            header,
            text="● Arrêté",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_STOPPED,
        )
        self._status_label.pack(side="right")

        # Boutons Start / Stop
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Démarrer",
            height=44,
            fg_color=COLOR_ACTIVE,
            hover_color="#27ae60",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start,
        )
        self._start_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text="■  Arrêter",
            height=44,
            fg_color=COLOR_STOPPED,
            hover_color="#c0392b",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._stop,
        )
        self._stop_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self._click_count_label = ctk.CTkLabel(
            self,
            text="Clics effectués : 0",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        self._click_count_label.grid(row=2, column=0, pady=(0, 12))

        # Vitesse CPS
        speed_frame = ctk.CTkFrame(self)
        speed_frame.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        speed_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            speed_frame,
            text="Clics par seconde",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 8), sticky="w")

        self._cps_slider = ctk.CTkSlider(
            speed_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self._on_cps_slider,
        )
        self._cps_slider.grid(row=1, column=0, columnspan=2, padx=12, sticky="ew")

        self._cps_entry = ctk.CTkEntry(speed_frame, width=60, justify="center")
        self._cps_entry.grid(row=1, column=2, padx=(8, 12), pady=4)
        self._cps_entry.bind("<Return>", self._on_cps_entry)
        self._cps_entry.bind("<FocusOut>", self._on_cps_entry)

        # Type de clic
        click_frame = ctk.CTkFrame(self)
        click_frame.grid(row=4, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkLabel(
            click_frame,
            text="Type de clic",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self._button_var = tk.StringVar(value=ClickButton.LEFT.value)
        btn_row = ctk.CTkFrame(click_frame, fg_color="transparent")
        btn_row.grid(row=1, column=0, padx=8, pady=(0, 12), sticky="ew")

        for i, (label, val) in enumerate(
            [
                ("Gauche", ClickButton.LEFT.value),
                ("Droit", ClickButton.RIGHT.value),
                ("Molette", ClickButton.MIDDLE.value),
            ]
        ):
            ctk.CTkRadioButton(
                btn_row,
                text=label,
                variable=self._button_var,
                value=val,
                command=self._apply_settings,
            ).grid(row=0, column=i, padx=12, pady=4)

        # Mode de position
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        mode_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mode_frame,
            text="Mode de clic",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self._mode_var = tk.StringVar(value=ClickMode.CURRENT_POSITION.value)
        ctk.CTkRadioButton(
            mode_frame,
            text="Position actuelle de la souris",
            variable=self._mode_var,
            value=ClickMode.CURRENT_POSITION.value,
            command=self._apply_settings,
        ).grid(row=1, column=0, padx=12, sticky="w")

        ctk.CTkRadioButton(
            mode_frame,
            text="Positions enregistrées",
            variable=self._mode_var,
            value=ClickMode.SAVED_POSITIONS.value,
            command=self._apply_settings,
        ).grid(row=2, column=0, padx=12, pady=(4, 8), sticky="w")

        # Liste des positions
        pos_frame = ctk.CTkFrame(self)
        pos_frame.grid(row=6, column=0, padx=20, pady=6, sticky="nsew")
        pos_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            pos_frame,
            text="Positions enregistrées (X, Y)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 6), sticky="w")

        self._positions_list = tk.Listbox(
            pos_frame,
            height=5,
            bg="#2b2b2b",
            fg="white",
            selectbackground=COLOR_ACCENT,
            font=("Segoe UI", 11),
            relief="flat",
            highlightthickness=0,
        )
        self._positions_list.grid(
            row=1, column=0, columnspan=2, padx=12, pady=4, sticky="nsew"
        )
        pos_frame.grid_rowconfigure(1, weight=1)

        pos_btns = ctk.CTkFrame(pos_frame, fg_color="transparent")
        pos_btns.grid(row=2, column=0, columnspan=2, padx=8, pady=(4, 12), sticky="ew")
        pos_btns.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            pos_btns, text="+ Capturer", command=self._capture_position
        ).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(
            pos_btns, text="Supprimer", command=self._remove_position
        ).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(
            pos_btns, text="Tout effacer", command=self._clear_positions
        ).grid(row=0, column=2, padx=4, sticky="ew")

        # Répétition
        repeat_frame = ctk.CTkFrame(self)
        repeat_frame.grid(row=7, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkLabel(
            repeat_frame,
            text="Répétition",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(12, 8), sticky="w")

        self._infinite_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            repeat_frame,
            text="Répétition infinie",
            variable=self._infinite_var,
            command=self._on_infinite_toggle,
        ).grid(row=1, column=0, padx=12, sticky="w")

        count_row = ctk.CTkFrame(repeat_frame, fg_color="transparent")
        count_row.grid(row=2, column=0, padx=12, pady=(4, 12), sticky="w")

        ctk.CTkLabel(count_row, text="Nombre de clics :").pack(side="left")
        self._count_entry = ctk.CTkEntry(count_row, width=80, justify="center")
        self._count_entry.pack(side="left", padx=8)
        self._count_entry.bind("<Return>", self._on_count_entry)
        self._count_entry.bind("<FocusOut>", self._on_count_entry)

        # Raccourcis
        hotkey_frame = ctk.CTkFrame(self)
        hotkey_frame.grid(row=8, column=0, padx=20, pady=6, sticky="ew")
        hotkey_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            hotkey_frame,
            text="Raccourcis clavier",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 8), sticky="w")

        ctk.CTkLabel(hotkey_frame, text="Start / Stop :").grid(
            row=1, column=0, padx=12, pady=4, sticky="w"
        )
        self._toggle_label = ctk.CTkLabel(
            hotkey_frame, text="F6", font=ctk.CTkFont(weight="bold")
        )
        self._toggle_label.grid(row=1, column=1, sticky="w")
        ctk.CTkButton(
            hotkey_frame,
            text="Modifier",
            width=80,
            command=lambda: self._configure_hotkey("toggle"),
        ).grid(row=1, column=2, padx=12, pady=4)

        ctk.CTkLabel(hotkey_frame, text="Arrêt d'urgence :").grid(
            row=2, column=0, padx=12, pady=(4, 12), sticky="w"
        )
        self._emergency_label = ctk.CTkLabel(
            hotkey_frame, text="Échap", font=ctk.CTkFont(weight="bold")
        )
        self._emergency_label.grid(row=2, column=1, sticky="w")
        ctk.CTkButton(
            hotkey_frame,
            text="Modifier",
            width=80,
            command=lambda: self._configure_hotkey("emergency"),
        ).grid(row=2, column=2, padx=12, pady=(4, 12))

        # Pied de page
        ctk.CTkLabel(
            self,
            text="F6 : bascule  •  Échap : arrêt d'urgence  •  Config : ~/.autoclicker/",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).grid(row=9, column=0, pady=(8, 16))

    def _sync_ui_from_settings(self) -> None:
        s = self._settings
        self._cps_slider.set(s.cps)
        self._cps_entry.delete(0, "end")
        self._cps_entry.insert(0, str(int(s.cps) if s.cps == int(s.cps) else s.cps))
        self._button_var.set(s.button.value)
        self._mode_var.set(s.mode.value)
        self._infinite_var.set(s.infinite)
        self._count_entry.delete(0, "end")
        self._count_entry.insert(0, str(s.click_count))
        self._count_entry.configure(state="disabled" if s.infinite else "normal")
        self._toggle_label.configure(text=s.toggle_hotkey_label)
        self._emergency_label.configure(text=s.emergency_hotkey_label)
        self._refresh_positions_list()

    def _refresh_positions_list(self) -> None:
        self._positions_list.delete(0, "end")
        for i, (x, y) in enumerate(self._settings.positions, start=1):
            self._positions_list.insert("end", f"  {i}.  X={x}  Y={y}")

    # -------------------------------------------------------------- Actions
    def _collect_settings(self) -> AppSettings:
        try:
            cps = float(self._cps_entry.get().replace(",", "."))
        except ValueError:
            cps = self._settings.cps
        cps = max(1.0, min(100.0, cps))

        try:
            click_count = int(self._count_entry.get())
        except ValueError:
            click_count = self._settings.click_count
        click_count = max(1, click_count)

        return AppSettings(
            cps=cps,
            button=ClickButton(self._button_var.get()),
            mode=ClickMode(self._mode_var.get()),
            positions=list(self._settings.positions),
            infinite=self._infinite_var.get(),
            click_count=click_count,
            toggle_hotkey=self._settings.toggle_hotkey,
            emergency_hotkey=self._settings.emergency_hotkey,
            toggle_hotkey_label=self._settings.toggle_hotkey_label,
            emergency_hotkey_label=self._settings.emergency_hotkey_label,
        )

    def _apply_settings(self) -> None:
        self._settings = self._collect_settings()
        self._engine.update_settings(self._settings)

    def _on_cps_slider(self, value: float) -> None:
        self._cps_entry.delete(0, "end")
        self._cps_entry.insert(0, str(int(value)))
        self._apply_settings()

    def _on_cps_entry(self, _event=None) -> None:
        try:
            v = float(self._cps_entry.get().replace(",", "."))
            v = max(1.0, min(100.0, v))
            self._cps_slider.set(v)
        except ValueError:
            pass
        self._apply_settings()

    def _on_infinite_toggle(self) -> None:
        state = "disabled" if self._infinite_var.get() else "normal"
        self._count_entry.configure(state=state)
        self._apply_settings()

    def _on_count_entry(self, _event=None) -> None:
        self._apply_settings()

    def _capture_position(self) -> None:
        x, y = self._mouse.position
        self._settings.positions.append((int(x), int(y)))
        self._refresh_positions_list()
        self._apply_settings()

    def _remove_position(self) -> None:
        sel = self._positions_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self._settings.positions):
            del self._settings.positions[idx]
            self._refresh_positions_list()
            self._apply_settings()

    def _clear_positions(self) -> None:
        if self._settings.positions and messagebox.askyesno(
            "Confirmation", "Supprimer toutes les positions ?"
        ):
            self._settings.positions.clear()
            self._refresh_positions_list()
            self._apply_settings()

    def _configure_hotkey(self, which: str) -> None:
        title = (
            "Raccourci Start / Stop"
            if which == "toggle"
            else "Raccourci arrêt d'urgence"
        )

        def on_captured(hotkey: str, label: str) -> None:
            if which == "toggle":
                self._settings.toggle_hotkey = hotkey
                self._settings.toggle_hotkey_label = label
                self._toggle_label.configure(text=label)
            else:
                self._settings.emergency_hotkey = hotkey
                self._settings.emergency_hotkey_label = label
                self._emergency_label.configure(text=label)
            self._hotkeys.set_hotkeys(
                self._settings.toggle_hotkey,
                self._settings.emergency_hotkey,
            )
            save_settings(self._settings)

        KeyCaptureDialog(self, title, on_captured)

    def _start(self) -> None:
        if (
            self._settings.mode == ClickMode.SAVED_POSITIONS
            and not self._settings.positions
        ):
            messagebox.showwarning(
                "Positions manquantes",
                "Ajoutez au moins une position ou passez en mode « position actuelle ».",
            )
            return
        self._apply_settings()
        self._engine.start()

    def _stop(self) -> None:
        self._engine.stop()

    def _toggle_from_hotkey(self) -> None:
        self.after(0, self._engine.toggle)

    def _emergency_stop(self) -> None:
        self.after(0, self._engine.stop)

    def _on_engine_running_change(self, active: bool) -> None:
        def update() -> None:
            if active:
                self._status_label.configure(
                    text="● Actif", text_color=COLOR_ACTIVE
                )
            else:
                self._status_label.configure(
                    text="● Arrêté", text_color=COLOR_STOPPED
                )

        self.after(0, update)

    def _on_click_done(self, count: int) -> None:
        self.after(
            0,
            lambda: self._click_count_label.configure(
                text=f"Clics effectués : {count}"
            ),
        )

    def _on_close(self) -> None:
        self._engine.stop()
        self._hotkeys.stop()
        self._settings = self._collect_settings()
        save_settings(self._settings)
        self.destroy()


def run_app() -> None:
    """Point d'entrée : CustomTkinter si disponible, sinon PySide6."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        from autoclicker.gui_qt import run_app_qt

        run_app_qt()
        return

    app = AutoClickerApp()
    app.mainloop()
