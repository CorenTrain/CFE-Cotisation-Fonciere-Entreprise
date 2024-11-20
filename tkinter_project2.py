import customtkinter as ctk
from tkinter import filedialog, messagebox


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Formulaire d'authentification")
        # self.geometry("400x250")
        ctk.set_appearance_mode("System")  # Options: "System" (par défaut), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Couleurs disponibles : "blue", "green", "dark-blue"

        # Identifiant
        self.label_username = ctk.CTkLabel(self, text="Identifiant :")
        self.label_username.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.username_entry = ctk.CTkEntry(self, width=250)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        # Mot de passe
        self.label_password = ctk.CTkLabel(self, text="Mot de passe :")
        self.label_password.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.password_entry = ctk.CTkEntry(self, show="*", width=250)
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        # Sélectionner un fichier
        self.label_file = ctk.CTkLabel(self, text="Fichier :")
        self.label_file.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.filepath = ctk.StringVar()
        self.file_entry = ctk.CTkEntry(
            self, textvariable=self.filepath, width=250, state="readonly")
        self.file_entry.grid(row=2, column=1, padx=10, pady=5)
        self.browse_button = ctk.CTkButton(self, text="Parcourir", command=self.select_file)
        self.browse_button.grid(row=2, column=2, padx=10, pady=5)

        # Bouton valider
        self.validate_button = ctk.CTkButton(self, text="Valider", command=self.validate)
        self.validate_button.grid(row=3, column=0, columnspan=3, pady=10)

    def select_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier."""
        file = filedialog.askopenfilename(
            title="Sélectionnez un fichier",
            filetypes=[("Tous les fichiers", "*.*"), ("Fichiers texte", "*.txt")]
        )
        if file:
            self.filepath.set(file)

    def validate(self):
        """Valide les champs et exécute la suite du script."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        file = self.filepath.get()

        if not username or not password or not file:
            messagebox.showerror("Erreur", "Tous les champs sont requis.")
            return

        # Exécuter la suite du script
        messagebox.showinfo("Succès", f"Identifiant : {username}\nFichier : {file}")
        # Ici, tu peux appeler une fonction pour la suite du script


# Lancer l'application
if __name__ == "__main__":
    app = App()
    app.mainloop()
