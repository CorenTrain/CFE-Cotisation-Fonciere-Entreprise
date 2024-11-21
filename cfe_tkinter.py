import pprint
import sys
from tkinter import filedialog

import customtkinter as ctk


class WindowApp(ctk.CTk):
    """Classe pour l'application fenêtrée"""

    def __init__(self):
        super().__init__()
        self.web_data: dict = {}
        self.eta = "En attente de lancement"
        self.var_activite = ctk.BooleanVar(value=False)
        self.texte_metrique = (
            f"Nombre dossiers: {0} "
            f"| Traités: {0} | Succès:  {0} | Échec: {0} | Restants: {0}"
        )

        # Initialisation de l'interface
        self.init_ui()

        self.dossiers_total = 0
        self.dossiers_traites = 0
        self.dossiers_succes = 0
        self.dossiers_echec = 0
        self.dossiers_restants = 0
        self.title("Application de Téléchargement des CFE")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        self.stopped = False  # Drapeau pour signaler l'arrêt
        self.protocol("WM_DELETE_WINDOW", self.quitter)  # Gestion de la fermeture

    @property
    def etat_app(self):
        return self.eta

    @etat_app.setter
    def etat_app(self, value: str):
        self.eta = value
        self.label_etat_app.configure(text=f"État de l'application : {self.eta}")

    @property
    def dossiers_total(self):
        return self._dossiers_total

    @dossiers_total.setter
    def dossiers_total(self, value: int):
        self._dossiers_total = value
        self.barre_de_progression.configure(
            determinate_speed=(1 / self.dossiers_total if self.dossiers_total != 0 else 1) * 50
        )

    def init_ui(self):
        """Méthode pour initialiser l'interface graphique"""
        # Étendre les colonnes et lignes pour s'adapter dynamiquement
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        # Section Titre (transparent)
        self.frame_titre = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.frame_titre.grid(row=0, column=0, padx=10, pady=20, sticky="ew")
        self.label_titre = ctk.CTkLabel(
            self.frame_titre,
            text="Bienvenue sur l'application de téléchargement des CFE",
            font=("Arial", 24, "bold")
        )
        self.label_titre.pack(expand=True)

        # Section Guide
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

        self.frame_guide = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=2
        )
        self.frame_guide.grid(row=1, column=0, padx=20, sticky="ew")
        self.frame_guide.bind("<Configure>", self.update_wraplength)
        self.label_title_guide = ctk.CTkLabel(
            self.frame_guide,
            text="Guide d'utilisation :",
            font=("Arial", 18, "bold", "underline"),
            anchor="w"
        )
        self.label_title_guide.pack(padx=20, pady=10, fill="x", anchor="w")
        self.label_guide = ctk.CTkLabel(
            self.frame_guide,
            anchor="w",
            text=texte,
            justify="left",
            font=("Arial", 14),
            wraplength=600
        )
        self.label_guide.pack(padx=(40, 20), pady=(0, 20), fill="x", anchor="w")

        # Section Champs
        self.frame_champs = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=2,

        )
        self.frame_champs.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.frame_champs.grid_columnconfigure(1, weight=0)  # Étendre les champs horizontalement

        self.label_titre_config = ctk.CTkLabel(
            self.frame_champs,
            text="Configurations :",
            font=("Arial", 16, "bold", "underline"),
            anchor="w"
        )
        self.label_titre_config.grid(padx=20, pady=(10, 0))

        # Champ Identifiant
        self.label_identifiant = ctk.CTkLabel(
            self.frame_champs, text="Identifiant :", font=("Arial", 14))
        self.label_identifiant.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.entry_identifiant = ctk.CTkEntry(
            self.frame_champs, width=300, placeholder_text="Entrez votre identifiant")
        self.entry_identifiant.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        # Champ Mot de passe
        self.label_password = ctk.CTkLabel(
            self.frame_champs, text="Mot de passe :", font=("Arial", 14))
        self.label_password.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.entry_password = ctk.CTkEntry(
            self.frame_champs, width=300, placeholder_text="Entrez votre mot de passe", show="*")
        self.entry_password.grid(row=2, column=1, padx=20, pady=10, sticky="w")

        # Bouton Sélection de fichier
        self.label_fichier = ctk.CTkLabel(self.frame_champs, text="Fichier :", font=("Arial", 14))
        self.label_fichier.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.entry_file = ctk.CTkEntry(self.frame_champs, state="disabled", width=300,
                                       placeholder_text="Aucun fichier sélectionné")
        self.entry_file.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        self.button_fichier = ctk.CTkButton(
            self.frame_champs,
            text="Parcourir",
            command=lambda: self.select_file(self.entry_file),
            border_width=2,
            border_color="black"
        )
        self.button_fichier.grid(row=3, column=2, padx=10, pady=10, sticky="e")

        # Bouton Sélection de destination
        self.label_destination = ctk.CTkLabel(
            self.frame_champs, text="Destination :", font=("Arial", 14)
        )
        self.label_destination.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="w")
        self.entry_destination = ctk.CTkEntry(
            self.frame_champs,
            state="disabled",
            placeholder_text="Aucun destination sélectionné",
            width=300  # Augmentation de la largeur
        )
        self.entry_destination.grid(row=4, column=1, padx=(20, 5), pady=(10, 20), sticky="w")
        self.button_destination = ctk.CTkButton(
            self.frame_champs,
            text="Parcourir",
            command=lambda: self.select_file(self.entry_destination, is_directory=True),
            border_width=2,
            border_color="black"
        )
        self.button_destination.grid(row=4, column=2, padx=(5, 10), pady=(10, 20), sticky="e")

        self.frame_progression = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=2,
        )
        self.frame_progression.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.frame_progression.grid_columnconfigure(0, weight=1)

        # Barre de progression avec étirement dynamique
        self.barre_de_progression = ctk.CTkProgressBar(
            self.frame_progression,
            height=20,
            border_color="gray",
            border_width=1,
        )
        self.barre_de_progression.configure(
            mode="determinate",
        )
        self.barre_de_progression.set(0)

        self.barre_de_progression.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.label_metrique = ctk.CTkLabel(
            self.frame_progression, text=self.texte_metrique, font=("Arial", 14))
        self.label_metrique.grid(row=1, column=0, padx=20, pady=(5, 10), sticky="w")

        self.frame_boutons = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="transparent"
        )
        self.frame_boutons.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.frame_boutons.grid_columnconfigure(0, weight=1)
        self.frame_boutons.grid_columnconfigure(1, weight=1)

        self.label_etat_app = ctk.CTkLabel(
            self.frame_boutons,
            text=f"État de l'application : {self.eta}",
            font=("Arial", 14)
        )
        self.label_etat_app.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.bouton_demarrer = ctk.CTkButton(
            self.frame_boutons, border_width=2,
            border_color="black", text="Démarrer",
            font=("Arial", 14), command=self.demarrer
        )
        self.bouton_demarrer.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        self.bouton_quitter = ctk.CTkButton(
            self.frame_boutons, border_width=2,
            border_color="black", text="Quitter",
            font=("Arial", 14), command=self.quitter
        )
        self.bouton_quitter.grid(row=1, column=1, padx=20, pady=10, sticky="w")

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
        self.label_guide.configure(wraplength=self.frame_guide.winfo_width() - 300)

    def update_progression(self, progression: dict, initialisation: bool = False):
        """Méthode pour mettre à jour la barre de progression"""
        if initialisation:
            self.dossiers_total = progression["dossiers_total"]
            self.dossiers_restants = progression["dossiers_restants"]
        self.dossiers_traites = progression["dossiers_traites"]
        self.dossiers_succes = progression["dossiers_succes"]
        self.dossiers_echec = progression["dossiers_echec"]
        self.dossiers_restants = progression["dossiers_restants"]
        self.texte_metrique = (
            f"Nombre dossiers: {self.dossiers_total} "
            f"| Traités: {self.dossiers_traites} | Succès:  {self.dossiers_succes} | Échec: "
            f"{self.dossiers_echec} | Restants: {self.dossiers_restants}"
        )
        if not initialisation:
            # self.barre_de_progression.set(self.dossiers_traites / self.dossiers_total * 100)
            self.barre_de_progression.step()
        print(f"PROGRESSION {self.barre_de_progression.get()}")
        print(f"settings:\n\t {self.barre_de_progression.cget('determinate_speed')}")
        self.label_metrique.configure(text=self.texte_metrique)

    def demarrer(self):
        """Méthode pour démarrer le téléchargement"""
        print("Bouton cliqué !")
        self.var_activite.set(True)  # Met à jour la variable pour débloquer wait_variable
        self.bouton_demarrer.configure(state="disabled")
        self.web_data = {
            "identifiant": self.entry_identifiant.get(),
            "mot_de_passe": self.entry_password.get(),
            "fichier": self.entry_file.get(),
            "destination": self.entry_destination.get().replace("/", "\\"),
        }
        pprint.pprint(self.web_data)

    def quitter(self):
        """Handler pour la fermeture."""
        self.stopped = True  # Indique que la fenêtre est fermée
        self.var_activite.set(True)  # Débloque le wait_variable
        self.quit()
        self.destroy()
