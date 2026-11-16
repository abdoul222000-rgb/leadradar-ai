@echo off
set "PATH=C:\Users\levis\AppData\Local\Programs\Git\cmd;C:\Users\levis\AppData\Local\Programs\Git\mingw64\bin;%PATH%"
title Deploiement LeadRadar AI vers GitHub / Render
color 0A

echo ========================================================
echo   ENVOI DE LEADRADAR AI VERS GITHUB (POUR RENDER)
echo ========================================================
echo.

REM 1. Verification ou ajout du remote leadradar
git remote | findstr /C:"leadradar" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Configuration du remote GitHub pour LeadRadar AI...
    git remote add leadradar https://github.com/abdoul222000-rgb/leadradar-ai.git
)

REM 2. Ajout des fichiers indispensables pour Render
echo [INFO] Preparation des fichiers pour le deploiement...
git add leadradar_ai/
git add render.yaml
git add requirements.txt
git add run_leadradar.py
git add lancer_leadradar.bat
git add pousser_vers_leadradar.bat
git add Procfile_leadradar

REM 3. Commit
git commit -m "feat: Deploy LeadRadar AI to Render (FastAPI + Reddit/X Engine + Grey USD Billing)"

REM 4. Creation / synchronisation de la branche leadradar
git branch -M leadradar-main

REM 5. Envoi vers GitHub
echo.
echo [INFO] Envoi vers https://github.com/abdoul222000-rgb/leadradar-ai.git ...
echo.
git push -u leadradar leadradar-main --progress -v

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   SUCCES ! Le code est sur GitHub !
    echo   Render va maintenant detecter et deployer LeadRadar AI !
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   ATTENTION : Le depot n'existe peut-etre pas encore !
    echo.
    echo   1. Rendez-vous sur : https://github.com/new
    echo   2. Nommez le depot : leadradar-ai
    echo   3. Cliquez sur "Create repository" (sans ajouter de README)
    echo   4. Relancez ensuite ce fichier (pousser_vers_leadradar.bat) !
    echo ========================================================
)
echo.
pause
