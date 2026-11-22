@echo off
call "%~dp0Commande.cmd" stop %*
exit /b %errorlevel%
