import customtkinter as ctk
from tkinter import filedialog


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Application de Téléchargement des CFE")
        self.geometry("800x600")  # Taille initiale de la fenêtre
        self.state('zoomed')  # Ouvrir en mode maximisé

        # Initialisation de l'interface
        self.initUI()

    def initUI(self):
        # Étendre les colonnes et lignes pour s'adapter dynamiquement
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        # self.grid_rowconfigure(3, weight=2)

        # # DEBUG: Visualiser les grilles avec des cadres colorés
        # for row in range(0, 3):  # Nombre de lignes dans la grille
        #     print(row)
        #     for col in range(1):  # Nombre de colonnes dans la grille
        #         debug_frame = ctk.CTkFrame(self, fg_color="lightgray", corner_radius=0)
        #         debug_frame.grid(row=row, column=col, pady=1, padx=1, sticky="nsew")

        # Section Titre (transparent)
        self.frame_titre = ctk.CTkFrame(self, fg_color="red")

        self.frame_titre.grid(row=0, column=0, padx=10, pady=20, sticky="ew")
        # (Label) Texte du titre
        self.label_titre = ctk.CTkLabel(
            self.frame_titre,
            text="Bienvenue sur l'application de téléchargement des CFE",
            font=("Arial", 24, "bold")
        )
        self.label_titre.pack(expand=True)

        texte = ("Guide:"
                 "\n\n    1. Exportez la liste des SIREN depuis votre logiciel comptable, il devra"
                 " être au format Siren;Nom;Code Dossier et à l'extension .txt."
                 "\n\n    2. Renseignez vos identifiants professionels Impots.gouv.\n\n"
                 "    3. Sélectionnez le fichier nécessaire.\n\n"
                 "    4. Cliquez sur démarrer pour lancer l'application.")
        # Section Guide
        self.frame_guide = ctk.CTkFrame(
            self, corner_radius=10, border_width=2, border_color="black")
        self.frame_guide.grid(row=1, column=0, padx=20, sticky="ew")
        self.label_guide = ctk.CTkLabel(
            self.frame_guide,
            anchor="w",
            text=texte,
            justify="left",
            font=("Arial", 14)
        )
        self.label_guide.pack(padx=20, pady=20, expand=True, anchor="w")

        # Section Champs
        self.frame_champs = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=2,
            border_color="black"
        )
        self.frame_champs.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.frame_champs.grid_columnconfigure(1, weight=1)  # Étendre les champs horizontalement

        # Champ Identifiant
        self.label_identifiant = ctk.CTkLabel(
            self.frame_champs, text="Identifiant :", font=("Arial", 14))
        self.label_identifiant.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.entry_identifiant = ctk.CTkEntry(
            self.frame_champs, placeholder_text="Entrez votre identifiant")
        self.entry_identifiant.grid(row=0, column=1, padx=20, pady=10, sticky="ew")

        # Champ Mot de passe
        self.label_password = ctk.CTkLabel(
            self.frame_champs, text="Mot de passe :", font=("Arial", 14))
        self.label_password.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.entry_password = ctk.CTkEntry(
            self.frame_champs, placeholder_text="Entrez votre mot de passe", show="*")
        self.entry_password.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        # Bouton Sélection de fichier
        self.label_fichier = ctk.CTkLabel(self.frame_champs, text="Fichier :", font=("Arial", 14))
        self.label_fichier.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.entry_file = ctk.CTkEntry(self.frame_champs, state="disabled",
                                       placeholder_text="Aucun fichier sélectionné")
        self.entry_file.grid(row=2, column=1, padx=20, pady=10, sticky="ew")
        self.button_fichier = ctk.CTkButton(
            self.frame_champs, text="Parcourir", command=self.select_file)
        self.button_fichier.grid(row=2, column=2, padx=10, pady=10, sticky="w")

    def select_file(self):
        # Méthode pour sélectionner un fichier
        file_path = filedialog.askopenfilename()
        if file_path:
            self.entry_file.configure(state="normal")
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, file_path)
            self.entry_file.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
