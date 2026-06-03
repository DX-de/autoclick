#!/bin/bash
# Génère dist/AutoClickerPro (Linux)
set -e
cd "$(dirname "$0")"

echo "=== Build Linux Auto Clicker Pro ==="
pip install -r requirements.txt pyinstaller --break-system-packages 2>/dev/null \
  || pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --onefile --windowed --name "AutoClickerPro" \
  --hidden-import=PySide6 \
  --hidden-import=PySide6.QtCore \
  --hidden-import=PySide6.QtWidgets \
  --hidden-import=pynput \
  --hidden-import=pynput.mouse \
  --hidden-import=pynput.keyboard \
  --hidden-import=customtkinter \
  --hidden-import=PIL \
  --collect-all PySide6 \
  --collect-all customtkinter \
  main.py

echo ""
echo "Exécutable : dist/AutoClickerPro"
echo "Test : ./dist/AutoClickerPro"
