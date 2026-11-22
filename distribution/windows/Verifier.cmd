@echo off
call "%~dp0Commande.cmd" verify %*
exit /b %errorlevel%
