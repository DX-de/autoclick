#!/bin/bash
# Publie Auto Clicker Pro sur GitHub (dépôt + release)
set -e
cd "$(dirname "$0")"

GH="${GH_BIN:-gh}"
if ! command -v "$GH" &>/dev/null; then
  GH="/tmp/gh_2.67.0_linux_amd64/bin/gh"
fi

if ! "$GH" auth status &>/dev/null; then
  echo "Connexion GitHub requise (une seule fois)..."
  "$GH" auth login -w -p https
fi

REPO_NAME="${1:-autoclick}"
VERSION="${2:-v1.0.0}"

echo "=== Build Linux ==="
if [ -x "./venv/bin/pyinstaller" ]; then
  ./venv/bin/pip install -q -r requirements.txt pyinstaller
  ./venv/bin/pyinstaller --noconfirm --onefile --windowed --name "AutoClickerPro" \
    --hidden-import=PySide6 --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtWidgets \
    --hidden-import=pynput --hidden-import=customtkinter \
    --collect-all PySide6 --collect-all customtkinter main.py
else
  bash build_linux.sh
fi

chmod +x dist/AutoClickerPro 2>/dev/null || true
(cd dist && zip -j "AutoClickerPro-linux-${VERSION}.zip" AutoClickerPro)

echo "=== Git ==="
git init -b main 2>/dev/null || git checkout -b main 2>/dev/null || true
git add -A
git diff --cached --quiet || git commit -m "Auto Clicker Pro ${VERSION}"

echo "=== Dépôt GitHub ==="
if ! "$GH" repo view "$REPO_NAME" &>/dev/null 2>&1; then
  "$GH" repo create "$REPO_NAME" --public --source=. --remote=origin --push --description "Auto Clicker Pro - clic automatique Windows/Linux"
else
  git remote add origin "$("$GH" repo view "$REPO_NAME" --json url -q .url)" 2>/dev/null || true
  git push -u origin main
fi

echo "=== Release ${VERSION} ==="
"$GH" release create "$VERSION" \
  dist/AutoClickerPro-linux-"${VERSION}".zip \
  --title "Auto Clicker Pro ${VERSION}" \
  --notes "Téléchargez AutoClickerPro-linux.zip, dézippez et lancez ./AutoClickerPro. Windows: build sur PC Windows avec build_windows.bat puis ajoutez le .exe à la release."

echo ""
echo "Terminé ! Lien :"
"$GH" release view "$VERSION" --json url -q .url
