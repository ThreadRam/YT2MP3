<img width="1382" height="812" alt="2026-05-05_00h52_51" src="https://github.com/user-attachments/assets/d2df1745-ce50-451e-98a9-91686b742005" />
Rôle des fichiers
YT2MP3.py

Script principal de l’application.

Il contient :

l’interface graphique Tkinter ;
la gestion de la file d’attente ;
l’ajout d’URLs individuelles ;
le chargement d’un fichier .txt ;
la récupération des métadonnées vidéo ;
l’affichage des miniatures ;
le téléchargement audio via yt-dlp;
la conversion en MP3 via FFmpeg ;
l’intégration des jaquettes et métadonnées ;
la gestion des erreurs, annulations et reprises ;
l’aide intégrée à l’application.
requirements.txt

Liste des dépendances Python nécessaires au projet.

yt-dlp>=2025.0.0
Pillow>=10.0.0
mutagen>=1.47.0
README.md

Documentation du projet.

Il explique :

l’objectif du projet ;
les systèmes compatibles ;
les prérequis ;
l’installation ;
l’utilisation ;
les commandes utiles ;
les erreurs fréquentes ;
le fonctionnement général de l’application.

Prérequis :

Python 3.10 ou supérieur
FFmpeg
Une connexion Internet

Installation des dépendances Python

Depuis le dossier du projet :

Windows
python -m pip install -r requirements.txt
Linux / macOS
python3 -m pip install -r requirements.txt

Le script peut aussi installer automatiquement les dépendances Python manquantes au lancement.

Installation de FFmpeg

FFmpeg est nécessaire pour :

convertir l’audio en MP3 ;
intégrer les métadonnées ;
intégrer la miniature comme jaquette.
Windows

Avec winget :

winget install Gyan.FFmpeg

Vérifier l’installation :

ffmpeg -version
ffprobe -version
Linux

Debian / Ubuntu :

sudo apt update
sudo apt install ffmpeg

Vérifier l’installation :

ffmpeg -version
ffprobe -version
macOS

Avec Homebrew :

brew install ffmpeg

Vérifier l’installation :

ffmpeg -version
ffprobe -version
Trouver le chemin FFmpeg

L’application essaie de détecter FFmpeg automatiquement.

Si la détection échoue, vous pouvez renseigner manuellement le dossier contenant ffmpeg et ffprobe.

Windows

Dans PowerShell :

where.exe ffmpeg
where.exe ffprobe

Exemple :

C:\Users\Devops\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe

Dans l’application, renseigner uniquement le dossier bin.

Exemple correct :

C:\Users\Devops\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin

Exemple incorrect :

C:\Users\Devops\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe
Linux / macOS

Dans un terminal :

which ffmpeg
which ffprobe

Exemple Linux :

/usr/bin/ffmpeg
/usr/bin/ffprobe

Dans l’application, renseigner uniquement le dossier :

/usr/bin

Exemple macOS avec Homebrew Apple Silicon :

/opt/homebrew/bin/ffmpeg
/opt/homebrew/bin/ffprobe

Dans l’application, renseigner uniquement :

/opt/homebrew/bin

Exemple macOS avec Homebrew Intel :

/usr/local/bin/ffmpeg
/usr/local/bin/ffprobe

Dans l’application, renseigner uniquement :

/usr/local/bin
Lancement de l’application
Windows
python YT2MP3.py OU py YT2MP3.py
Linux / macOS
python3 YT2MP3.py.py
Utilisation
Ajouter une seule vidéo
Copier une URL YouTube.
Coller l’URL dans le champ prévu.
Cliquer sur Ajouter cette URL à la file.
Vérifier la vidéo dans la file d’attente.
Cliquer sur Démarrer le téléchargement MP3.
Ajouter plusieurs vidéos avec un fichier TXT
Créer un fichier .txt.
Ajouter une URL YouTube par ligne.
Cliquer sur Choisir et charger un fichier TXT.
Sélectionner le fichier.
La file se charge automatiquement.
Cliquer sur Démarrer le téléchargement MP3.
Format du fichier TXT

Exemple :

https://www.youtube.com/watch?v=XXXXXXXXXXX

https://www.youtube.com/watch?v=YYYYYYYYYYY
# Cette ligne est ignorée
https://www.youtube.com/watch?v=ZZZZZZZZZZZ

Règles de lecture :

une URL par ligne ;
les lignes vides sont ignorées ;
plusieurs lignes vides d’affilée sont ignorées ;
les lignes qui commencent par # sont ignorées ;
la lecture continue jusqu’à la fin du fichier.
Options disponibles
Qualité MP3

Permet de choisir le bitrate du fichier final.

Options disponibles :

128 kbps
192 kbps
256 kbps
320 kbps
Autoriser les playlists

Si cette option est activée, une URL de playlist peut ajouter plusieurs vidéos dans la file.

Si elle est désactivée, seule la vidéo ciblée est traitée.

Intégrer la miniature comme jaquette MP3

Télécharge la miniature YouTube et l’intègre dans le fichier MP3 final.

Cette jaquette est visible dans les lecteurs compatibles comme VLC, MusicBee, Windows Media Player, Plex ou autres lecteurs audio prenant en charge les jaquettes intégrées.

Ajouter les métadonnées audio

Ajoute les informations disponibles dans le fichier MP3, par exemple :

titre ;
artiste ;
source ;
date ;
informations récupérées par yt-dlp.
Supprimer les fichiers temporaires

Supprime les fichiers intermédiaires après conversion :

.webm
.m4a
miniatures temporaires
Rôle des principales fonctions du script
ensure_package()

Vérifie si une dépendance Python est installée.

Si elle est absente, elle est installée automatiquement avec pip.

detect_ffmpeg_dir_silent()

Recherche automatiquement ffmpeg et ffprobe dans le PATH du système.

Si les deux exécutables sont trouvés, le dossier correspondant est utilisé automatiquement.

get_ffmpeg_location()

Valide le chemin FFmpeg utilisé par l’application.

La fonction vérifie que le dossier contient bien :

ffmpeg.exe et ffprobe.exe sur Windows ;
ffmpeg et ffprobe sur Linux / macOS.
install_ffmpeg_with_winget()

Lance l’installation de FFmpeg avec winget.

Cette fonction est uniquement prévue pour Windows.

add_single_url()

Ajoute une seule URL à la file d’attente.

La fonction récupère les métadonnées de la vidéo :

titre ;
durée ;
miniature ;
URL finale.
load_metadata()

Charge les URLs depuis un fichier .txt.

Chaque URL est analysée avec yt-dlp, puis ajoutée à la file d’attente.

download_queue()

Parcourt la file d’attente et télécharge les vidéos une par une.

Elle gère :

les vidéos en attente ;
les erreurs ;
les annulations ;
les vidéos déjà terminées.
download_one()

Télécharge une vidéo précise.

Cette fonction gère :

le téléchargement audio ;
la conversion MP3 ;
l’ajout de la jaquette ;
l’ajout des métadonnées ;
la progression ;
l’annulation.
build_postprocessors()

Construit la liste des traitements à appliquer après téléchargement.

Selon les options choisies, elle ajoute :

conversion MP3 ;
métadonnées ;
jaquette.
toggle_pause()

Met le téléchargement en pause ou le reprend.

cancel_selected()

Annule la vidéo sélectionnée dans la file d’attente.

cancel_everything()

Annule toute la file de téléchargement.

retry_failed_items()

Remet en attente les vidéos ayant échoué ou ayant été annulées.

open_selected_video()

Ouvre la vidéo sélectionnée dans le navigateur par défaut.

show_help_window()

Affiche une fenêtre d’aide intégrée contenant les commandes utiles et les explications d’installation.

Statuts de la file d’attente
Statut	Description
En attente	La vidéo est prête à être téléchargée.
Téléchargement	Le téléchargement est en cours.
Conversion MP3	Le fichier audio est en cours de conversion.
En pause	Le téléchargement est temporairement suspendu.
Terminé	Le fichier MP3 a été créé avec succès.
Erreur	Une erreur est survenue.
Annulé	La vidéo a été annulée.
Problèmes fréquents
FFmpeg introuvable

Erreur possible :

ffmpeg and ffprobe not found

Solutions :

Installer FFmpeg.
Cliquer sur Détecter dans l’application.
Choisir manuellement le dossier contenant ffmpeg et ffprobe.
Vérifier le chemin dans un terminal.

Windows :

where.exe ffmpeg
where.exe ffprobe

Linux / macOS :

which ffmpeg
which ffprobe
Vidéo privée

Erreur possible :

Private video

La vidéo est privée ou nécessite une connexion.

Vidéo indisponible

Erreur possible :

Video unavailable

La vidéo peut être supprimée, bloquée ou indisponible dans votre région.

La conversion sort en .webm au lieu de .mp3

Cela indique généralement que FFmpeg n’est pas trouvé.

Vérifier que le chemin configuré pointe vers le dossier contenant :

Windows :

ffmpeg.exe
ffprobe.exe

Linux / macOS :

ffmpeg
ffprobe
Commandes développeur

Cloner le dépôt :

git clone https://github.com/TON-USER/TON-REPO.git

Entrer dans le dossier :

cd TON-REPO

Créer un environnement virtuel :

Windows
python -m venv .venv
.venv\Scripts\activate
Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

Installer les dépendances :

Windows
python -m pip install -r requirements.txt
Linux / macOS
python3 -m pip install -r requirements.txt

Lancer l’application :

Windows
python mp3_gui_queue.py
Linux / macOS
python3 mp3_gui_queue.py
Bonnes pratiques
Utiliser un dossier de sortie dédié.
Vérifier la file avant de démarrer le téléchargement.
Désactiver les playlists si vous voulez télécharger uniquement une vidéo.
Garder l’option jaquette activée si vous voulez un MP3 propre dans un lecteur audio.
Utiliser Réessayer erreurs / annulées après une coupure réseau ou une erreur temporaire.
Garder FFmpeg installé et accessible dans le PATH si possible.
Limites connues
Les vidéos privées ne peuvent pas être téléchargées sans authentification.
Certaines vidéos peuvent être bloquées selon la région.
La pause dépend des callbacks de yt-dlp et peut ne pas être instantanée.
Les playlists très longues peuvent prendre du temps à analyser.
L’installation automatique de FFmpeg via l’interface est uniquement prévue pour Windows avec winget.
Sur Linux et macOS, FFmpeg doit être installé via le gestionnaire de paquets du système.
Avertissement

Ce projet doit être utilisé uniquement avec des contenus que vous avez le droit de télécharger.

Respectez les droits d’auteur, les conditions d’utilisation des plateformes et la législation applicable.
