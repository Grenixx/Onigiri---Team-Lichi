@echo off
taskkill /F /IM python.exe /T

taskkill /FI "WINDOWTITLE eq FENETRE_SERVEUR" /F 
taskkill /FI "WINDOWTITLE eq FENETRE_CLIENT" /F  
taskkill /FI "WINDOWTITLE eq FENETRE_CLIENT" /F  

start "FENETRE_SERVEUR" start_server.bat
start "FENETRE_CLIENT" start_client.bat
start "FENETRE_CLIENT" start_client.bat

