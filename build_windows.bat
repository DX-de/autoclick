@echo off
REM Génère AutoClickerPro.exe (Windows) — à lancer sur un PC Windows
cd /d "%~dp0"
echo === Build Windows Auto Clicker Pro ===
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --onefile --windowed --name "AutoClickerPro" ^
  --hidden-import=PySide6 ^
  --hidden-import=PySide6.QtCore ^
  --hidden-import=PySide6.QtWidgets ^
  --hidden-import=pynput ^
  --hidden-import=pynput.mouse ^
  --hidden-import=pynput.keyboard ^
  --hidden-import=customtkinter ^
  --hidden-import=PIL ^
  --hidden-import=PIL._tkinter_finder ^
  --collect-all PySide6 ^
  --collect-all customtkinter ^
  main.py

echo.
echo Executable : dist\AutoClickerPro.exe
pause
