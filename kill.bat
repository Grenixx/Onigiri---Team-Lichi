@echo off

taskkill /F /IM python.exe /T

taskkill /FI "WINDOWTITLE eq FENETRE_SERVEUR" /F 
taskkill /FI "WINDOWTITLE eq FENETRE_CLIENT" /F  