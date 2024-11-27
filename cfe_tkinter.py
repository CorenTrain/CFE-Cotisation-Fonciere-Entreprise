"""Module pour l'interface graphique de l'application de téléchargement des CFE."""
from tkinter import filedialog

import customtkinter as ctk


class WindowApp(ctk.CTk):
    """Classe pour l'application fenêtrée"""

    def __init__(self):
        super().__init__()
        self.web_data: dict = {}
        self.objects: dict = {}
        self.eta = "En attente de lancement"
        self.var_activite = ctk.BooleanVar(value=False)

        # Initialisation de l'interface
        self.init_ui()

        self.dossiers_total = 0
        self.title("Application de Téléchargement des CFE")
        self.stopped = False
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.protocol("WM_DELETE_WINDOW", self.quitter)

    @property
    def etat_app(self):
        """Propriété pour l'état de l'application"""
        return self.eta

    @etat_app.setter
    def etat_app(self, value: str):
        self.eta = value
        self.objects["label_etat"].configure(text=f"État de l'application : {self.eta}")

    @property
    def dossiers_total(self):
        """Propriété pour le nombre total de dossiers à traiter"""
        return self._dossiers_total

    @dossiers_total.setter
    def dossiers_total(self, value: int):
        self._dossiers_total = value
        self.objects["barre_de_progression"].configure(
            determinate_speed=(1 / self.dossiers_total if self.dossiers_total != 0 else 1) * 50
        )

    def init_ui(self):
        """Initialise l'interface graphique avec une structure claire et modulaire."""
        self._configure_main_grid()
        self._create_title_section()
        self._create_guide_section()
        self._create_config_section()
        self._create_progress_bar_section()
        self._create_buttons_section()

    def _configure_main_grid(self):
        """Configure la grille principale pour une mise en page dynamique."""
        self.grid_columnconfigure(0, weight=1)
        for i in range(5):  # Pour chaque ligne nécessaire
            self.grid_rowconfigure(i, weight=0)

    def _create_title_section(self):
        """Crée la section du titre."""
        frame_titre = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        frame_titre.grid(row=0, column=0, padx=10, pady=20, sticky="ew")
        ctk.CTkLabel(
            frame_titre,
            text="Bienvenue sur l'application de téléchargement des CFE",
            font=("Arial", 24, "bold")
        ).pack(expand=True)

    def _create_guide_section(self):
        """Crée la section du guide d'utilisation."""
        texte = (
            "1. Exportez la liste des SIREN depuis votre logiciel comptable. Les lignes du fichier"
            " devront être au format \'Siren;Nom;Code\' Dossier et à l'extension \'.txt\'.\n\n"
            "2. Renseignez vos identifiants professionels Impots.gouv.\n\n"
            "3. Sélectionnez le fichier de SIREN.\n\n"
            "4. Sélectionnez le répertoire de destination où vous souhaitez que le script "
            "télécharge vos fichiers.\n\n"
            "5. Cliquez sur démarrer pour lancer l'application.\n\n"
            "6. Remplissez le CAPTCHA (Code de sécurité sur la page d'accueil impots.gouv).\n\n"
            "7. C'est parti ! Le script télécharge tous vos fichiers CFE !"
        )
        frame_guide = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        frame_guide.grid(row=1, column=0, padx=20, sticky="ew")
        frame_guide.bind("<Configure>", self.update_wraplength)
        self.objects["frame_guide"] = frame_guide

        ctk.CTkLabel(
            frame_guide,
            text="Guide d'utilisation :",
            font=("Arial", 18, "bold", "underline"),
            anchor="w"
        ).pack(padx=20, pady=10, fill="x")

        label_guide = ctk.CTkLabel(
            frame_guide,
            text=texte,
            font=("Arial", 14),
            wraplength=600,
            anchor="w",
            justify="left"
        )
        label_guide.pack(padx=(40, 20), pady=(0, 20), fill="x")
        self.objects["label_guide"] = label_guide

    def _create_config_section(self):
        """Crée la section des champs de configuration."""
        frame_champs = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        frame_champs.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        frame_champs.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            frame_champs,
            text="Configurations :",
            font=("Arial", 16, "bold", "underline"),
            anchor="w"
        ).grid(padx=20, pady=(10, 0))

        # Ajout des champs avec configuration centralisée
        fields = [
            {"label": "Identifiant :", "object_name": "entry_identifiant",
                "row": 1, "placeholder": "Entrez votre identifiant"},
            {"label": "Mot de passe :", "object_name": "entry_password", "row": 2,
                "placeholder": "Entrez votre mot de passe", "is_password": True},
            {"label": "Fichier de SIREN :", "object_name": "entry_file", "row": 3,
                "placeholder": "Aucun fichier sélectionné", "is_browse": True},
            {"label": "Destination :", "object_name": "entry_destination", "row": 4,
                "placeholder": "Aucun destination sélectionnée", "is_browse": True,
                "is_directory": True},
        ]

        for field in fields:
            self._add_config_field(frame_champs, field)

    def _add_config_field(self, frame, config):
        """
        Ajoute un champ de configuration avec label,
        entry et éventuellement un bouton Parcourir.
        """
        # Extraction des paramètres avec des valeurs par défaut
        label = config["label"]
        object_name = config["object_name"]
        row = config["row"]
        placeholder = config.get("placeholder", "")
        is_password = config.get("is_password", False)
        is_browse = config.get("is_browse", False)
        is_directory = config.get("is_directory", False)

        ctk.CTkLabel(frame, text=label, font=("Arial", 14)).grid(
            row=row, column=0, padx=20, pady=10, sticky="w"
        )

        entry = ctk.CTkEntry(
            frame,
            width=300,
            placeholder_text=placeholder,
            show="*" if is_password else None,
            state="disabled" if is_browse else None
        )
        entry.grid(row=row, column=1, padx=20, pady=10, sticky="w")

        # Stocker l'entrée dans self.objects
        self.objects[object_name] = entry

        if is_browse:
            ctk.CTkButton(
                frame,
                text="Parcourir",
                command=lambda: self.select_file(entry, is_directory=is_directory),
                border_width=2,
                border_color="black"
            ).grid(row=row, column=2, padx=10, pady=10, sticky="e")

    def _create_progress_bar_section(self):
        """Crée la section de la barre de progression."""
        frame_progression = ctk.CTkFrame(self, corner_radius=10, border_width=2)
        frame_progression.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        frame_progression.grid_columnconfigure(0, weight=1)

        barre_de_progression = ctk.CTkProgressBar(
            frame_progression, height=20, border_color="gray", border_width=1)
        barre_de_progression.configure(mode="determinate")
        barre_de_progression.set(0)
        barre_de_progression.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.objects["barre_de_progression"] = barre_de_progression

        label_metrique = ctk.CTkLabel(
            frame_progression,
            text="Nombre dossiers: 0 | Traités: 0 | Succès:  0 | Échec: 0 | Restants: 0",
            font=("Arial", 14)
        )
        label_metrique.grid(row=1, column=0, padx=20, pady=(5, 10), sticky="w")
        self.objects["label_metrique"] = label_metrique

    def _create_buttons_section(self):
        """Crée la section des boutons."""
        frame_boutons = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        frame_boutons.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        frame_boutons.grid_columnconfigure((0, 1), weight=1)

        self.objects["label_etat"] = ctk.CTkLabel(
            frame_boutons,
            text=f"État de l'application : {self.eta}",
            font=("Arial", 14)
        )
        self.objects["label_etat"].grid(row=0, column=0, padx=20, pady=10, sticky="w")

        bouton_demarrer = ctk.CTkButton(
            frame_boutons, text="Démarrer", font=("Arial", 14),
            border_width=2, border_color="black", command=self.demarrer
        )
        bouton_demarrer.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.objects["bouton_demarrer"] = bouton_demarrer
        ctk.CTkButton(
            frame_boutons, text="Quitter", font=("Arial", 14),
            border_width=2, border_color="black", command=self.quitter
        ).grid(row=1, column=1, padx=20, pady=10, sticky="w")

    def select_file(self, entree: ctk.CTkEntry, is_directory: bool = False):
        """Méthode pour sélectionner un fichier et mettre à jour le champ d'entrée"""
        # Méthode pour sélectionner un fichier
        if is_directory:
            file_path = filedialog.askdirectory()
        else:
            file_path = filedialog.askopenfilename()

        if file_path:
            entree.configure(state="normal")
            entree.delete(0, "end")
            entree.insert(0, file_path)
            entree.configure(state="disabled")

    def update_wraplength(self, event):
        """Méthode pour mettre à jour la longueur de l'enveloppe du texte"""
        self.objects["label_guide"].configure(
            wraplength=self.objects["frame_guide"].winfo_width() - 300)

    def update_progression(self, progression: dict, initialisation: bool = False):
        """Méthode pour mettre à jour la barre de progression"""
        if initialisation:
            self.dossiers_total = progression["dossiers_total"]
        dossiers_restants = progression["dossiers_restants"]
        dossiers_traites = progression["dossiers_traites"]
        dossiers_succes = progression["dossiers_succes"]
        dossiers_echec = progression["dossiers_echec"]
        texte_metrique = (
            f"Nombre dossiers: {self.dossiers_total} "
            f"| Traités: {dossiers_traites} | Succès:  {dossiers_succes} | Échec: "
            f"{dossiers_echec} | Restants: {dossiers_restants}"
        )

        if not initialisation:
            self.objects["barre_de_progression"].step()
        self.objects["label_metrique"].configure(text=texte_metrique)

    def demarrer(self):
        """Méthode pour démarrer le téléchargement"""
        self.var_activite.set(True)  # Met à jour la variable pour débloquer wait_variable
        self.objects["bouton_demarrer"].configure(state="disabled")
        self.objects["entry_identifiant"].configure(state="disabled")
        self.objects["entry_password"].configure(state="disabled")

        self.web_data = {
            "identifiant": self.objects["entry_identifiant"].get(),
            "mot_de_passe": self.objects["entry_password"].get(),
            "fichier": self.objects["entry_file"].get(),
            "destination": self.objects["entry_destination"].get().replace("/", "\\"),
        }

    def quitter(self):
        """Handler pour la fermeture."""
        self.stopped = True
        self.var_activite.set(True)
        self.quit()
        self.destroy()
