import glob
import logging
import os
import shutil
import sys
from datetime import datetime
from itertools import islice
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Program:
    def __init__(self):
        self.script_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.url = "https://cfspro-idp.impots.gouv.fr/oauth2/authorize?[...]"
        self.file_path = os.path.join(self.script_path, "SIREN.TXT")
        self.credentials_file = os.path.join(self.script_path, "identifiants.txt")
        self.donnees = self.lire_donnees()
        self.creds = self.lire_identifiants()
        print(self.creds)
        self.driver = self.initialiser_driver()
        self.is_first_connection = True  # Ajout de la variable pour vérifier la première connexion

    def __del__(self):
        self.driver.quit()

    def initialiser_driver(self):
        options_firefox = FirefoxOptions()
        options_firefox.add_argument("--disable-extensions")
        options_firefox.add_argument("--disable-notifications")
        options_firefox.add_argument("--no-sandbox")
        options_firefox.add_argument("--disable-dev-shm-usage")
        dossier_actuel = os.path.join(self.script_path, "Documents")
        options_firefox.set_preference("browser.download.folderList", 2)
        options_firefox.set_preference("browser.download.manager.showWhenStarting", False)
        options_firefox.set_preference("browser.download.dir", dossier_actuel)
        options_firefox.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        options_firefox.set_preference("pdfjs.disabled", True)
        return webdriver.Firefox(options=options_firefox)

    def lire_identifiants(self):
        with open(self.credentials_file, "r", encoding="utf-8") as fichier:
            return [ligne.strip() for ligne in islice(fichier, 2)]

    def lire_donnees(self):
        with open(self.file_path, "r", encoding="utf-8") as fichier:
            next(fichier)
            return [
                tuple(ligne.strip().split(";", 3)[:3])
                for ligne in fichier if len(ligne.strip().split(";", 3)) == 3
            ]

    def connexion_site(self):
        print("Ouverture de la page...")
        self.driver.get(self.url)

        try:
            WebDriverWait(self.driver, 0.5).until(
                EC.presence_of_element_located((By.ID, "identifiant_après_connexion")))
            print("Déjà connecté.")
            return
        except TimeoutException:
            print("Pas encore connecté. Procédure de connexion en cours.")

        # Attendre 10 secondes uniquement lors de la première connexion
        if self.is_first_connection:
            print("Délai de 10 secondes pour ajouter le captcha...")
            sleep(10)
            self.is_first_connection = False  # Marque que la première connexion a eu lieu

        self.driver.find_element(By.ID, "ident").send_keys(self.creds[0])
        self.driver.find_element(By.NAME, "password").send_keys(self.creds[1])
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Connexion')]").click()

    def traiter_siren(self, siren, nom_entreprise, code_dossier):
        if self.ouvrir_avis_cfe(siren):
            self.traiter_lien_avis_imposition(code_dossier, nom_entreprise, siren)

    def ouvrir_avis_cfe(self, siren):
        try:
            self.driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")
        except TimeoutException:
            print("Timeout lors de l'accès à la page d'accueil.")
            return self.ouvrir_avis_cfe(siren)

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Avis CFE')]"))
        ).click()

        for i, digit in enumerate(siren):
            self.driver.find_element(By.ID, f"siren{i}").send_keys(digit)

        self.driver.find_element(By.NAME, "button.submitValider").click()

        if len(self.driver.window_handles) < 2:
            print("SIREN non accessible.")
            logging.info('SIREN - %s - INACCESSIBLE', siren)
            return False

        self.driver.switch_to.window(self.driver.window_handles[-1])

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Accueil du compte fiscal des professionnels')]")
                )
            )
        except TimeoutException:
            return self.ouvrir_avis_cfe(siren)

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
        annee = datetime.now().year
        nouveau_nom = f"{code}_{nom_entreprise.replace(' ', '_')}_{siret.replace(' ', '')}_CFE_{annee}.pdf"
        chemin_source = os.path.join(dossier_telechargement, "Documents", "AvisCfe*.pdf")

        fichiers = glob.glob(chemin_source)
        if len(fichiers) == 0:
            print("Fichier PDF correspondant introuvable.")
            return

        fichier_original = fichiers[0]
        chemin_nouveau = os.path.join(dossier_telechargement, nouveau_nom)
        dossier_destination = os.path.join(self.script_path, "Documents")
        os.rename(fichier_original, chemin_nouveau)
        os.makedirs(dossier_destination, exist_ok=True)
        shutil.move(chemin_nouveau, os.path.join(dossier_destination, nouveau_nom))
        print(f"Le fichier renommé a été déplacé vers : {os.path.join(dossier_destination, nouveau_nom)}")

    def fermer_fenetres(self):
        if len(self.driver.window_handles) > 1:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])


def afficher_aide():
    aide_message = """
        Usage : python recup_cfe.py [acomptes|imposition]
        ...
    """
    print(aide_message)


def main():
    argument = sys.argv[1] if len(sys.argv) == 2 else None
    if argument not in ["acomptes", "imposition"] and argument not in ["-h", "--help"]:
        afficher_aide()
        return

    try:
        print("Démarrage du script...")
        logging.basicConfig(filename='log.txt', level=logging.INFO,
                            format='%(asctime)s - %(message)s')

        app = Program()
        print("Initialisation terminée.")

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
