@echo off
cls

set ROAMING_LIBS="C:\Users\Kato\AppData\Roaming\Python\Python314\site-packages"

echo ======================================================
echo   BRIDGING LOCAL ENGINE WITH ROAMING LIBRARIES
echo ======================================================

:: 2. Run PyInstaller and MANUALLY point to the Roaming folder
python -m PyInstaller --noconfirm --onefile --console ^
    --paths "." ^
    --paths %ROAMING_LIBS% ^
    --hidden-import="colorama" ^
    --hidden-import="requests" ^
    --collect-all "colorama" ^
    --add-data "config.ini;." ^
    --icon="lab_icon.ico" ^
    main.py

pause