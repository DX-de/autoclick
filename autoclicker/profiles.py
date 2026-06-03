"""
Gestion des profils de configuration (presets).
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

from autoclicker.config import AppSettings
from autoclicker.persistence import dict_to_settings, settings_to_dict

_PROFILES_NAME = "profiles.json"


def _profiles_path() -> Path:
    base = Path.home() / ".autoclicker"
    base.mkdir(parents=True, exist_ok=True)
    return base / _PROFILES_NAME


def _load_raw() -> Dict:
    path = _profiles_path()
    if not path.exists():
        return {"active": "", "profiles": {}}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"active": "", "profiles": {}}


def _save_raw(data: Dict) -> None:
    with _profiles_path().open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_profiles() -> List[str]:
    return sorted(_load_raw().get("profiles", {}).keys())


def get_active_profile_name() -> str:
    return _load_raw().get("active", "")


def set_active_profile(name: str) -> None:
    data = _load_raw()
    data["active"] = name
    _save_raw(data)


def save_profile(name: str, settings: AppSettings) -> None:
    name = name.strip()
    if not name:
        raise ValueError("Nom de profil vide")
    data = _load_raw()
    profiles = data.setdefault("profiles", {})
    profiles[name] = settings_to_dict(settings)
    data["active"] = name
    _save_raw(data)


def load_profile(name: str) -> AppSettings:
    data = _load_raw()
    raw = data.get("profiles", {}).get(name)
    if raw is None:
        raise KeyError(name)
    return dict_to_settings(raw)


def delete_profile(name: str) -> None:
    data = _load_raw()
    profiles = data.get("profiles", {})
    if name not in profiles:
        return
    del profiles[name]
    if data.get("active") == name:
        data["active"] = next(iter(sorted(profiles)), "")
    _save_raw(data)


def profile_exists(name: str) -> bool:
    return name in _load_raw().get("profiles", {})
