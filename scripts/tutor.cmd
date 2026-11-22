@echo off
setlocal EnableExtensions
pushd "%~dp0.." || exit /b 1
py -3.12 -c "import platform, struct; raise SystemExit(0 if struct.calcsize('P') == 8 and platform.machine().lower() in ('amd64', 'x86_64') else 1)" >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 et son lanceur py sont requis sur Windows x64.
    echo Ouvrez le guide docs\P5_PERFORMANCES_WINDOWS.md pour les preparer.
    popd
    exit /b 1
)
if not exist "tutor\server.py" (
    echo Lanceur incomplet. Placez scripts\tutor.cmd dans le dossier du projet.
    popd
    exit /b 1
)
echo Ouvrez l'adresse affichee par le serveur. Ctrl+C arrete l'atelier.
if exist ".venv-p5\Scripts\python.exe" (
    ".venv-p5\Scripts\python.exe" -m tutor.server %*
) else (
    py -3.12 -m tutor.server %*
)
set "NSI_TUTOR_EXIT=%errorlevel%"
popd
exit /b %NSI_TUTOR_EXIT%
