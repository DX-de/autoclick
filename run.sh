#!/bin/bash
# Lance Auto Clicker Pro (une double-clic ou cette commande suffit)
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

exec python3 main.py
