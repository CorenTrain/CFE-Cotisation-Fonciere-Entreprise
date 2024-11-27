"""Programme de recuperation des CFE."""
import glob
import logging
import os
import re
import shutil
import sys
import threading
import tkinter
from datetime import datetime
from itertools import islice
from time import sleep
from tkinter import messagebox

import time


from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from cfe_tkinter import WindowApp

LIEN_IMPOTS = "https://cfspro.impots.gouv.fr/mire/accueil.do"


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
        self.credentials_file = os.path.join(self.script_path, "identifiants.txt")
        self.donnees: dict = {}
        self.driver = None
        self.avancee: dict = {"dossiers_total": len(self.donnees), "dossiers_traites": 0,
                              "dossiers_succes": 0, "dossiers_echec": 0,
                              "dossiers_restants": len(self.donnees)}
        print("Initialisation terminée.")
        logging.info("Initialisation terminée.")

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def initialiser_driver(self, chemin_dossier: str):
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
        dossier_actuel = chemin_dossier

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
        self.driver = webdriver.Firefox(options=options_firefox)

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

    def lire_donnees(self, chemin: str) -> list:
        """
        Lit les données depuis un fichier et retourne une liste de tuples contenant le SIREN,
        le nom de l'entreprise et le numéro de dossier.

        Retourne :
            list: Une liste de tuples, chaque tuple contenant le SIREN (str),
            le nom de l'entreprise (str) et le numéro de dossier (str).
        """
        with open(chemin, "r", encoding="utf-8") as fichier:
            return [
                tuple(ligne.strip().split(";", 3)[:3])
                for ligne in fichier if len(ligne.strip().split(";", 3)) == 3
            ]

    def afficher_warning(self):
        """
        Affiche une boîte de dialogue Warning toujours au premier
        plan avec une icône personnalisée dans la barre des tâches.
        """
        # Créer une fenêtre temporaire
        root = tkinter.Tk()
        root.title("Attention")
        root.geometry("2x2")
        root.deiconify()
        root.attributes("-topmost", True)

        # Afficher la boîte de dialogue
        messagebox.showwarning(
            "Attention",
            "Saisissez le captcha et cliquez sur le bouton de connexion.\n",
            parent=root
        )

        # Détruire la fenêtre après fermeture de la boîte de dialogue
        root.destroy()

    def connexion_site(self, identifiant: str, mot_de_passe: str):
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
        self.driver.get(LIEN_IMPOTS)

        # Connexion
        self.driver.find_element(By.ID, "ident").send_keys(identifiant)
        self.driver.find_element(By.NAME, "password").send_keys(mot_de_passe)

        # Désactiver les événements clavier temporairement
        self.driver.execute_script("""
            document.body.addEventListener('keydown', function(event) {
                event.stopPropagation();
            }, true);
        """)

        # Afficher la warning box
        self.afficher_warning()

        self.driver.switch_to.window(self.driver.current_window_handle)
        self.driver.find_element(By.ID, "inputcaptcha").click()

        # Attendre que l'URL change
        try:
            WebDriverWait(self.driver, 120).until(EC.url_to_be(LIEN_IMPOTS))
        except TimeoutException:
            print("Timeout lors de la connexion. ")
            logging.error("Timeout lors de la connexion.")
            self.connexion_site(identifiant, mot_de_passe)

    def traiter_siren(self, siren: str, nom_entreprise: str, code_dossier: str):
        """
        Traite un SIREN, un nom d'entreprise, et un code de dossier en ouvrant l'avis de CFE
        et en accédant au lien d'avis d'imposition associé.

        Args:
            siren (str): Numéro SIREN de l'entreprise.
            nom_entreprise (str): Nom de l'entreprise.
            code_dossier (str): Code de dossier associé.
        """
        # Je tente d'accéder à la page des avis CFE
        # Si elle est présente et contient des avis, je passe à l'étape du téléchargement
        succes = self.acceder_avis_cfe_du_siren(siren)
        if succes:
            self.traiter_lien_avis_imposition(code_dossier, nom_entreprise, siren)
        maj_avancee(self, echec=not succes)

    def acceder_avis_cfe_du_siren(self, siren):
        """
        Ouvre la page des Avis CFE et entre le numéro SIREN pour accéder aux informations CFE.

        Args:
            siren (str): Le numéro SIREN pour accéder aux informations CFE.

        Returns:
            bool: True si l'accès aux informations CFE est réussi, False sinon.
        """
        # Clique pour accéder à la page de saisie de SIREN
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='Avis CFE']"))).click()
        except (TimeoutException, WebDriverException):
            return self.acceder_avis_cfe_du_siren(siren)

        # S'assure que les champs sont vides
        for i in range(9):
            self.driver.find_element(By.ID, f"siren{i}").clear()

        # Entrer le SIREN
        for i, digit in enumerate(siren):
            self.driver.find_element(By.ID, f"siren{i}").send_keys(digit)

        # Cliquer sur le bouton consulter
        self.driver.find_element(By.NAME, "button.submitValider").click()

        # Vérifier si une nouvelle fenêtre s'ouvre
        if len(self.driver.window_handles) < 2:
            print("SIREN non accessible.")
            logging.error('SIREN - %s - INACCESSIBLE', siren)
            return False

        # Passer à la fenêtre qui s'est ouverte
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # Vérifier la présence de la page d'accueil, sinon réessayer
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Accueil du compte fiscal des professionnels')]")))
        except TimeoutException:
            return self.acceder_avis_cfe_du_siren(siren)

        # Essayer de cliquer sur le bouton pour accéder aux avis de CFE
        try:
            WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located(
                (By.XPATH, "//a[@class='custom_bouton_cfe']"))).click()
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
        logging.info("Arrivée sur la page des avis d'imposition.")

        # Vérifier si aucun document n'est trouvé
        try:
            WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class='messageTableau'] ul li")))
            print("Pas de document trouvés.")
            return
        except TimeoutException:
            pass

        # Obtention des lignes de document s'il y en a, sinon retour
        try:
            lignes = WebDriverWait(self.driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, "//tbody/tr")))
        except TimeoutException:
            print("Pas de document trouvés.")
            return

        # Clique sur le lien d'avis d'imposition pour chaque ligne et les renomme
        for ligne in lignes:
            cellules = ligne.find_elements(By.TAG_NAME, "td")
            if cellules:

                lien = ligne.find_element(By.TAG_NAME, "a")
                lien.click()
                logging.info("Clic sur le lien d'avis d'imposition.")
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

    def retour_accueil(self):
        """
        Retourne à la page d'accueil du site.
        """
        self.driver.get(LIEN_IMPOTS)
        WebDriverWait(self.driver, 10).until(EC.url_to_be(LIEN_IMPOTS))


def afficher_aide():
    """
    Affiche le message d'aide pour le script.
    """

    aide_message = """
        Usage : python recup_cfe.py

        Ce script récupère les avis d'imposition de la CFE pour un ensemble de SIREN fournis.

        Entrées :
        - Fichier 'SIREN.TXT' contenant les SIREN, noms d'entreprise et codes, au format :
            Siren;Nom;Code Dossier

        - Fichier 'identifiants.txt' avec les identifiants et le mot de passe, au format :
            identifiant
            mot_de_passe

        Exemples d'utilisation :
            python recup_cfe.py imposition
    """
    print(aide_message)


def gestion_erreur(siren: str, nom: str, code: str) -> bool:
    """
    Vérifie les erreurs dans les données fournies et journalise les anomalies.

    :param siren: Numéro SIREN (doit contenir uniquement des chiffres et être valide).
    :param nom: Nom associé au SIREN.
    :param code: Code complémentaire (doit contenir uniquement des chiffres ou caractères valides).
    :return: True si une condition d'erreur est vérifiée, sinon False.
    """
    # Vérification SIREN invalide
    if siren == "000000000":
        logging.info("SIREN invalide - %s", siren)
        return True

    # Vérification que le SIREN contient exactement 9 caractères
    if len(siren) != 9:
        logging.error("SIREN doit contenir exactement 9 caractères - %s", siren)
        return True

    # Vérification de données manquantes
    if not all((siren, nom, code)):
        logging.error("Données manquantes - SIREN: '%s', Nom: '%s', Code: '%s'", siren, nom, code)
        return True

    # Vérification si le SIREN contient des lettres
    if not siren.isdigit():
        logging.error("SIREN invalide - %s", siren)
        return True

    # Vérification si le code contient des lettres
    if not code.isdigit():
        logging.error("Code invalide - %s", code)
        return True

    # Si aucune erreur n'est détectée
    return False


def maj_avancee(app: Program, echec=False):
    """Met à jour les données d'avancement de l'application."""
    app.avancee["dossiers_traites"] += 1
    app.avancee["dossiers_restants"] -= 1
    app.avancee["dossiers_echec" if echec else "dossiers_succes"] += 1


def traitement(app: Program, window_app: WindowApp):
    """ Fonction de traitement des dossiers. """
    try:
        # Attente du clic sur le bouton ou fermeture de la fenêtre
        window_app.wait_variable(window_app.var_activite)

        if window_app.stopped:
            return

        print("Démarrage du traitement des dossiers...")
        window_app.etat_app = "En cours de traitement..."
        app.donnees = app.lire_donnees(window_app.web_data["fichier"])
        app.avancee["dossiers_total"] = len(app.donnees)
        app.avancee["dossiers_restants"] = len(app.donnees)
        window_app.update_progression(app.avancee, initialisation=True)

        app.initialiser_driver(window_app.web_data["destination"])

        app.connexion_site(window_app.web_data["identifiant"], window_app.web_data["mot_de_passe"])

        for compteur, (siren, nom, code) in enumerate(app.donnees, start=1):
            window_app.update_progression(app.avancee)
            if gestion_erreur(siren, nom, code):
                maj_avancee(app, echec=True)
                continue

            if not window_app:
                print(f"Fenêtre fermée pendant le traitement. {compteur} dossiers traités.")
                return

            print(f"Compteur: {compteur} | SIREN: {siren} | Nom: {nom} | Code: {code}")
            app.traiter_siren(siren, nom, code)
            app.fermer_fenetres()
            app.retour_accueil()

        window_app.update_progression(app.avancee)
        window_app.etat_app = "Programme terminé !"

    except Exception as e:
        print(f"Erreur : {e}")
        logging.exception("Erreur lors de l'exécution : %s", e)


def config_logging():
    """
    Configure les gestionnaires de logs pour enregistrer les logs d'info et d'erreur
    dans des fichiers séparés.
    """
    logger = logging.getLogger("mon_logger")
    logger.setLevel(logging.DEBUG)

    info_handler = logging.FileHandler("log_infos.txt", encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    info_handler.setFormatter(info_formatter)

    error_handler = logging.FileHandler("log_erreurs.txt", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    error_handler.setFormatter(error_formatter)

    if not logger.hasHandlers():
        logger.addHandler(info_handler)
        logger.addHandler(error_handler)

    return logger


def main():
    """
    Fonction principale qui initialise le journal de logs, crée une instance de la classe Program,
    et traite chaque SIREN, nom, et code.
    """

    print("Démarrage du script...")
    # Initialisation des classes de l'application
    logging.basicConfig(filename='log.txt', encoding='utf-8',
                        level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = config_logging()
    app = Program()
    window_app = WindowApp()

    # Lancement du traitement dans un thread
    thread = threading.Thread(target=traitement, args=(app, window_app), daemon=True)
    thread.start()

    # Gestion de l'interface
    try:
        window_app.mainloop()
    except Exception as e:
        logger.exception("Erreur lors de l'exécution de l'interface : %s", e)
        print(f"Erreur tkinter : {e}")

    if window_app.stopped:
        print("La fenêtre a été fermée. Arrêt du script.")
        return

    print("Script terminé !")


if __name__ == "__main__":
    main()
