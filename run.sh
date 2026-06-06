#!/bin/bash
# Lance Auto Clicker Pro (un double-clic ou cette commande suffit)
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

# Ne jamais hériter d'un rendu hors écran (sinon la fenêtre est invisible)
if [ "$QT_QPA_PLATFORM" = "offscreen" ]; then
  unset QT_QPA_PLATFORM
fi

# Sous Wayland, forcer le plugin wayland (le plugin xcb/XWayland peut manquer
# de libxcb-cursor0 et empêcher l'affichage).
if [ -z "$QT_QPA_PLATFORM" ] && [ -n "$WAYLAND_DISPLAY" ]; then
  export QT_QPA_PLATFORM=wayland
fi

if [ -d "venv" ]; then
  source venv/bin/activate
fi

exec python3 main.py
