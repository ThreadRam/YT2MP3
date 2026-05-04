import sys
import subprocess
import importlib.util


def ensure_package(import_name, pip_name=None):
    """
    Installe automatiquement une dépendance Python si elle est absente.
    """
    pip_name = pip_name or import_name

    if importlib.util.find_spec(import_name) is None:
        print(f"[INSTALL] Installation de {pip_name}...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            pip_name
        ])


# Dépendances Python auto-installées au lancement.
ensure_package("yt_dlp", "yt-dlp")
ensure_package("PIL", "pillow")
ensure_package("mutagen", "mutagen")


import io
import os
import re
import shutil
import threading
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
import yt_dlp


APP_TITLE = "YT2MP3 - Téléchargeur MP3"


HELP_TEXT = r"""
YT2MP3 - Aide d'installation

1. Installer Python

Windows :
    winget install Python.Python.3.12

Vérifier Python :
    python --version
    pip --version


2. Installer les dépendances Python

Normalement, l'application les installe automatiquement au lancement.

Commande manuelle :
    python -m pip install -U yt-dlp pillow mutagen


3. Installer FFmpeg

Windows avec winget :
    winget install Gyan.FFmpeg

Vérifier FFmpeg :
    ffmpeg -version
    ffprobe -version


4. Trouver le chemin FFmpeg

Dans PowerShell :
    where.exe ffmpeg
    where.exe ffprobe

Exemple de résultat :
    C:\Users\Devops\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe

Dans l'application, il faut mettre uniquement le dossier bin :

    C:\Users\Devops\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin

Ne pas mettre :
    ...\ffmpeg.exe


5. Format du fichier TXT

Le fichier TXT doit contenir une URL par ligne :

    https://www.youtube.com/watch?v=XXXXXXXXXXX
    https://www.youtube.com/watch?v=YYYYYYYYYYY
    https://www.youtube.com/playlist?list=ZZZZZZZZZZZ

Les lignes vides sont ignorées.
Les lignes qui commencent par # sont ignorées.


6. Utilisation rapide

- Coller une URL dans le champ URL
- Cliquer sur Ajouter cette URL à la file

ou

- Choisir un fichier TXT
- La file se charge automatiquement

Puis :

- Choisir le dossier de sortie
- Choisir la qualité MP3
- Activer ou désactiver la jaquette
- Cliquer sur Démarrer le téléchargement MP3


7. Options importantes

Intégrer la miniature comme jaquette MP3 :
    Ajoute la miniature YouTube dans le fichier MP3.

Ajouter les métadonnées audio :
    Ajoute titre, artiste et autres infos disponibles.

Supprimer les fichiers temporaires :
    Supprime les fichiers .webm, .m4a ou images temporaires après conversion.


8. Problèmes fréquents

Erreur :
    ffmpeg and ffprobe not found

Solution :
    Installer FFmpeg ou choisir manuellement le dossier bin dans l'application.

Erreur :
    Private video

Solution :
    La vidéo est privée ou inaccessible.

Erreur :
    Video unavailable

Solution :
    La vidéo est supprimée, bloquée ou indisponible dans ta région.


9. Commandes développeur

Cloner le projet :
    git clone https://github.com/TON-USER/TON-REPO.git

Entrer dans le dossier :
    cd TON-REPO

Créer un environnement virtuel :
    python -m venv .venv

Activer l'environnement virtuel Windows :
    .venv\Scripts\activate

Installer les dépendances :
    python -m pip install -U yt-dlp pillow mutagen

Lancer l'application :
    python mp3_gui_queue.py
"""


class YTDLPLogger:
    def __init__(self, app):
        self.app = app

    def debug(self, message):
        pass

    def info(self, message):
        self.app.log(message)

    def warning(self, message):
        self.app.log(f"[AVERTISSEMENT] {message}")

    def error(self, message):
        self.app.log(f"[ERREUR] {message}")


class MP3QueueDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1380x780")
        self.root.minsize(1180, 700)

        self.txt_file = tk.StringVar()
        self.single_url = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "mp3"))

        self.ffmpeg_dir = tk.StringVar(value=self.detect_ffmpeg_dir_silent())

        self.quality = tk.StringVar(value="320")
        self.allow_playlist = tk.BooleanVar(value=False)
        self.embed_cover = tk.BooleanVar(value=True)
        self.add_metadata = tk.BooleanVar(value=True)
        self.delete_temp_files = tk.BooleanVar(value=True)

        self.queue = []
        self.current_index = None

        self.is_loading_metadata = False
        self.is_downloading = False

        self.pause_event = threading.Event()
        self.pause_event.set()

        self.cancel_all = False
        self.cancelled_ids = set()

        self.thumbnail_image = None

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        title = ttk.Label(
            left,
            text="Téléchargeur YouTube vers MP3",
            font=("Arial", 18, "bold")
        )
        title.pack(anchor="w", pady=(0, 6))

        subtitle = ttk.Label(
            left,
            text="Ajoute une URL ou un fichier TXT, vérifie la file, puis démarre le téléchargement MP3.",
            font=("Arial", 10)
        )
        subtitle.pack(anchor="w", pady=(0, 10))

        self.build_source_section(left)
        self.build_settings_section(left)
        self.build_actions_section(left)
        self.build_logs_section(left)

        self.build_queue_section(right)
        self.build_preview_section(right)

        self.log_startup_status()

    def build_source_section(self, parent):
        source_frame = ttk.LabelFrame(parent, text="Sources")
        source_frame.pack(fill=tk.X, pady=5)

        url_frame = ttk.Frame(source_frame)
        url_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        ttk.Label(url_frame, text="URL vidéo ou playlist :").pack(anchor="w")

        url_entry_frame = ttk.Frame(url_frame)
        url_entry_frame.pack(fill=tk.X, pady=(4, 0))

        self.url_entry = ttk.Entry(url_entry_frame, textvariable=self.single_url)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            url_entry_frame,
            text="Ajouter cette URL à la file",
            command=self.add_single_url_thread
        ).pack(side=tk.RIGHT, padx=(8, 0))

        txt_frame = ttk.Frame(source_frame)
        txt_frame.pack(fill=tk.X, padx=8, pady=(8, 8))

        ttk.Label(txt_frame, text="Fichier TXT, une URL par ligne :").pack(anchor="w")

        txt_entry_frame = ttk.Frame(txt_frame)
        txt_entry_frame.pack(fill=tk.X, pady=(4, 0))

        ttk.Entry(txt_entry_frame, textvariable=self.txt_file).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        ttk.Button(
            txt_entry_frame,
            text="Choisir et charger un fichier TXT",
            command=self.select_txt_file
        ).pack(side=tk.RIGHT, padx=(8, 0))

    def build_settings_section(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Réglages")
        settings_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(row1, text="Qualité MP3 :").pack(side=tk.LEFT)

        ttk.Combobox(
            row1,
            textvariable=self.quality,
            values=["128", "192", "256", "320"],
            state="readonly",
            width=8
        ).pack(side=tk.LEFT, padx=(8, 20))

        ttk.Checkbutton(
            row1,
            text="Autoriser les playlists",
            variable=self.allow_playlist
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(
            row1,
            text="Intégrer la miniature comme jaquette MP3",
            variable=self.embed_cover
        ).pack(side=tk.LEFT)

        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Checkbutton(
            row2,
            text="Ajouter les métadonnées audio",
            variable=self.add_metadata
        ).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Checkbutton(
            row2,
            text="Supprimer les fichiers temporaires",
            variable=self.delete_temp_files
        ).pack(side=tk.LEFT)

        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Label(output_frame, text="Dossier de sortie :").pack(anchor="w")

        output_entry_frame = ttk.Frame(output_frame)
        output_entry_frame.pack(fill=tk.X, pady=(4, 0))

        ttk.Entry(output_entry_frame, textvariable=self.output_dir).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        ttk.Button(
            output_entry_frame,
            text="Choisir le dossier",
            command=self.select_output_dir
        ).pack(side=tk.RIGHT, padx=(8, 0))

        ffmpeg_frame = ttk.Frame(settings_frame)
        ffmpeg_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Label(
            ffmpeg_frame,
            text="Dossier FFmpeg bin, contenant ffmpeg.exe et ffprobe.exe :"
        ).pack(anchor="w")

        ffmpeg_entry_frame = ttk.Frame(ffmpeg_frame)
        ffmpeg_entry_frame.pack(fill=tk.X, pady=(4, 0))

        ttk.Entry(ffmpeg_entry_frame, textvariable=self.ffmpeg_dir).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        ttk.Button(
            ffmpeg_entry_frame,
            text="Choisir FFmpeg",
            command=self.select_ffmpeg_dir
        ).pack(side=tk.RIGHT, padx=(8, 0))

        ttk.Button(
            ffmpeg_entry_frame,
            text="Détecter",
            command=self.detect_ffmpeg_dir_button
        ).pack(side=tk.RIGHT, padx=(8, 0))

        ttk.Button(
            ffmpeg_entry_frame,
            text="Installer FFmpeg",
            command=self.install_ffmpeg_thread
        ).pack(side=tk.RIGHT, padx=(8, 0))

    def build_actions_section(self, parent):
        actions = ttk.LabelFrame(parent, text="Actions")
        actions.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(actions)
        row1.pack(fill=tk.X, padx=8, pady=8)

        self.start_button = ttk.Button(
            row1,
            text="Démarrer le téléchargement MP3",
            command=self.start_download_thread
        )
        self.start_button.pack(side=tk.LEFT)

        self.pause_button = ttk.Button(
            row1,
            text="Mettre en pause",
            command=self.toggle_pause
        )
        self.pause_button.pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row1,
            text="Annuler la vidéo sélectionnée",
            command=self.cancel_selected
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row1,
            text="Annuler tous les téléchargements",
            command=self.cancel_everything
        ).pack(side=tk.LEFT, padx=6)

        row2 = ttk.Frame(actions)
        row2.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.load_button = ttk.Button(
            row2,
            text="Recharger le TXT dans la file",
            command=self.start_metadata_thread
        )
        self.load_button.pack(side=tk.LEFT)

        ttk.Button(
            row2,
            text="Ouvrir la vidéo sélectionnée",
            command=self.open_selected_video
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row2,
            text="Réessayer erreurs / annulées",
            command=self.retry_failed_items
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row2,
            text="Retirer annulées",
            command=self.remove_cancelled_items
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row2,
            text="Retirer terminées",
            command=self.remove_finished_items
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row2,
            text="Vider toute la file",
            command=self.clear_queue
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            row2,
            text="Aide / Installation",
            command=self.show_help_window
        ).pack(side=tk.LEFT, padx=6)

    def build_logs_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Journal d'activité")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text.config(yscrollcommand=log_scroll.set)

    def build_queue_section(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            header,
            text="File d'attente",
            font=("Arial", 15, "bold")
        ).pack(side=tk.LEFT)

        self.queue_count_label = ttk.Label(header, text="0 élément")
        self.queue_count_label.pack(side=tk.RIGHT)

        columns = ("title", "duration", "status", "progress")
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=24
        )

        self.tree.heading("title", text="Titre")
        self.tree.heading("duration", text="Durée")
        self.tree.heading("status", text="Statut")
        self.tree.heading("progress", text="Progression")

        self.tree.column("title", width=500)
        self.tree.column("duration", width=80, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.column("progress", width=100, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_video)
        self.tree.bind("<Double-1>", lambda event: self.open_selected_video())

    def build_preview_section(self, parent):
        preview = ttk.LabelFrame(parent, text="Aperçu vidéo / jaquette")
        preview.pack(fill=tk.X, pady=10)

        self.thumbnail_label = ttk.Label(preview, text="Aucune miniature")
        self.thumbnail_label.pack(padx=10, pady=10)

        self.selected_info = ttk.Label(parent, text="", wraplength=650)
        self.selected_info.pack(anchor="w", pady=5)

    def show_help_window(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Aide / Installation")
        help_window.geometry("900x650")
        help_window.minsize(700, 500)

        frame = ttk.Frame(help_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            frame,
            text="Aide d'installation et d'utilisation",
            font=("Arial", 16, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        help_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10)
        )
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        help_text.config(yscrollcommand=scrollbar.set)
        help_text.insert(tk.END, HELP_TEXT)
        help_text.config(state=tk.DISABLED)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Copier l'aide",
            command=lambda: self.copy_text_to_clipboard(HELP_TEXT)
        ).pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Fermer",
            command=help_window.destroy
        ).pack(side=tk.RIGHT)

    def copy_text_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Copié", "Le texte d'aide a été copié dans le presse-papiers.")

    def log_startup_status(self):
        self.log("Application démarrée.")
        self.log("Les dépendances Python sont vérifiées automatiquement au lancement.")
        self.log("Clique sur 'Aide / Installation' pour voir les commandes utiles.")

        ffmpeg_dir = self.ffmpeg_dir.get().strip()

        if ffmpeg_dir:
            self.log(f"FFmpeg détecté : {ffmpeg_dir}")
        else:
            self.log("FFmpeg non détecté automatiquement.")
            self.log("Utilise le bouton 'Installer FFmpeg', 'Détecter' ou 'Choisir FFmpeg'.")

    def clean_ansi(self, text):
        return re.sub(r"\x1b\[[0-9;]*m", "", str(text))

    def log(self, message):
        if not message:
            return

        clean_message = self.clean_ansi(message)

        def append():
            self.log_text.insert(tk.END, clean_message + "\n")
            self.log_text.see(tk.END)

        self.root.after(0, append)

    def detect_ffmpeg_dir_silent(self):
        ffmpeg_path = shutil.which("ffmpeg")
        ffprobe_path = shutil.which("ffprobe")

        if ffmpeg_path and ffprobe_path:
            ffmpeg_dir = Path(ffmpeg_path).parent

            ffmpeg_file = ffmpeg_dir / "ffmpeg.exe"
            ffprobe_file = ffmpeg_dir / "ffprobe.exe"

            if ffmpeg_file.exists() and ffprobe_file.exists():
                return str(ffmpeg_dir)

        return ""

    def detect_ffmpeg_dir_button(self):
        ffmpeg_dir = self.detect_ffmpeg_dir_silent()

        if ffmpeg_dir:
            self.ffmpeg_dir.set(ffmpeg_dir)
            self.log(f"FFmpeg détecté : {ffmpeg_dir}")
            messagebox.showinfo("FFmpeg détecté", f"FFmpeg trouvé :\n{ffmpeg_dir}")
        else:
            messagebox.showwarning(
                "FFmpeg introuvable",
                "FFmpeg n'a pas été détecté automatiquement. "
                "Installe-le ou choisis manuellement le dossier bin."
            )

    def select_ffmpeg_dir(self):
        path = filedialog.askdirectory(
            title="Choisir le dossier bin de FFmpeg contenant ffmpeg.exe et ffprobe.exe"
        )

        if path:
            self.ffmpeg_dir.set(path)

            try:
                self.get_ffmpeg_location()
                self.log(f"Dossier FFmpeg configuré : {path}")
                messagebox.showinfo("FFmpeg configuré", "Le dossier FFmpeg est valide.")
            except Exception as error:
                messagebox.showerror("Erreur FFmpeg", str(error))

    def get_ffmpeg_location(self):
        ffmpeg_dir = self.ffmpeg_dir.get().strip()

        if ffmpeg_dir:
            ffmpeg_path = Path(ffmpeg_dir) / "ffmpeg.exe"
            ffprobe_path = Path(ffmpeg_dir) / "ffprobe.exe"

            if not ffmpeg_path.exists() or not ffprobe_path.exists():
                raise FileNotFoundError(
                    "Le dossier FFmpeg choisi doit contenir ffmpeg.exe et ffprobe.exe."
                )

            return ffmpeg_dir

        detected = self.detect_ffmpeg_dir_silent()

        if detected:
            self.ffmpeg_dir.set(detected)
            return detected

        raise FileNotFoundError(
            "FFmpeg introuvable. Clique sur Installer FFmpeg ou choisis manuellement "
            "le dossier bin contenant ffmpeg.exe et ffprobe.exe."
        )

    def install_ffmpeg_thread(self):
        thread = threading.Thread(target=self.install_ffmpeg_with_winget, daemon=True)
        thread.start()

    def install_ffmpeg_with_winget(self):
        if os.name != "nt":
            messagebox.showwarning(
                "Installation non disponible",
                "L'installation automatique FFmpeg via winget est prévue pour Windows."
            )
            return

        winget_path = shutil.which("winget")

        if not winget_path:
            messagebox.showerror(
                "Winget introuvable",
                "winget n'est pas disponible. Installe FFmpeg manuellement depuis gyan.dev."
            )
            return

        self.log("Installation de FFmpeg via winget...")
        self.log("Commande utilisée : winget install Gyan.FFmpeg")

        try:
            process = subprocess.Popen(
                [
                    "winget",
                    "install",
                    "Gyan.FFmpeg",
                    "--accept-source-agreements",
                    "--accept-package-agreements"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in process.stdout:
                self.log(line.strip())

            process.wait()

            if process.returncode != 0:
                self.log(f"Installation FFmpeg terminée avec code erreur : {process.returncode}")
                messagebox.showwarning(
                    "Installation FFmpeg",
                    "L'installation ne semble pas terminée correctement. Vérifie les logs."
                )
                return

            detected = self.detect_ffmpeg_dir_silent()

            if detected:
                self.ffmpeg_dir.set(detected)
                self.log(f"FFmpeg installé et détecté : {detected}")
                messagebox.showinfo("FFmpeg installé", f"FFmpeg détecté :\n{detected}")
            else:
                self.log("FFmpeg installé, mais non détecté. Redémarre l'application ou choisis le dossier bin.")
                messagebox.showwarning(
                    "FFmpeg installé",
                    "FFmpeg semble installé, mais n'a pas été détecté. "
                    "Redémarre l'application ou choisis le dossier bin manuellement."
                )

        except Exception as error:
            self.log(f"Erreur installation FFmpeg : {error}")
            messagebox.showerror("Erreur installation FFmpeg", str(error))

    def update_queue_count(self):
        count = len([
            item for item in self.queue
            if item["id"] in self.tree.get_children()
        ])

        label = "élément" if count <= 1 else "éléments"
        self.queue_count_label.config(text=f"{count} {label}")

    def select_txt_file(self):
        path = filedialog.askopenfilename(
            title="Choisir un fichier TXT",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )

        if path:
            self.txt_file.set(path)

            if not self.is_downloading:
                self.start_metadata_thread()

    def select_output_dir(self):
        path = filedialog.askdirectory(title="Choisir le dossier de sortie")

        if path:
            self.output_dir.set(path)

    def read_urls(self):
        path = Path(self.txt_file.get())

        if not path.exists():
            raise FileNotFoundError("Fichier TXT introuvable.")

        urls = []

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                urls.append(line)

        return urls

    def format_duration(self, seconds):
        if not seconds:
            return "?"

        seconds = int(seconds)
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{sec:02d}"

        return f"{minutes:02d}:{sec:02d}"

    def add_single_url_thread(self):
        url = self.single_url.get().strip()

        if not url:
            messagebox.showwarning("URL manquante", "Colle d'abord une URL.")
            return

        if self.is_loading_metadata:
            messagebox.showwarning("Chargement en cours", "Attends la fin du chargement actuel.")
            return

        thread = threading.Thread(target=self.add_single_url, args=(url,), daemon=True)
        thread.start()

    def add_single_url(self, url):
        self.is_loading_metadata = True
        self.root.after(0, lambda: self.load_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.start_button.config(state=tk.DISABLED))

        try:
            self.log(f"Ajout de l'URL à la file : {url}")

            ydl_opts = {
                "quiet": True,
                "ignoreerrors": True,
                "noplaylist": not self.allow_playlist.get(),
                "extract_flat": False,
                "logger": YTDLPLogger(self),
            }

            ffmpeg_location = self.ffmpeg_dir.get().strip()
            if ffmpeg_location:
                ydl_opts["ffmpeg_location"] = ffmpeg_location

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    self.add_failed_item(url, "Métadonnées introuvables")
                    return

                if "entries" in info and info["entries"]:
                    added = 0

                    for entry in info["entries"]:
                        if entry:
                            self.add_queue_item(entry)
                            added += 1

                    self.log(f"{added} élément(s) ajouté(s) depuis la playlist.")
                else:
                    self.add_queue_item(info)
                    self.log("Vidéo ajoutée à la file.")

            self.root.after(0, lambda: self.single_url.set(""))

        except Exception as error:
            self.add_failed_item(url, str(error))
            self.log(f"Erreur lors de l'ajout : {error}")

        finally:
            self.is_loading_metadata = False
            self.root.after(0, lambda: self.load_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_queue_count)

    def start_metadata_thread(self):
        if self.is_loading_metadata:
            messagebox.showwarning("Chargement en cours", "La file est déjà en cours de chargement.")
            return

        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Impossible de recharger la file pendant le téléchargement."
            )
            return

        if not self.txt_file.get():
            messagebox.showwarning("Fichier manquant", "Choisis d'abord un fichier TXT.")
            return

        thread = threading.Thread(target=self.load_metadata, daemon=True)
        thread.start()

    def load_metadata(self):
        self.is_loading_metadata = True
        self.root.after(0, lambda: self.load_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.start_button.config(state=tk.DISABLED))

        try:
            urls = self.read_urls()

            if not urls:
                messagebox.showwarning("Aucune URL", "Le fichier TXT ne contient aucune URL.")
                return

            self.queue.clear()
            self.cancelled_ids.clear()
            self.cancel_all = False
            self.root.after(0, self.clear_tree)

            self.log(f"Chargement du fichier TXT : {len(urls)} URL trouvée(s).")

            ydl_opts = {
                "quiet": True,
                "ignoreerrors": True,
                "noplaylist": not self.allow_playlist.get(),
                "extract_flat": False,
                "logger": YTDLPLogger(self),
            }

            ffmpeg_location = self.ffmpeg_dir.get().strip()
            if ffmpeg_location:
                ydl_opts["ffmpeg_location"] = ffmpeg_location

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for position, url in enumerate(urls, start=1):
                    self.log(f"Analyse {position}/{len(urls)} : {url}")

                    try:
                        info = ydl.extract_info(url, download=False)

                        if not info:
                            self.add_failed_item(url, "Métadonnées introuvables")
                            continue

                        if "entries" in info and info["entries"]:
                            for entry in info["entries"]:
                                if entry:
                                    self.add_queue_item(entry)
                        else:
                            self.add_queue_item(info)

                    except Exception as error:
                        self.add_failed_item(url, str(error))

            self.log("File chargée depuis le fichier TXT.")

        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            self.log(f"Erreur : {error}")

        finally:
            self.is_loading_metadata = False
            self.root.after(0, lambda: self.load_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_queue_count)

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.thumbnail_label.config(text="Aucune miniature", image="")
        self.selected_info.config(text="")
        self.thumbnail_image = None
        self.update_queue_count()

    def add_failed_item(self, url, reason):
        item_id = f"failed_{len(self.queue)}"

        item = {
            "id": item_id,
            "url": url,
            "title": url,
            "duration": "?",
            "thumbnail": None,
            "status": "Erreur",
            "progress": "0%",
            "skip": True,
            "reason": reason,
        }

        self.queue.append(item)

        def insert():
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(url, "?", "Erreur", "0%")
            )
            self.update_queue_count()

        self.root.after(0, insert)

    def add_queue_item(self, info):
        video_id = info.get("id") or f"video_{len(self.queue)}"
        item_id = f"item_{len(self.queue)}_{video_id}"

        title = info.get("title") or "Sans titre"
        duration = self.format_duration(info.get("duration"))
        thumbnail = info.get("thumbnail")
        webpage_url = (
            info.get("webpage_url")
            or info.get("original_url")
            or info.get("url")
        )

        item = {
            "id": item_id,
            "url": webpage_url,
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "status": "En attente",
            "progress": "0%",
            "skip": False,
        }

        self.queue.append(item)

        def insert():
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(title, duration, "En attente", "0%")
            )
            self.update_queue_count()

        self.root.after(0, insert)

    def update_item(self, item_id, status=None, progress=None):
        def update():
            if item_id not in self.tree.get_children():
                return

            values = list(self.tree.item(item_id, "values"))

            if status is not None:
                values[2] = status

            if progress is not None:
                values[3] = progress

            self.tree.item(item_id, values=values)

            for item in self.queue:
                if item["id"] == item_id:
                    if status is not None:
                        item["status"] = status
                    if progress is not None:
                        item["progress"] = progress
                    break

        self.root.after(0, update)

    def start_download_thread(self):
        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Un téléchargement est déjà en cours."
            )
            return

        downloadable = [
            item for item in self.queue
            if item["id"] in self.tree.get_children()
            and not item.get("skip")
            and item.get("status") in ["En attente", "Erreur", "Annulé"]
        ]

        if not downloadable:
            messagebox.showwarning(
                "Aucun téléchargement disponible",
                "La file ne contient aucune vidéo en attente."
            )
            return

        try:
            self.get_ffmpeg_location()
        except Exception as error:
            messagebox.showerror("FFmpeg requis", str(error))
            return

        thread = threading.Thread(target=self.download_queue, daemon=True)
        thread.start()

    def download_queue(self):
        self.is_downloading = True
        self.cancel_all = False
        self.pause_event.set()

        self.root.after(0, lambda: self.start_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.load_button.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.pause_button.config(text="Mettre en pause"))

        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            ffmpeg_location = self.get_ffmpeg_location()
            self.log(f"FFmpeg utilisé : {ffmpeg_location}")
            self.log("Démarrage du téléchargement MP3.")

            for index, item in enumerate(list(self.queue)):
                if item["id"] not in self.tree.get_children():
                    continue

                if self.cancel_all:
                    self.log("Téléchargement global annulé.")
                    break

                if item.get("skip"):
                    continue

                if item.get("status") == "Terminé":
                    continue

                item_id = item["id"]

                if item_id in self.cancelled_ids:
                    self.update_item(item_id, status="Annulé", progress="0%")
                    continue

                self.current_index = index
                self.update_item(item_id, status="Téléchargement", progress="0%")
                self.log(f"Téléchargement MP3 : {item['title']}")

                try:
                    self.download_one(item, output_path, ffmpeg_location)

                    if item_id not in self.cancelled_ids:
                        self.update_item(item_id, status="Terminé", progress="100%")
                        self.log(f"Terminé : {item['title']}")

                except Exception as error:
                    if item_id in self.cancelled_ids or self.cancel_all:
                        self.update_item(item_id, status="Annulé")
                        self.log(f"Annulé : {item['title']}")
                    else:
                        self.update_item(item_id, status="Erreur")
                        self.log(f"Erreur sur {item['title']} : {error}")

            self.log("Traitement de la file terminé.")

        finally:
            self.is_downloading = False
            self.current_index = None
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.load_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.pause_button.config(text="Mettre en pause"))

    def build_postprocessors(self):
        postprocessors = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": self.quality.get(),
            }
        ]

        if self.add_metadata.get():
            postprocessors.append({"key": "FFmpegMetadata"})

        if self.embed_cover.get():
            postprocessors.append({
                "key": "EmbedThumbnail",
                "already_have_thumbnail": False,
            })

        return postprocessors

    def download_one(self, item, output_path, ffmpeg_location):
        item_id = item["id"]

        def progress_hook(data):
            while not self.pause_event.is_set():
                self.update_item(item_id, status="En pause")
                threading.Event().wait(0.2)

            if item_id in self.cancelled_ids or self.cancel_all:
                raise Exception("Téléchargement annulé")

            status = data.get("status")

            if status == "downloading":
                percent = data.get("_percent_str", "0%").strip()
                self.update_item(item_id, status="Téléchargement", progress=percent)

            elif status == "finished":
                self.update_item(item_id, status="Conversion MP3", progress="100%")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path / "%(title)s.%(ext)s"),
            "ignoreerrors": False,
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "keepvideo": not self.delete_temp_files.get(),
            "ffmpeg_location": ffmpeg_location,
            "logger": YTDLPLogger(self),
            "progress_hooks": [progress_hook],
            "postprocessors": self.build_postprocessors(),
        }

        if self.embed_cover.get():
            ydl_opts["writethumbnail"] = True

        if self.add_metadata.get():
            ydl_opts["addmetadata"] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([item["url"]])

    def toggle_pause(self):
        if not self.is_downloading:
            return

        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Reprendre le téléchargement")
            self.log("Pause demandée.")
        else:
            self.pause_event.set()
            self.pause_button.config(text="Mettre en pause")
            self.log("Reprise du téléchargement.")

    def cancel_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Aucune sélection",
                "Sélectionne une vidéo à annuler."
            )
            return

        for item_id in selected:
            self.cancelled_ids.add(item_id)

            current_item = None

            if self.current_index is not None and 0 <= self.current_index < len(self.queue):
                current_item = self.queue[self.current_index]

            if current_item and current_item["id"] == item_id:
                self.update_item(item_id, status="Annulé")
                continue

            if item_id in self.tree.get_children():
                self.tree.delete(item_id)

            self.queue = [item for item in self.queue if item["id"] != item_id]

        self.update_queue_count()
        self.log("Vidéo(s) sélectionnée(s) annulée(s)/retirée(s).")

    def cancel_everything(self):
        self.cancel_all = True

        for item in self.queue:
            item_id = item["id"]
            self.cancelled_ids.add(item_id)

            if item_id in self.tree.get_children():
                self.update_item(item_id, status="Annulé")

        self.pause_event.set()
        self.pause_button.config(text="Mettre en pause")
        self.log("Annulation globale demandée.")

    def open_selected_video(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Aucune sélection",
                "Sélectionne une vidéo à ouvrir."
            )
            return

        item_id = selected[0]
        item = next((x for x in self.queue if x["id"] == item_id), None)

        if not item:
            messagebox.showerror("Erreur", "Vidéo introuvable dans la file.")
            return

        url = item.get("url")

        if not url:
            messagebox.showerror("Erreur", "Aucun lien disponible pour cette vidéo.")
            return

        webbrowser.open(url)
        self.log(f"Ouverture vidéo : {url}")

    def remove_cancelled_items(self):
        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Attends la fin avant de retirer les vidéos annulées."
            )
            return

        removed = self.remove_items_by_status(["Annulé"])
        self.log(f"{removed} vidéo(s) annulée(s) retirée(s) de la liste.")

    def remove_finished_items(self):
        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Attends la fin avant de retirer les vidéos terminées."
            )
            return

        removed = self.remove_items_by_status(["Terminé"])
        self.log(f"{removed} vidéo(s) terminée(s) retirée(s) de la liste.")

    def remove_items_by_status(self, statuses):
        removed = 0
        new_queue = []

        for item in self.queue:
            item_id = item["id"]

            if item_id in self.tree.get_children():
                values = self.tree.item(item_id, "values")
                status = values[2] if values else item.get("status")
            else:
                status = item.get("status")

            if status in statuses:
                if item_id in self.tree.get_children():
                    self.tree.delete(item_id)

                self.cancelled_ids.discard(item_id)
                removed += 1
            else:
                new_queue.append(item)

        self.queue = new_queue
        self.update_queue_count()
        return removed

    def retry_failed_items(self):
        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Attends la fin du téléchargement avant de réessayer."
            )
            return

        count = 0

        for item in self.queue:
            item_id = item["id"]

            if item_id not in self.tree.get_children():
                continue

            values = list(self.tree.item(item_id, "values"))
            status = values[2]

            if status in ["Erreur", "Annulé"]:
                values[2] = "En attente"
                values[3] = "0%"
                self.tree.item(item_id, values=values)

                item["skip"] = False
                item["status"] = "En attente"
                item["progress"] = "0%"

                self.cancelled_ids.discard(item_id)
                count += 1

        self.cancel_all = False
        self.pause_event.set()
        self.pause_button.config(text="Mettre en pause")

        self.log(f"{count} vidéo(s) remise(s) en attente.")

    def clear_queue(self):
        if self.is_downloading:
            messagebox.showwarning(
                "Téléchargement en cours",
                "Impossible de vider la file pendant un téléchargement."
            )
            return

        confirm = messagebox.askyesno(
            "Vider la file",
            "Supprimer toute la file d'attente ?"
        )

        if not confirm:
            return

        self.queue.clear()
        self.cancelled_ids.clear()
        self.cancel_all = False
        self.clear_tree()
        self.log("File d'attente vidée.")

    def on_select_video(self, event=None):
        selected = self.tree.selection()

        if not selected:
            return

        item_id = selected[0]
        item = next((x for x in self.queue if x["id"] == item_id), None)

        if not item:
            return

        self.selected_info.config(
            text=(
                f"Titre : {item['title']}\n"
                f"Durée : {item['duration']}\n"
                f"URL : {item['url']}"
            )
        )

        self.load_thumbnail(item.get("thumbnail"))

    def load_thumbnail(self, thumbnail_url):
        if not thumbnail_url:
            self.thumbnail_label.config(text="Aucune miniature", image="")
            self.thumbnail_image = None
            return

        def worker():
            try:
                with urllib.request.urlopen(thumbnail_url, timeout=10) as response:
                    data = response.read()

                image = Image.open(io.BytesIO(data))
                image.thumbnail((350, 200))

                photo = ImageTk.PhotoImage(image)

                def update():
                    self.thumbnail_image = photo
                    self.thumbnail_label.config(image=photo, text="")

                self.root.after(0, update)

            except Exception:
                self.root.after(
                    0,
                    lambda: self.thumbnail_label.config(
                        text="Miniature indisponible",
                        image=""
                    )
                )

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    MP3QueueDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()