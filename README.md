Yo c est Enzo 
Pour lancer le jeu faut lancer un server le plus recent dans ninja_game_server
Puis dans ninja_game lancer game.py

Dependencies: 
pip install pygame moderngl numpy miniupnpc screeninfo

C:\Users\enzom\Downloads\PythonMultiplayerNetworking\ninja_game>pyinstaller --onefile --add-data "data;data" --add-data "scripts;scripts" game.py

Pour compiler en exe il faut allez dans ninja game puis lancer la commande suivante 
pyinstaller --onefile --add-data "data;data" --add-data "scripts;scripts" game.py