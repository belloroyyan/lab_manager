@echo off
cls

set ROAMING_LIBS="C:\Users\Kato\AppData\Roaming\Python\Python314\site-packages"

echo ======================================================
echo   BRIDGING LOCAL ENGINE WITH ROAMING LIBRARIES
echo ======================================================

python -m PyInstaller --noconfirm --manifest listener.manifest --onefile --console ^
    --paths "." ^
    --paths %ROAMING_LIBS% ^
    --hidden-import="colorama" ^
    --hidden-import="cryptography" ^
    --hidden-import="psutil" ^
    --hidden-import="requests" ^
    --collect-all "colorama" ^
    --icon="listener.ico" ^
    --name="listener" ^
    listener.py

pause