"""Programme de recuperation des CFE."""
import glob
import logging
import os
import shutil
import sys
from datetime import datetime
from itertools import islice
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import (TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Program:
    """
    Class that contains methods to connect to the CFE website, process the CFE information, and
    rename the downloaded PDF file.

    Attributes:
        script_path (str): The path to the script.
        url (str): The URL of the CFE website.
        driver (webdriver): A Selenium WebDriver object for Firefox with specific options.
        file_path (str): The path to the file containing the SIREN numbers, company names, and
            dossier numbers.
        credentials_file (str): The path to the file containing the login credentials.
        data (list): A list of tuples containing the SIREN numbers, company names, and dossier
        numbers.

    Methods:
        __init__ (self): Initializes the Program instance.
        __del__ (self): Closes the WebDriver object.
        initialize_driver (self): Initializes and returns a Selenium WebDriver object for Firefox
        withspecific options.
        read_creds (self): Reads the login credentials from the file and returns them as a list.
        read_data (self): Reads data from a file and returns a list of tuples containing the SIREN
        numbers, company names, and dossier numbers.
        connexion_site (self): Connects to the website using the provided
        credentials.
        process_avis_imposition_link (self, code, name): Processes a single link for the avis
        d'imposition.
        open_avis_cfe (self, siren): Opens the Avis CFE page and enters the SIREN number to access
        the CFE information.
        traiter_siren (self, siren, name, code): Processes a SIREN, name, and code by opening the
        avis de CFE and processing the avis imposition link.
    """

    def __init__(self):
        self.script_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.url = "https://cfspro-idp.impots.gouv.fr/oauth2/authorize?[...]"
        self.file_path = os.path.join(self.script_path, "SIREN.TXT")
        self.credentials_file = os.path.join(self.script_path, "identifiants.txt")
        self.donnees = self.lire_donnees()
        self.creds = self.lire_identifiants()
        print(self.creds)
        self.driver = self.initialiser_driver()

    def __del__(self):
        self.driver.quit()

    def initialiser_driver(self):
        """
        Initialise et retourne un objet Selenium WebDriver pour Firefox avec des options
        spécifiques.

        Retourne :
            webdriver.Firefox: Un objet WebDriver pour Firefox avec les options suivantes :
                - Désactiver les extensions
                - Désactiver les notifications
                - Désactiver le sandbox
                - Désactiver le dev-shm-usage
                - Définir le dossier de téléchargement sur le répertoire actuel
                - Cacher le gestionnaire de téléchargement au démarrage
                - Ne jamais demander de sauvegarder les fichiers avec le type MIME application/pdf
                - Désactiver PDF.js
        """
        # Définir le répertoire de téléchargement dans le dossier "Documents"
        dossier_actuel = os.path.join(self.script_path, "Documents")

        # Initialisation des options Firefox
        options_firefox = FirefoxOptions()
        options_firefox.add_argument("--disable-extensions")
        options_firefox.add_argument("--disable-notifications")
        options_firefox.add_argument("--no-sandbox")
        options_firefox.add_argument("--disable-dev-shm-usage")

        # Préférences de téléchargement
        options_firefox.set_preference("browser.download.folderList", 2)
        options_firefox.set_preference("browser.download.manager.showWhenStarting", False)
        options_firefox.set_preference("browser.download.dir", dossier_actuel)
        options_firefox.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        options_firefox.set_preference("pdfjs.disabled", True)

        # Retourner le driver Firefox configuré
        return webdriver.Firefox(options=options_firefox)

    def lire_identifiants(self):
        """
        Lit les identifiants depuis le fichier et les retourne sous forme de liste.

        Retourne :
            list: Une liste contenant les deux premières lignes du fichier `identifiants_file`,
            avec les espaces blancs en début et fin de ligne supprimés.
        """
        with open(self.credentials_file, "r", encoding="utf-8") as fichier:
            # Utilisation de islice pour limiter à 2 lignes.
            return [ligne.strip() for ligne in islice(fichier, 2)]

    def lire_donnees(self):
        """
        Lit les données depuis un fichier et retourne une liste de tuples contenant le SIREN,
        le nom de l'entreprise et le numéro de dossier.

        Retourne :
            list: Une liste de tuples, chaque tuple contenant le SIREN (str),
            le nom de l'entreprise (str) et le numéro de dossier (str).
        """
        with open(self.file_path, "r", encoding="utf-8") as fichier:
            # Ignorer la première ligne (en-tête)
            next(fichier)
            # Utilisation d'une liste en compréhension pour extraire les données
            return [
                tuple(ligne.strip().split(";", 3)[:3])
                for ligne in fichier if len(ligne.strip().split(";", 3)) == 3
            ]

    def connexion_site(self):
        """
        Connects to the website using the provided credentials.

        This function navigates to the website specified by `self.url` and checks if the user is
        already logged in. If the user is already logged in, it prints "Déjà connecté."
        and returns. If the user is not logged in, it proceeds with the login process.

        The login process involves finding the username and password input fields on the website,
        entering the credentials from `self.creds`, and clicking the login button.

        Parameters:
            self (Program): The Program instance.
        """
        print("Ouverture de la page...")
        self.driver.get(self.url)

        # Vérification si déjà connecté
        try:
            WebDriverWait(self.driver, 0.5).until(
                EC.presence_of_element_located((By.ID, "identifiant_après_connexion")))
            print("Déjà connecté.")
            return
        except TimeoutException:
            print("Pas encore connecté. Procédure de connexion en cours.")

        # Connexion
        self.driver.find_element(By.ID, "ident").send_keys(self.creds[0])
        self.driver.find_element(By.NAME, "password").send_keys(self.creds[1])
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Connexion')]").click()

    def traiter_siren(self, siren, nom_entreprise, code_dossier):
        """
        Traite un SIREN, un nom d'entreprise, et un code de dossier en ouvrant l'avis de CFE
        et en accédant au lien d'avis d'imposition associé.

        Args:
            siren (str): Numéro SIREN de l'entreprise.
            nom_entreprise (str): Nom de l'entreprise.
            code_dossier (str): Code de dossier associé.
        """
        if self.ouvrir_avis_cfe(siren):
            self.traiter_lien_avis_imposition(code_dossier, nom_entreprise, siren)

    def ouvrir_avis_cfe(self, siren):
        """
        Ouvre la page des Avis CFE et entre le numéro SIREN pour accéder aux informations CFE.

        Args:
            siren (str): Le numéro SIREN pour accéder aux informations CFE.

        Returns:
            bool: True si l'accès aux informations CFE est réussi, False sinon.
        """
        # Essayer d'accéder à la page d'accueil
        try:
            self.driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")
        except TimeoutException:
            print("Timeout lors de l'accès à la page d'accueil.")
            return self.ouvrir_avis_cfe(siren)

        # Attendre et cliquer sur "Avis CFE"
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Avis CFE')]"))
        ).click()

        # Entrer le SIREN
        for i, digit in enumerate(siren):
            self.driver.find_element(By.ID, f"siren{i}").send_keys(digit)

        # Cliquer sur le bouton consulter
        self.driver.find_element(By.NAME, "button.submitValider").click()

        # Vérifier si une nouvelle fenêtre s'ouvre
        if len(self.driver.window_handles) < 2:
            print("SIREN non accessible.")
            logging.info('SIREN - %s - INACCESSIBLE', siren)
            return False

        # Passer à la fenêtre qui s'est ouverte
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # Vérifier la présence de la page d'accueil
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Accueil du compte fiscal des professionnels')]")
                )
            )
        except TimeoutException:
            return self.ouvrir_avis_cfe(siren)

        # Essayer de cliquer sur le bouton pour accéder aux avis de CFE
        try:
            WebDriverWait(self.driver, 0.5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='custom_bouton_cfe']"))
            ).click()
        except TimeoutException:
            print("Pas de CFE, passage au SIREN suivant.")
            logging.info('PAS DE CFE - SIREN - %s', siren)
            return False
        return True

    def traiter_lien_avis_imposition(self, code, nom, siren):
        """
        Traite un lien pour un avis d'imposition en renvoyant un PDF renommé.

        Args:
            code (str): Code associé à l'avis d'imposition.
            nom (str): Nom de l'entreprise.
            siren (str): Numéro SIREN de l'entreprise.
        """
        print("Arrivée sur la page des avis d'imposition.")

        try:
            lignes = WebDriverWait(self.driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr"))
            )
        except TimeoutException:
            print("Aucune ligne de document trouvée.")
            return

        for ligne in lignes:
            cellules = ligne.find_elements(By.TAG_NAME, "td")
            if cellules:
                cellules[7].click()
                print("Clic sur le lien d'avis d'imposition.")
                siret = f"{siren}{cellules[4].text.strip()}"
                self.renommer_pdf_telecharge(code, nom, self.script_path, siret)
                sleep(1)

    def renommer_pdf_telecharge(self, code, nom_entreprise, dossier_telechargement, siret):
        """
        Renomme et déplace un fichier PDF téléchargé en ajoutant des informations pertinentes au
        nom de fichier.

        Args:
            code (str): Code associé au fichier PDF.
            nom_entreprise (str): Nom de l'entreprise.
            dossier_telechargement (str): Répertoire où le fichier PDF est téléchargé.
            siret (str): Numéro SIRET de l'entreprise.
        """
        # Création du nom du fichier avec l'année actuelle
        annee = datetime.now().year
        nouveau_nom = f"{code}_{nom_entreprise.replace(' ', '_')}_{
            siret.replace(' ', '')}_CFE_{annee}.pdf"
        chemin_source = os.path.join(dossier_telechargement, "Documents", "AvisCfe*.pdf")

        # Recherche du fichier PDF dans le répertoire spécifié
        fichiers = glob.glob(chemin_source)
        if len(fichiers) == 0:
            print("Fichier PDF correspondant introuvable.")
            return

        fichier_original = fichiers[0]
        chemin_nouveau = os.path.join(dossier_telechargement, nouveau_nom)
        dossier_destination = os.path.join(self.script_path, "Documents")

        # Renommage et déplacement du fichier
        os.rename(fichier_original, chemin_nouveau)
        os.makedirs(dossier_destination, exist_ok=True)
        shutil.move(chemin_nouveau, os.path.join(dossier_destination, nouveau_nom))
        print(f"Le fichier renommé a été déplacé vers : {
              os.path.join(dossier_destination, nouveau_nom)}")

    def fermer_fenetres(self):
        """
        Ferme toutes les fenêtres du navigateur, sauf la principale.
        """

        if len(self.driver.window_handles) > 1:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])


def afficher_aide():
    """
    Affiche le message d'aide pour le script.
    """

    aide_message = """
        Usage : python recup_cfe.py [acomptes|imposition]

        Ce script récupère les avis d'imposition de la CFE pour un ensemble de SIREN fournis.

        Entrées :
        - Fichier 'SIREN.TXT' contenant les SIREN, noms d'entreprise et codes, au format :
            Siren;Nom;Code Dossier

        - Fichier 'identifiants.txt' avec les identifiants et le mot de passe, au format :
            identifiant
            mot_de_passe

        Argument :
        - 'acomptes' ou 'imposition' : spécifie le type de document à récupérer.

        Exemples d'utilisation :
            python recup_cfe.py acomptes
            python recup_cfe.py imposition
    """
    print(aide_message)


def main():
    """
    Fonction principale qui initialise le journal de logs, crée une instance de la classe Program,
    et traite chaque SIREN, nom, et code. Pour chaque entrée, elle affiche le compteur et les
    détails. Elle connecte ensuite l'application au site web avec les identifiants et lance
    le traitement des données.
    """

    # Validation des arguments
    argument = sys.argv[1] if len(sys.argv) == 2 else None
    if argument not in ["acomptes", "imposition"] and argument not in ["-h", "--help"]:
        afficher_aide()
        return

    try:
        # Initialisation du logging et démarrage de l'application
        print("Démarrage du script...")
        logging.basicConfig(filename='log.txt', level=logging.INFO,
                            format='%(asctime)s - %(message)s')

        app = Program()
        print("Initialisation terminée.")

        # Traitement de chaque SIREN
        for compteur, (siren, nom, code) in enumerate(app.donnees, start=1):
            print(f"\nCompteur: {compteur} | Code: {code} | Nom: {nom} | SIREN: {siren}")
            app.connexion_site()
            app.traiter_siren(siren, nom, code)
            app.fermer_fenetres()

    except Exception as e:
        print(f"Erreur : {e}")
        logging.exception("Erreur lors de l'exécution : %s", e)

    print("Script terminé !")


if __name__ == "__main__":
    main()
