#!/bin/bash
# Termine la publication GitHub (à lancer une fois — connexion navigateur possible)
set -e
cd "$(dirname "$0")"

GH="${GH_BIN:-/tmp/gh_2.67.0_linux_amd64/bin/gh}"
if [ ! -x "$GH" ]; then
  echo "Téléchargement de GitHub CLI..."
  python3 -c "import urllib.request; urllib.request.urlretrieve(
    'https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz', '/tmp/gh.tar.gz')"
  tar -xzf /tmp/gh.tar.gz -C /tmp
  GH="/tmp/gh_2.67.0_linux_amd64/bin/gh"
fi

if ! "$GH" auth status &>/dev/null; then
  echo ""
  echo ">>> Connexion GitHub (compte DX-de) — suis les instructions à l'écran <<<"
  echo ""
  "$GH" auth login -h github.com -p ssh -s repo,workflow,read:org
fi

VERSION="v1.0.0"
ZIP="dist/AutoClickerPro-linux-${VERSION}.zip"

if [ ! -f "$ZIP" ]; then
  echo "Build du binaire Linux..."
  export PATH="$HOME/.local/bin:$PATH"
  pip install -q pyinstaller --break-system-packages 2>/dev/null || true
  bash build_linux.sh 2>/dev/null || {
    pyinstaller --noconfirm --onefile --windowed --name AutoClickerPro \
      --hidden-import=PySide6 --hidden-import=pynput --collect-all PySide6 main.py
  }
  chmod +x dist/AutoClickerPro
  (cd dist && zip -j "AutoClickerPro-linux-${VERSION}.zip" AutoClickerPro)
fi

git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:DX-de/autoclick.git"

if ! "$GH" repo view DX-de/autoclick &>/dev/null; then
  echo "Création du dépôt public autoclick..."
  "$GH" repo create DX-de/autoclick --public --source=. --remote=origin \
    --description "Auto Clicker Pro — clic automatique Windows/Linux" --push
else
  git push -u origin main
fi

echo "Publication de la release ${VERSION}..."
if "$GH" release view "$VERSION" &>/dev/null; then
  "$GH" release upload "$VERSION" "$ZIP" --clobber
else
  "$GH" release create "$VERSION" "$ZIP" \
    --title "Auto Clicker Pro 1.0.0" \
    --notes "## Télécharger

- **Linux** : \`AutoClickerPro-linux-v1.0.0.zip\` — dézipper puis \`./AutoClickerPro\`
- **Windows** : build \`build_windows.bat\` sur un PC Windows, puis ajouter le .exe à cette release

## Utilisation
- **F6** : démarrer / arrêter
- **Échap** : arrêt d'urgence

Usage responsable uniquement."
fi

echo ""
echo "=========================================="
echo "  TERMINÉ !"
echo "  https://github.com/DX-de/autoclick/releases/latest"
echo "=========================================="
