# Auto Clicker Pro

Application professionnelle de clic automatique pour **Windows** et **Linux**, écrite en Python 3.12+.

## Télécharger (utilisateurs finaux)

- **Site web** : [https://dx-de.github.io/autoclick/](https://dx-de.github.io/autoclick/)
- **Dernière version** : [GitHub Releases](https://github.com/DX-de/autoclick/releases/latest)
- Windows : `AutoClickerPro.exe`
- Linux : `AutoClickerPro-linux.zip` (dézipper puis lancer `./AutoClickerPro`)

**Pour publier toi-même l’app** (build, GitHub, releases automatiques) → voir **[DISTRIBUTION.md](DISTRIBUTION.md)**.

## Fonctionnalités

- Interface graphique moderne (thème sombre)
- Boutons **Démarrer** / **Arrêter**
- Raccourci configurable (défaut **F6**) pour basculer Start/Stop
- Arrêt d'urgence configurable (défaut **Échap**)
- Réglage des **clics par seconde** (1–100)
- Clic **gauche**, **droit** ou **molette**
- Statut **Actif** / **Arrêté** en temps réel
- **Positions enregistrées** (capture de la souris)
- Mode **position actuelle** ou **coordonnées enregistrées**
- Répétition **infinie** ou **nombre de clics** défini
- Boucle optimisée CPU (`sleep` adaptatif, pas de busy-wait)
- Configuration sauvegardée dans `~/.autoclicker/autoclicker_config.json`

## Installation

```bash
cd autoclick
python -m venv venv

# Windows
venv\Scripts\activate

# Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

### Linux — permissions

Sur Linux, l'accès global à la souris/clavier peut nécessiter d'être dans le groupe approprié ou d'exécuter sous X11/Wayland avec les permissions d'entrée. Sous Wayland, certaines distributions restreignent les hooks globaux ; privilégier X11 ou accorder les permissions à l'application si les raccourcis ne répondent pas.

## Structure du projet

```
autoclick/
├── main.py                 # Point d'entrée
├── requirements.txt
├── README.md
└── autoclicker/
    ├── __init__.py
    ├── config.py           # Modèles et valeurs par défaut
    ├── click_engine.py     # Moteur de clic (thread, CPS)
    ├── hotkey_manager.py   # Raccourcis globaux
    ├── persistence.py      # Sauvegarde JSON
    └── gui.py              # Interface CustomTkinter
```

## Exécutable Windows (PyInstaller)

Installer PyInstaller :

```bash
pip install pyinstaller
```

Générer un exécutable **sans console** (fenêtre GUI uniquement) :

```bash
pyinstaller --noconfirm --onefile --windowed --name "AutoClickerPro" ^
  --hidden-import=customtkinter ^
  --hidden-import=PIL ^
  --hidden-import=PIL._tkinter_finder ^
  --collect-all customtkinter ^
  main.py
```

Sous **Linux/macOS**, remplacer `^` par `\` pour continuer la ligne :

```bash
pyinstaller --noconfirm --onefile --windowed --name "AutoClickerPro" \
  --hidden-import=customtkinter \
  --hidden-import=PIL \
  --hidden-import=PIL._tkinter_finder \
  --collect-all customtkinter \
  main.py
```

L'exécutable se trouve dans `dist/AutoClickerPro.exe` (Windows) ou `dist/AutoClickerPro` (Linux).

### Icône personnalisée (optionnel)

```bash
pyinstaller ... --icon=assets/icon.ico main.py
```

## Avertissement

Utilisez cet outil de manière responsable et conformément aux conditions d'utilisation des logiciels et jeux concernés. L'automatisation peut être interdite sur certaines plateformes.

## Licence

Usage personnel et éducatif.
