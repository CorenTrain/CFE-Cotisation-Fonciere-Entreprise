"""Programme de recuperation des CFE."""
import logging
import os
import shutil
import sys
from datetime import datetime
from itertools import islice
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
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
        connect_to_website_with_credentials (self): Connects to the website using the provided
        credentials.
        process_avis_imposition_link (self, code, name): Processes a single link for the avis
        d'imposition.
        open_avis_cfe (self, siren): Opens the Avis CFE page and enters the SIREN number to access
        the CFE information.
        process_siren (self, siren, name, code): Processes a SIREN, name, and code by opening the
        avis de CFE and processing the avis imposition link.
    """

    def __init__(self):
        self.script_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.url = "https://cfspro-idp.impots.gouv.fr/oauth2/authorize?[...]"
        self.driver = self.initialize_driver()
        self.file_path = os.path.join(self.script_path, "SIREN.TXT")
        self.credentials_file = os.path.join(self.script_path, "identifiants.txt")
        self.data = self.read_data()
        self.creds = self.read_creds()
        print(self.creds)

    def __del__(self):
        self.driver.quit()

    def initialize_driver(self):
        """
        Initializes and returns a Selenium WebDriver object for Firefox with specific options.

        Returns:
            webdriver.Firefox: A WebDriver object for Firefox with the following options:
                - Disable extensions
                - Disable notifications
                - Disable the sandbox
                - Disable the dev-shm-usage
                - Set the download folder to the current directory
                - Hide the download manager when starting
                - Set the download directory to the current directory
                - Never ask to save files with the application/pdf MIME type
                - Disable PDF.js
        """
        current_directory = os.path.join(self.script_path, "Documents")
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--disable-extensions")
        firefox_options.add_argument("--disable-notifications")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference("browser.download.dir", current_directory)
        firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        firefox_options.set_preference("pdfjs.disabled", True)
        return webdriver.Firefox(options=firefox_options)

    def read_creds(self):
        """
        Reads the login credentials from the file and returns them as a list.

        Returns:
            list: A list containing the first two lines of the `credentials_file`, with leading
            and trailing whitespace removed.
        """
        with open(self.credentials_file, "r", encoding="utf-8") as file:
            return [line.strip() for line in islice(file, 2)]

    def read_data(self):
        """
        Reads data from a file and returns a list of tuples containing the SIREN, company name,
        and dossier number.

        Returns:
            list: A list of tuples, where each tuple contains the SIREN (a string), company name
            (a string), and dossier number (a string).
        """
        with open(self.file_path, "r", encoding="utf-8") as file:
            next(file)
            return [tuple(line.strip().split(";", 3)[:3])
                    for line in file if len(line.strip().split(";", 3)) == 3]

    def connect_to_website_with_credentials(self):
        """
        Connects to the website using the provided credentials.

        This function navigates to the website specified by `self.url` and checks if the user is
        already logged in. If the user is already logged in, it prints "Déjà connecté."
        and returns. If the user is not logged in, it proceeds with the login process.

        The login process involves finding the username and password input fields on the website,
        entering the credentials from `self.creds`, and clicking the login button.

        Parameters:
            self (Program): The Program instance.

        Returns:
            None
        """
        self.driver.get(self.url)

        # Vérification si déjà connecté
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "identifiant_après_connexion")))
            print("Déjà connecté.")
            return
        except TimeoutException:
            print("Pas encore connecté. Procédure de connexion en cours.")

        # Connexion
        self.driver.find_element(By.ID, "ident").send_keys(self.creds[0])
        self.driver.find_element(By.NAME, "password").send_keys(self.creds[1])
        self.driver.find_element(By.XPATH, "//button[contains(text(), 'Connexion')]").click()

    def process_siren(self, siren, name, code):
        """
        Process a SIREN, name, and code by opening the avis de CFE and processing the avis
        imposition link.

        Args:
            siren (str): The SIREN number.
            name (str): The name of the company.
            code (str): The dossier number.

        Returns:
            None
        """
        if not self.open_avis_cfe(siren):
            return
        self.process_avis_imposition_link(code, name)

    def open_avis_cfe(self, siren):
        """
        Opens the Avis CFE page and enters the SIREN number to access the CFE information.

        Args:
            siren (str): The SIREN number to access the CFE information.

        Returns:
            bool: True if the CFE information is successfully accessed, False otherwise.
        """
        self.driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")

        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Avis CFE')]"))).click()

        for i, digit in enumerate(siren):
            self.driver.find_element(By.ID, f"siren{i}").send_keys(digit)

        # Clic sur le bouton consulter
        self.driver.find_element(By.NAME, "button.submitValider").click()

        window_handles = self.driver.window_handles

        if len(window_handles) < 2:
            print("SIREN non accessible.")
            logging.info('SIREN - %s - INACCESSIBLE', siren)
            return False
        self.driver.switch_to.window(window_handles[-1])

        # Tente de cliquer sur Accès aux avis de CFE et s'il ne fonctionne pas, passe au SIREN
        # suivant
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Accueil du compte fiscal des professionnels')]")))
        except TimeoutException:
            return self.open_avis_cfe(siren)

        try:
            WebDriverWait(self.driver, 0.5).until(EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]"))).click()
        except TimeoutException:
            print("Pas de CFE, passage au SIREN suivant.")
            logging.info('PAS DE CFE - SIREN - %s', siren)
            return False
        return True

    def process_avis_imposition_link(self, code, name):
        """
          Process a single link for the avis d'imposition.

          Args:
              avis_imposition_link (WebElement): The avis imposition link to process.

          Returns:
              bool: True if the link was successfully processed, False otherwise.
          """
        def delete_and_restart():
            try:
                self.driver.find_element(By.XPATH, "//a[contains(text(), 'Tout effacer')]").click()
            except NoSuchElementException:
                pass

            self.driver.find_element(By.XPATH, "//span[contains(text(), 'Fermer')]").click()
            print("Erreur lors de la récupération du fichier, nouvelle tentative.")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.back()
            return False

        # Procédure pour un seul fichier
        def process_single_link(avis_imposition_link):
            print("Clic sur le lien d'avis d'imposition...")
            avis_imposition_link.click()

            self.driver.find_element(By.XPATH, '//img[@alt="Demandes d\'impression"]').click()
            element_siret_label = self.driver.find_element(
                By.XPATH, "//td[contains(text(), 'N° SIRET')]")

            # Récupère le numéro de SIRET
            siret = element_siret_label.find_element(By.XPATH, "following-sibling::td").text

            # Vérification de la présence du lien "Tout le document"
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Tout le document"))).click()

            self.driver.switch_to.window(self.driver.window_handles[-1])

            try:
                text_div = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((
                    By.XPATH, "//td[contains(text(),'Demandé le')]")))
            except NoSuchElementException:
                return delete_and_restart()

            while True:
                try:
                    text_div = self.driver.find_element(
                        By.XPATH, "//td[contains(text(),'Demandé le')]")
                    if "En cours" not in text_div.text and "moins" not in text_div.text:
                        temp = text_div.text
                        break
                except StaleElementReferenceException:
                    pass
                except NoSuchElementException:
                    return delete_and_restart()
                sleep(1)

            if "En erreur" in temp:
                return delete_and_restart()

            try:
                WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(
                    (By.XPATH, "//img[contains(@alt, 'Imprimer - PDF')]"))).click()
                WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Tout effacer')]"))).click()
                print("Fichier téléchargé.")
            except (NoSuchElementException, TimeoutException):
                return delete_and_restart()

            self.rename_downloaded_pdf(code, name, self.script_path, siret)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.back()
            return True
        # Boucle sur tous les liens de documents
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
        except TimeoutException:
            print("Pas d'avis d'imposition")
            return

        avis_imposition_links = self.driver.find_elements(By.LINK_TEXT, "Avis d'imposition")
        print(f"Nombre d'avis d'imposition: {len(avis_imposition_links)}")
        i = 0
        while i < len(avis_imposition_links):
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
            avis_imposition_links = self.driver.find_elements(By.LINK_TEXT, "Avis d'imposition")
            if process_single_link(avis_imposition_links[i]):
                i = i + 1

    def rename_downloaded_pdf(self, code, company_name, download_directory, siret):
        """
        Renames a downloaded PDF file by appending relevant information to the file name.

        Args:
            code (str): The code associated with the PDF file.
            company_name (str): The name of the company.
            download_directory (str): The directory where the PDF file is downloaded.
            siret (str): The SIRET number of the company.

        Returns:
            None

        Raises:
            None
        """
        year = datetime.now().year
        original_file = os.path.join(self.script_path, "Documents", "doc.pdf")
        new_file_name = f"{code}_{company_name.replace(' ', '_')}_" \
            f"{siret.replace(' ', '')}_CFE_{year}.pdf"
        new_file = os.path.join(download_directory, new_file_name)
        destination_directory = os.path.join(self.script_path, "Documents")

        if os.path.exists(original_file):
            os.rename(original_file, new_file)
            # Créer le répertoire de destination s'il n'existe pas
            if not os.path.exists(destination_directory):
                os.makedirs(destination_directory)
                print(f"Le répertoire de destination '{destination_directory}' a été créé.")

            # Déplacer le fichier renommé vers le répertoire de destination
            shutil.move(new_file, os.path.join(destination_directory, new_file_name))
            print(f"Le fichier renommé a été déplacé vers :"
                  f"{os.path.join(destination_directory, new_file_name)}")
        else:
            print("Le fichier 'doc.pdf' n'a pas été trouvé.")

    def close_windows(self):
        """
        Closes all the windows in the browser.

        Returns:
            None
        """
        if len(self.driver.window_handles) < 2:
            return
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])


def main():
    """
    The main function that initializes the logging, creates an instance of the Program class, and
    iterates over the data to process each SIREN, name, and code. It prints the counter, code,
    name, and siren for each iteration. It then calls the connect_to_website_with_credentials
    method of the Program class to connect to the website with credentials, and calls the
    process_siren method of the Program class to process the SIREN, name, and code. The script
    is completed when all the SIRENs have been processed.

    Parameters:
    None

    Returns:
    None
    """
    print("Démarrage du script...")
    logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
    app = Program()
    compteur = 1

    # Pour chacun des SIREN
    for data in app.data:
        siren = data[0]
        name = data[1]
        code = data[2]
        print(f"\nCompteur : {compteur} Code: {code} Name: {name} Siren: {siren}")

        app.connect_to_website_with_credentials()
        app.process_siren(siren, name, code)
        app.close_windows()
        compteur = compteur + 1

    print("Script terminé !")


if __name__ == "__main__":
    main()
