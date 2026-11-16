@echo off
title LeadRadar AI - Zero-Ad Reddit & X Lead Engine
color 0A
echo ==============================================================
echo 📡 LANCEMENT DE LEADRADAR AI (PORT 8070)
echo ==============================================================
echo.
echo Activation de l'environnement virtuel Python...
call .\venv\Scripts\activate.bat
echo.
echo Demarrage du serveur FastAPI...
python run_leadradar.py
pause
