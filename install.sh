#!/bin/bash
# Installation en une seule commande — Auto Clicker Pro
# Usage : bash install.sh
# (votre mot de passe Linux peut être demandé une fois)

set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  Auto Clicker Pro — Installation"
echo "============================================"
echo ""

# Paquets système (tkinter, venv, pip, compilation pynput)
echo "[1/4] Paquets système (mot de passe admin possible)..."
sudo apt-get update -qq
sudo apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-tk \
  python3-dev \
  build-essential \
  curl

# Environnement virtuel propre
echo "[2/4] Environnement Python..."
rm -rf venv
python3 -m venv venv
source venv/bin/activate

echo "[3/4] Bibliothèques Python..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Terminé !"
echo ""
echo "Pour lancer l'app à chaque fois :"
echo "  bash run.sh"
echo ""
read -p "Lancer maintenant ? (o/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[oOyY]$ ]]; then
  python main.py
fi
