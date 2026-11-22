@echo off
call "%~dp0Commande.cmd" prepare %*
exit /b %errorlevel%
