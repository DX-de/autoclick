"""
Interface PySide6 — utilisée si tkinter (CustomTkinter) n'est pas installé.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from pynput import keyboard
from pynput.mouse import Controller as MouseController

from autoclicker.click_engine import ClickEngine
from autoclicker.config import AppSettings, ClickButton, ClickMode, PositionOrder
from autoclicker.hotkey_manager import HotkeyManager, key_to_hotkey_string
from autoclicker.icon_util import make_app_icon
from autoclicker.persistence import load_settings, save_settings
from autoclicker import profiles as profile_store
from autoclicker.styles import (
    COLOR_ACCENT,
    COLOR_ACTIVE,
    COLOR_STOPPED,
    COLOR_WARN,
    DARK_STYLESHEET,
)


class KeyCaptureDialog(QDialog):
    def __init__(
        self, parent, title: str, on_captured: Callable[[str, str], None]
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(380, 130)
        self._on_captured = on_captured
        self._listener: Optional[keyboard.Listener] = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Appuyez sur la touche souhaitée…"))
        box = QDialogButtonBox(QDialogButtonBox.Cancel)
        box.rejected.connect(self._cancel)
        layout.addWidget(box)
        QTimer.singleShot(100, self._start_listen)

    def _start_listen(self) -> None:
        self._listener = keyboard.Listener(on_press=self._on_key)
        self._listener.start()

    def _on_key(self, key) -> None:
        hotkey, label = key_to_hotkey_string(key)
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        QTimer.singleShot(0, lambda: self._finish(hotkey, label))

    def _finish(self, hotkey: str, label: str) -> None:
        self._on_captured(hotkey, label)
        self.accept()

    def _cancel(self) -> None:
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        self.reject()


class AutoClickerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Auto Clicker Pro")
        self.resize(540, 640)
        self.setMinimumSize(480, 560)
        self.setWindowIcon(make_app_icon())

        self._settings = load_settings()
        self._mouse = MouseController()
        self._countdown_timer: Optional[QTimer] = None
        self._countdown_remaining = 0
        self._config_widgets: list[QWidget] = []
        self._tray: Optional[QSystemTrayIcon] = None
        self._really_quit = False

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
        self._setup_tray()
        self._start_mouse_tracker()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ---- En-tête : titre + statut (toujours visibles) ----
        header = QHBoxLayout()
        layout.addLayout(header)
        title = QLabel("Auto Clicker Pro")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        self._status = QLabel("● Arrêté")
        self._status.setStyleSheet(
            f"color: {COLOR_STOPPED}; font-weight: bold; font-size: 14px;"
        )
        header.addWidget(self._status)

        # ---- Gros bouton démarrer / arrêter ----
        self._toggle_btn = QPushButton("▶  Démarrer")
        self._toggle_btn.setMinimumHeight(48)
        self._toggle_btn.setStyleSheet(
            f"background:{COLOR_ACTIVE}; color:#1e1e2e; font-weight:bold; "
            f"font-size:15px; padding:12px; border-radius:10px;"
        )
        self._toggle_btn.clicked.connect(self._on_toggle_clicked)
        layout.addWidget(self._toggle_btn)

        # ---- Barre d'info live (souris + clics) ----
        info = QHBoxLayout()
        self._mouse_label = QLabel("Souris : —")
        self._mouse_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self._click_label = QLabel("Clics : 0")
        self._click_label.setStyleSheet("color: #a6adc8;")
        info.addWidget(self._mouse_label)
        info.addStretch()
        info.addWidget(self._click_label)
        layout.addLayout(info)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # ---- Onglets ----
        tabs = QTabWidget()
        tabs.addTab(self._build_tab_simple(), "Simple")
        tabs.addTab(self._build_tab_target(), "Cible")
        tabs.addTab(self._build_tab_advanced(), "Avancé")
        tabs.addTab(self._build_tab_profiles(), "Profils")
        layout.addWidget(tabs, 1)

        # ---- Pied de page ----
        self._footer = QLabel()
        self._footer.setStyleSheet("color: #6c7086; font-size: 11px;")
        self._footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._footer)

        self._refresh_profile_combo()
        self._update_footer()

    def _build_tab_simple(self) -> QWidget:
        """Onglet principal : vitesse, type de clic, répétition."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)

        speed = QGroupBox("Vitesse — clics par seconde")
        sl = QHBoxLayout(speed)
        self._cps_slider = QSlider(Qt.Horizontal)
        self._cps_slider.setRange(1, 100)
        self._cps_slider.valueChanged.connect(self._on_cps_slider)
        sl.addWidget(self._cps_slider)
        self._cps_spin = QDoubleSpinBox()
        self._cps_spin.setRange(1, 100)
        self._cps_spin.setDecimals(1)
        self._cps_spin.setSuffix(" /s")
        self._cps_spin.valueChanged.connect(self._on_cps_spin)
        sl.addWidget(self._cps_spin)
        v.addWidget(speed)
        self._config_widgets.extend([self._cps_slider, self._cps_spin])

        click_g = QGroupBox("Type de clic")
        cl = QHBoxLayout(click_g)
        self._btn_group = QButtonGroup(self)
        for label, val in [
            ("Gauche", "left"),
            ("Droit", "right"),
            ("Molette", "middle"),
        ]:
            rb = QRadioButton(label)
            rb.setProperty("val", val)
            self._btn_group.addButton(rb)
            cl.addWidget(rb)
            self._config_widgets.append(rb)
        self._btn_group.buttonClicked.connect(self._apply_settings)
        v.addWidget(click_g)

        rep = QGroupBox("Répétition")
        rl = QVBoxLayout(rep)
        self._infinite = QCheckBox("Répétition infinie")
        self._infinite.toggled.connect(self._on_infinite_toggle)
        rl.addWidget(self._infinite)
        self._config_widgets.append(self._infinite)
        cr = QHBoxLayout()
        cr.addWidget(QLabel("Nombre de clics :"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 999999)
        self._count_spin.valueChanged.connect(self._apply_settings)
        cr.addWidget(self._count_spin)
        cr.addStretch()
        rl.addLayout(cr)
        self._config_widgets.append(self._count_spin)
        v.addWidget(rep)

        v.addStretch()
        return w

    def _build_tab_target(self) -> QWidget:
        """Onglet cible : où cliquer + positions enregistrées."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)

        mode_g = QGroupBox("Où cliquer ?")
        ml = QVBoxLayout(mode_g)
        self._mode_cur = QRadioButton("Position actuelle de la souris")
        self._mode_saved = QRadioButton("Positions enregistrées")
        self._mode_cur.toggled.connect(self._apply_settings)
        self._mode_saved.toggled.connect(self._apply_settings)
        ml.addWidget(self._mode_cur)
        ml.addWidget(self._mode_saved)
        self._config_widgets.extend([self._mode_cur, self._mode_saved])

        order_row = QHBoxLayout()
        order_row.addWidget(QLabel("Ordre :"))
        self._order_combo = QComboBox()
        self._order_combo.addItem("Séquentiel", PositionOrder.SEQUENTIAL.value)
        self._order_combo.addItem("Aléatoire", PositionOrder.RANDOM.value)
        self._order_combo.currentIndexChanged.connect(self._apply_settings)
        order_row.addWidget(self._order_combo)
        order_row.addStretch()
        ml.addLayout(order_row)
        self._config_widgets.append(self._order_combo)
        v.addWidget(mode_g)

        pos_g = QGroupBox("Positions enregistrées (X, Y)")
        pgl = QVBoxLayout(pos_g)
        self._pos_list = QListWidget()
        pgl.addWidget(self._pos_list)
        pb = QHBoxLayout()
        for text, slot in [
            ("+ Capturer", self._capture_position),
            ("Supprimer", self._remove_position),
            ("Tout effacer", self._clear_positions),
        ]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            pb.addWidget(b)
            self._config_widgets.append(b)
        pgl.addLayout(pb)
        self._config_widgets.append(self._pos_list)
        v.addWidget(pos_g, 1)
        return w

    def _build_tab_advanced(self) -> QWidget:
        """Onglet avancé : timing, raccourcis, comportement."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)

        timing = QGroupBox("Timing")
        ag = QGridLayout(timing)
        ag.addWidget(QLabel("Décompte avant départ (s) :"), 0, 0)
        self._countdown_spin = QSpinBox()
        self._countdown_spin.setRange(0, 30)
        self._countdown_spin.setToolTip("0 = démarrage immédiat")
        self._countdown_spin.valueChanged.connect(self._apply_settings)
        ag.addWidget(self._countdown_spin, 0, 1)
        self._config_widgets.append(self._countdown_spin)

        ag.addWidget(QLabel("Jitter min (ms) :"), 1, 0)
        self._jitter_min = QSpinBox()
        self._jitter_min.setRange(0, 5000)
        self._jitter_min.setToolTip("Pause aléatoire extra entre clics")
        self._jitter_min.valueChanged.connect(self._on_jitter_changed)
        ag.addWidget(self._jitter_min, 1, 1)
        self._config_widgets.append(self._jitter_min)

        ag.addWidget(QLabel("Jitter max (ms) :"), 2, 0)
        self._jitter_max = QSpinBox()
        self._jitter_max.setRange(0, 5000)
        self._jitter_max.valueChanged.connect(self._on_jitter_changed)
        ag.addWidget(self._jitter_max, 2, 1)
        self._config_widgets.append(self._jitter_max)
        v.addWidget(timing)

        hk = QGroupBox("Raccourcis clavier")
        gl = QGridLayout(hk)
        gl.addWidget(QLabel("Start / Stop :"), 0, 0)
        self._toggle_lbl = QLabel("F6")
        self._toggle_lbl.setStyleSheet("font-weight: bold;")
        gl.addWidget(self._toggle_lbl, 0, 1)
        b1 = QPushButton("Modifier")
        b1.clicked.connect(lambda: self._configure_hotkey("toggle"))
        gl.addWidget(b1, 0, 2)
        gl.addWidget(QLabel("Arrêt d'urgence :"), 1, 0)
        self._emergency_lbl = QLabel("Échap")
        self._emergency_lbl.setStyleSheet("font-weight: bold;")
        gl.addWidget(self._emergency_lbl, 1, 1)
        b2 = QPushButton("Modifier")
        b2.clicked.connect(lambda: self._configure_hotkey("emergency"))
        gl.addWidget(b2, 1, 2)
        v.addWidget(hk)

        misc = QGroupBox("Comportement")
        mv = QVBoxLayout(misc)
        self._minimize_tray = QCheckBox(
            "Réduire dans la barre système à la fermeture"
        )
        self._minimize_tray.setChecked(True)
        self._minimize_tray.toggled.connect(self._on_tray_toggle)
        mv.addWidget(self._minimize_tray)
        v.addWidget(misc)

        v.addStretch()
        return w

    def _build_tab_profiles(self) -> QWidget:
        """Onglet profils : gestion des presets."""
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)

        prof = QGroupBox("Profils de configuration")
        pgl = QVBoxLayout(prof)
        row = QHBoxLayout()
        row.addWidget(QLabel("Profil actif :"))
        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(160)
        self._profile_combo.currentTextChanged.connect(self._on_profile_selected)
        row.addWidget(self._profile_combo, 1)
        pgl.addLayout(row)
        btns = QHBoxLayout()
        save_p = QPushButton("Sauver")
        save_p.clicked.connect(self._save_profile)
        new_p = QPushButton("Nouveau")
        new_p.clicked.connect(self._new_profile)
        del_p = QPushButton("Supprimer")
        del_p.clicked.connect(self._delete_profile)
        for b in (save_p, new_p, del_p):
            btns.addWidget(b)
        pgl.addLayout(btns)
        self._config_widgets.extend([self._profile_combo, save_p, new_p, del_p])
        v.addWidget(prof)

        hint = QLabel(
            "Sauvegarde plusieurs configurations (vitesse, positions, "
            "raccourcis…) et bascule de l'une à l'autre en un clic."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #6c7086; font-size: 11px;")
        v.addWidget(hint)

        v.addStretch()
        return w

    def _setup_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._minimize_tray.setEnabled(False)
            self._minimize_tray.setChecked(False)
            return

        from PySide6.QtWidgets import QMenu

        self._tray = QSystemTrayIcon(make_app_icon(), self)
        self._tray.setToolTip("Auto Clicker Pro")
        menu = QMenu(self)

        show_act = QAction("Afficher", self)
        show_act.triggered.connect(self._show_from_tray)
        menu.addAction(show_act)

        toggle_act = QAction("Démarrer / Arrêter", self)
        toggle_act.triggered.connect(self._on_toggle_clicked)
        menu.addAction(toggle_act)

        menu.addSeparator()
        quit_act = QAction("Quitter", self)
        quit_act.triggered.connect(self._quit_app)
        menu.addAction(quit_act)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self) -> None:
        self._really_quit = True
        self.close()

    def _on_tray_toggle(self, checked: bool) -> None:
        self._settings.minimize_to_tray = checked
        save_settings(self._settings)

    def _refresh_profile_combo(self) -> None:
        names = profile_store.list_profiles()
        active = profile_store.get_active_profile_name()
        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        self._profile_combo.addItem("— Aucun —", "")
        for n in names:
            self._profile_combo.addItem(n, n)
        if active:
            idx = self._profile_combo.findData(active)
            if idx >= 0:
                self._profile_combo.setCurrentIndex(idx)
        self._profile_combo.blockSignals(False)

    def _on_profile_selected(self, name: str) -> None:
        if not name or name == "— Aucun —":
            return
        try:
            self._settings = profile_store.load_profile(name)
            profile_store.set_active_profile(name)
            self._engine.update_settings(self._settings)
            self._hotkeys.set_hotkeys(
                self._settings.toggle_hotkey,
                self._settings.emergency_hotkey,
            )
            self._sync_ui_from_settings()
        except KeyError:
            pass

    def _save_profile(self) -> None:
        self._apply_settings()
        name, ok = QInputDialog.getText(
            self, "Sauver le profil", "Nom du profil :",
            text=profile_store.get_active_profile_name() or "Mon profil",
        )
        if not ok or not name.strip():
            return
        profile_store.save_profile(name.strip(), self._settings)
        self._refresh_profile_combo()
        idx = self._profile_combo.findData(name.strip())
        if idx >= 0:
            self._profile_combo.setCurrentIndex(idx)

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Nouveau profil", "Nom :")
        if not ok or not name.strip():
            return
        self._apply_settings()
        profile_store.save_profile(name.strip(), self._settings)
        self._refresh_profile_combo()

    def _delete_profile(self) -> None:
        name = self._profile_combo.currentData()
        if not name:
            return
        if QMessageBox.question(
            self, "Supprimer", f"Supprimer le profil « {name} » ?"
        ) != QMessageBox.Yes:
            return
        profile_store.delete_profile(name)
        self._refresh_profile_combo()

    def _start_mouse_tracker(self) -> None:
        self._mouse_timer = QTimer(self)
        self._mouse_timer.timeout.connect(self._update_mouse_pos)
        self._mouse_timer.start(80)

    def _update_mouse_pos(self) -> None:
        try:
            x, y = self._mouse.position
            self._mouse_label.setText(f"Souris : X={int(x)}  Y={int(y)}")
        except Exception:
            pass

    def _update_footer(self) -> None:
        s = self._settings
        self._footer.setText(
            f"{s.toggle_hotkey_label} : bascule  •  "
            f"{s.emergency_hotkey_label} : urgence  •  "
            f"Config : ~/.autoclicker/"
        )

    def _sync_ui_from_settings(self) -> None:
        s = self._settings
        self._cps_slider.setValue(int(s.cps))
        self._cps_spin.setValue(s.cps)
        for btn in self._btn_group.buttons():
            if btn.property("val") == s.button.value:
                btn.setChecked(True)
        if s.mode == ClickMode.CURRENT_POSITION:
            self._mode_cur.setChecked(True)
        else:
            self._mode_saved.setChecked(True)
        idx = self._order_combo.findData(s.position_order.value)
        if idx >= 0:
            self._order_combo.setCurrentIndex(idx)
        self._infinite.setChecked(s.infinite)
        self._count_spin.setValue(s.click_count)
        self._count_spin.setEnabled(not s.infinite)
        self._countdown_spin.setValue(s.countdown_seconds)
        self._jitter_min.setValue(s.jitter_min_ms)
        self._jitter_max.setValue(s.jitter_max_ms)
        self._minimize_tray.setChecked(s.minimize_to_tray)
        self._toggle_lbl.setText(s.toggle_hotkey_label)
        self._emergency_lbl.setText(s.emergency_hotkey_label)
        self._refresh_positions()
        self._update_progress(0)
        self._update_footer()

    def _refresh_positions(self) -> None:
        self._pos_list.clear()
        for i, (x, y) in enumerate(self._settings.positions, 1):
            self._pos_list.addItem(f"  {i}.  X={x}  Y={y}")

    def _collect_settings(self) -> AppSettings:
        btn_val = ClickButton.LEFT
        for b in self._btn_group.buttons():
            if b.isChecked():
                btn_val = ClickButton(b.property("val"))
        mode = (
            ClickMode.CURRENT_POSITION
            if self._mode_cur.isChecked()
            else ClickMode.SAVED_POSITIONS
        )
        order = PositionOrder(self._order_combo.currentData())
        jmin, jmax = self._jitter_min.value(), self._jitter_max.value()
        if jmin > jmax:
            jmin, jmax = jmax, jmin
        return AppSettings(
            cps=self._cps_spin.value(),
            button=btn_val,
            mode=mode,
            positions=list(self._settings.positions),
            position_order=order,
            infinite=self._infinite.isChecked(),
            click_count=self._count_spin.value(),
            jitter_min_ms=jmin,
            jitter_max_ms=jmax,
            countdown_seconds=self._countdown_spin.value(),
            minimize_to_tray=self._minimize_tray.isChecked(),
            toggle_hotkey=self._settings.toggle_hotkey,
            emergency_hotkey=self._settings.emergency_hotkey,
            toggle_hotkey_label=self._settings.toggle_hotkey_label,
            emergency_hotkey_label=self._settings.emergency_hotkey_label,
        )

    def _apply_settings(self) -> None:
        self._settings = self._collect_settings()
        self._engine.update_settings(self._settings)
        if not self._settings.infinite:
            self._progress.setMaximum(self._settings.click_count)

    def _on_cps_slider(self, v: int) -> None:
        self._cps_spin.blockSignals(True)
        self._cps_spin.setValue(float(v))
        self._cps_spin.blockSignals(False)
        self._apply_settings()

    def _on_cps_spin(self, _v: float) -> None:
        self._cps_slider.blockSignals(True)
        self._cps_slider.setValue(int(self._cps_spin.value()))
        self._cps_slider.blockSignals(False)
        self._apply_settings()

    def _on_infinite_toggle(self, checked: bool) -> None:
        self._count_spin.setEnabled(not checked)
        self._progress.setVisible(not checked)
        self._apply_settings()

    def _on_jitter_changed(self) -> None:
        self._apply_settings()

    def _set_config_enabled(self, enabled: bool) -> None:
        for w in self._config_widgets:
            w.setEnabled(enabled)

    def _update_toggle_button(self, running: bool) -> None:
        if running:
            self._toggle_btn.setText("■  Arrêter")
            self._toggle_btn.setStyleSheet(
                f"background:{COLOR_STOPPED}; color:#1e1e2e; font-weight:bold; padding:14px;"
            )
        else:
            self._toggle_btn.setText("▶  Démarrer")
            self._toggle_btn.setStyleSheet(
                f"background:{COLOR_ACTIVE}; color:#1e1e2e; font-weight:bold; padding:14px;"
            )

    def _update_progress(self, count: int) -> None:
        if self._settings.infinite:
            self._progress.setVisible(False)
            return
        self._progress.setVisible(True)
        self._progress.setMaximum(self._settings.click_count)
        self._progress.setValue(min(count, self._settings.click_count))
        self._progress.setFormat(f"{count} / {self._settings.click_count} clics")

    def _can_start(self) -> bool:
        if self._mode_saved.isChecked() and not self._settings.positions:
            QMessageBox.warning(
                self,
                "Positions manquantes",
                "Ajoutez au moins une position ou passez en mode « position actuelle ».",
            )
            return False
        return True

    def _on_toggle_clicked(self) -> None:
        if self._engine.is_running or self._countdown_remaining > 0:
            self._cancel_countdown()
            self._engine.stop()
            return
        self._begin_start()

    def _begin_start(self) -> None:
        self._apply_settings()
        if not self._can_start():
            return
        countdown = self._settings.countdown_seconds
        if countdown > 0:
            self._countdown_remaining = countdown
            self._set_config_enabled(False)
            self._toggle_btn.setEnabled(True)
            self._run_countdown_tick()
        else:
            self._engine.start()

    def _run_countdown_tick(self) -> None:
        if self._countdown_remaining <= 0:
            self._countdown_remaining = 0
            self._set_config_enabled(True)
            self._engine.start()
            return
        self._status.setText(f"● Départ dans {self._countdown_remaining}s…")
        self._status.setStyleSheet(
            f"color: {COLOR_WARN}; font-weight: bold; font-size: 14px;"
        )
        self._toggle_btn.setText("✕  Annuler")
        self._countdown_remaining -= 1
        QTimer.singleShot(1000, self._run_countdown_tick)

    def _cancel_countdown(self) -> None:
        self._countdown_remaining = 0
        self._set_config_enabled(True)
        self._update_toggle_button(False)
        self._status.setText("● Arrêté")
        self._status.setStyleSheet(
            f"color: {COLOR_STOPPED}; font-weight: bold; font-size: 14px;"
        )

    def _capture_position(self) -> None:
        x, y = self._mouse.position
        self._settings.positions.append((int(x), int(y)))
        self._refresh_positions()
        self._apply_settings()

    def _remove_position(self) -> None:
        row = self._pos_list.currentRow()
        if row >= 0:
            del self._settings.positions[row]
            self._refresh_positions()
            self._apply_settings()

    def _clear_positions(self) -> None:
        if self._settings.positions and QMessageBox.question(
            self, "Confirmation", "Supprimer toutes les positions ?"
        ) == QMessageBox.Yes:
            self._settings.positions.clear()
            self._refresh_positions()
            self._apply_settings()

    def _configure_hotkey(self, which: str) -> None:
        title = "Raccourci Start / Stop" if which == "toggle" else "Arrêt d'urgence"

        def on_captured(hotkey: str, label: str) -> None:
            if which == "toggle":
                self._settings.toggle_hotkey = hotkey
                self._settings.toggle_hotkey_label = label
                self._toggle_lbl.setText(label)
            else:
                self._settings.emergency_hotkey = hotkey
                self._settings.emergency_hotkey_label = label
                self._emergency_lbl.setText(label)
            self._hotkeys.set_hotkeys(
                self._settings.toggle_hotkey,
                self._settings.emergency_hotkey,
            )
            save_settings(self._settings)
            self._update_footer()

        KeyCaptureDialog(self, title, on_captured).exec()

    def _toggle_from_hotkey(self) -> None:
        def action() -> None:
            if self._engine.is_running or self._countdown_remaining > 0:
                self._cancel_countdown()
                self._engine.stop()
            else:
                self._begin_start()

        QTimer.singleShot(0, action)

    def _emergency_stop(self) -> None:
        QTimer.singleShot(0, lambda: (self._cancel_countdown(), self._engine.stop()))

    def _on_engine_running_change(self, active: bool) -> None:
        def update() -> None:
            self._update_toggle_button(active)
            self._set_config_enabled(not active)
            tip = f"Auto Clicker Pro — {'Actif' if active else 'Arrêté'}"
            if self._tray:
                self._tray.setToolTip(tip)
            if active:
                self._status.setText("● Actif")
                self._status.setStyleSheet(
                    f"color: {COLOR_ACTIVE}; font-weight: bold; font-size: 14px;"
                )
            elif self._countdown_remaining <= 0:
                self._status.setText("● Arrêté")
                self._status.setStyleSheet(
                    f"color: {COLOR_STOPPED}; font-weight: bold; font-size: 14px;"
                )

        QTimer.singleShot(0, update)

    def _on_click_done(self, count: int) -> None:
        QTimer.singleShot(
            0,
            lambda: (
                self._click_label.setText(f"Clics : {count}"),
                self._update_progress(count),
            ),
        )

    def closeEvent(self, event) -> None:
        if (
            not self._really_quit
            and self._minimize_tray.isChecked()
            and self._tray
            and self._tray.isVisible()
        ):
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "Auto Clicker Pro",
                "L'app tourne en arrière-plan. Clic droit sur l'icône pour quitter.",
                QSystemTrayIcon.Information,
                3000,
            )
            return
        self._cancel_countdown()
        self._engine.stop()
        self._hotkeys.stop()
        self._settings = self._collect_settings()
        save_settings(self._settings)
        if self._tray:
            self._tray.hide()
        super().closeEvent(event)


def run_app_qt() -> None:
    import sys

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    app.setWindowIcon(make_app_icon())
    win = AutoClickerWindow()
    win.show()
    sys.exit(app.exec())
