@echo off
setlocal DisableDelayedExpansion
pushd "%~dp0" || exit /b 1
if not exist "runtime\python.exe" (
    echo Runtime embarque manquant. Extrais le ZIP Windows entier avant de lancer l'atelier.
    if not "%NSI_NONINTERACTIVE%"=="1" pause
    popd
    exit /b 1
)
if "%~1"=="prepare" if not "%NSI_NONINTERACTIVE%"=="1" (
    echo Preparation du profil hybride. Jusqu'a 2 Go seront telecharges via HTTPS.
    echo Les fichiers seront ranges dans models. Le reste fonctionne ensuite hors ligne.
    choice /C ON /N /M "Commencer la preparation [O/N] ? "
    if errorlevel 2 (
        popd
        exit /b 0
    )
)
"runtime\python.exe" -B -X utf8 -m distribution.launcher %*
set "NSI_EXIT=%errorlevel%"
if not "%NSI_NONINTERACTIVE%"=="1" (
    if not "%~1"=="start" (
        pause
    ) else if not "%NSI_EXIT%"=="0" (
        pause
    )
)
popd
exit /b %NSI_EXIT%
