"""Programme de recuperation des CFE."""
import logging
import os
import shutil
import sys
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
        self.credentials_file = os.path.join(
            self.script_path, "identifiants.txt")
        self.data = self.read_data()
        self.creds = self.read_creds()

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
        firefox_options.set_preference(
            "browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference(
            "browser.download.dir", current_directory)
        firefox_options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        firefox_options.set_preference("pdfjs.disabled", True)
        return webdriver.Firefox(options=firefox_options)

    def read_creds(self):
        """
        Reads the credentials from the `credentials_file` and returns them as a list.

        Returns:
            list: A list containing the first two lines of the `credentials_file`, with leading
            and trailing whitespace removed.
        """
        creds = []
        with open(self.credentials_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
            creds[0] = lines[0].strip()
            creds[1] = lines[1].strip()

        return creds

    def read_data(self):
        """
        Reads data from a file and returns a list of tuples containing the SIREN, company name,
        and dossier number.

        Returns:
            list: A list of tuples, where each tuple contains the SIREN (a string), company name
            (a string), and dossier number (a string).
        """
        file_path = self.file_path
        info_list = []

        with open(file_path, "r", encoding="utf-8") as file:
            next(file)
            for line in file:
                parts = line.strip().split(";", 3)
                if len(parts) == 3:
                    siren = parts[0].strip()
                    company_name = parts[1].strip()
                    dossier_number = parts[2].strip()
                    info_list.append((siren, company_name, dossier_number))

        return info_list

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
            WebDriverWait(self.driver, 2, poll_frequency=0.1).until(
                EC.presence_of_element_located((By.ID, "identifiant_après_connexion")))
            print("Déjà connecté.")
            return
        except TimeoutException:
            print("Pas encore connecté. Procédure de connexion en cours.")

        # Connexion
        username_input = self.driver.find_element(By.ID, "ident")
        password_input = self.driver.find_element(By.NAME, "password")
        username_input.send_keys(self.creds[0])
        password_input.send_keys(self.creds[1])

        self.driver.find_element(
            By.XPATH, "//button[contains(text(), 'Connexion')]").click()

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
        original_file = os.path.join(download_directory, "doc.pdf")
        new_file_name = f"{code}_{company_name.replace(' ', '_')}_{
            siret.replace(' ', '')}_CFE_{year}.pdf"
        new_file = os.path.join(download_directory, new_file_name)
        destination_directory = "./Documents/"

        if os.path.exists(original_file):
            os.rename(original_file, new_file)
            print(f"Le fichier PDF a été renommé en : {new_file}")

            # Créer le répertoire de destination s'il n'existe pas
            if not os.path.exists(destination_directory):
                os.makedirs(destination_directory)
                print(f"Le répertoire de destination '{
                    destination_directory}' a été créé.")

            # Déplacer le fichier renommé vers le répertoire de destination
            shutil.move(new_file, os.path.join(
                destination_directory, new_file_name))
            print(f"Le fichier renommé a été déplacé vers : {
                os.path.join(destination_directory, new_file_name)}")
        else:
            print("Le fichier 'doc.pdf' n'a pas été trouvé.")

    def process_avis_imposition_link(self, code, name):
        """
        Process a single link for the avis d'imposition.

        Args:
            avis_imposition_link (WebElement): The avis imposition link to process.

        Returns:
            bool: True if the link was successfully processed, False otherwise.
        """
        # Procédure pour un seul fichier
        def process_single_link(avis_imposition_link):
            print("Début avis d'imposition:")
            avis_imposition_link.click()

            demandes_impression_image = self.driver.find_element(
                By.XPATH, '//img[@alt="Demandes d\'impression"]')
            demandes_impression_image.click()

            element_siret_label = self.driver.find_element(
                By.XPATH, "//td[contains(text(), 'N° SIRET')]")

            element_siret_value = element_siret_label.find_element(
                By.XPATH, "following-sibling::td")
            siret = element_siret_value.text

            # Vérification de la présence du lien "Tout le document"
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Tout le document")))
            tout_document_link = self.driver.find_element(
                By.LINK_TEXT, "Tout le document")
            tout_document_link.click()

            self.driver.switch_to.window(self.driver.window_handles[-1])

            print("Vérification de la présence du PDF")
            wait = WebDriverWait(self.driver, 30)
            try:
                # Tentative d'enregistrement du fichier PDF
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//img[contains(@alt, 'Imprimer - PDF')]"))).click()
            except TimeoutException:
                # Gestion d'erreur, si le PDF n'est pas trouvé ou s'il n'y a pas de lien
                # "Tout effacer"
                try:
                    wait = WebDriverWait(self.driver, 5)
                    tout_effacer_link = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))
                    tout_effacer_link.click()
                    print("Pas de PDF trouvé, Nouvelle tentative.")
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.back()
                    sleep(10)
                    return False
                except TimeoutException:
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//span[contains(text(), 'Fermer')]"))).click()
                    print(
                        "Erreur lors de la récupération du fichier, nouvelle tentative.")
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.back()
                    sleep(10)
                    return False

            wait = WebDriverWait(self.driver, 90)
            tout_effacer_link = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))
            tout_effacer_link.click()
            print("Le lien 'Tout effacer' a été cliqué avec succès.")

            sleep(2)
            self.rename_downloaded_pdf(code,  name, os.getcwd(), siret)

            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.back()
            sleep(2)
            return True

        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
        except TimeoutException:
            self.driver.quit()
            print("Pas d'avis d'imposition")
            return

        avis_imposition_links = self.driver.find_elements(
            By.LINK_TEXT, "Avis d'imposition")
        print(f"Nombre d'avis d'imposition: {len(avis_imposition_links)}")
        i = 0
        while i < len(avis_imposition_links):
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
            avis_imposition_links = self.driver.find_elements(
                By.LINK_TEXT, "Avis d'imposition")
            if process_single_link(avis_imposition_links[i]):
                i = i + 1
        self.driver.quit()

    def open_avis_cfe(self, siren):
        """
        Opens the Avis CFE page and enters the SIREN number to access the CFE information.

        Args:
            siren (str): The SIREN number to access the CFE information.

        Returns:
            bool: True if the CFE information is successfully accessed, False otherwise.
        """
        print("Connexion à la page d'accueil")
        self.driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")

        print("clique sur Avis CFE")
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Avis CFE')]")))
        avis_cfe_link = self.driver.find_element(
            By.XPATH, "//a[contains(text(), 'Avis CFE')]")
        avis_cfe_link.click()

        for i in range(9):
            siren_input = self.driver.find_element(By.ID, f"siren{i}")
            siren_input.send_keys(siren[i])

        consulter_button = self.driver.find_element(
            By.NAME, "button.submitValider")
        consulter_button.click()

        window_handles = self.driver.window_handles
        self.driver.switch_to.window(window_handles[-1])

        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]")))
            self.driver.find_element(
                By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]").click()
            print("Clique sur Accès aux avis de CFE")
        except TimeoutException:
            print("Pas de CFE, passage au SIREN suivant.")
            logging.info('PAS DE CFE; SIREN; %s', siren)

            self.driver.quit()
            return False
        return True

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
        if self.open_avis_cfe(siren):
            self.process_avis_imposition_link(code, name)


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
    logging.basicConfig(filename='error_log.txt',
                        level=logging.ERROR, format='%(asctime)s - %(message)s')
    app = Program()
    compteur = 0

    # Pour chacun des SIREN
    for compteur in app.data:
        siren = app.data[compteur][0]
        name = app.data[compteur][1]
        code = app.data[compteur][2]
        print(f"\nCompteur : {compteur} Code: \
            {code} Name: {name} Siren: {siren}")

        app.connect_to_website_with_credentials()
        app.process_siren(siren, name, code)
        compteur = compteur + 1

    print("Script terminé !")


if __name__ == "__main__":
    main()
