@echo off
call "%~dp0Commande.cmd" start %*
exit /b %errorlevel%
