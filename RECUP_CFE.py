import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import logging
import datetime
import os

# Variables
url = "https://cfspro-idp.impots.gouv.fr/oauth2/authorize?[...]"
credentials_file = "identifiants.txt"
file_path = "SIREN.TXT"


def initialize_driver():
    current_directory = os.getcwd()
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": current_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })
    return webdriver.Chrome(options=chrome_options)


def connect_to_website_with_credentials(driver, url, credentials_file):
    driver.get(url)

    # Vérification si déjà connecté
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.ID, "identifiant_après_connexion")))
        print("Déjà connecté.")
        return driver
    except:
        print("Pas encore connecté. Procédure de connexion en cours.")

    # Connexion
    with open(credentials_file, "r") as file:
        lines = file.readlines()
        username = lines[0].strip()
        password = lines[1].strip()

    username_input = driver.find_element(By.ID, "ident")
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys(username)
    password_input.send_keys(password)

    login_button = driver.find_element(
        By.XPATH, "//button[contains(text(), 'Connexion')]")
    login_button.click()
    sleep(1)

    return driver


def rename_downloaded_pdf(code, company_name, download_directory, siret):
    year = datetime.date.today().year
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


def read_siren_data(file_path):
    siren_data = []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(";", 2)
            if len(parts) == 3:
                company_name = parts[1].strip()
                # Ajoutez le nom de l'entreprise à la liste
                siren_data.append(company_name)
    return siren_data


def extract_valid_siren_numbers(file_path):
    siren_numbers = []

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(";", 2)
            if len(parts) == 3:
                siren_number = parts[0].strip()
                # Vérifier que siren_number contient exactement 9 chiffres
                if len(siren_number) == 9 and siren_number.isdigit():
                    siren_numbers.append(siren_number)
    return siren_numbers


def read_code(file_path):
    code_list = []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(";", 2)
            if len(parts) == 3:
                code = parts[2].strip()
                # Ajouter le code à la liste
                code_list.append(code)
    return code_list


def process_avis_imposition_link(driver, code, name):
    # Procédure pour un seul fichier
    def process_single_link(avis_imposition_link):
        print("Début avis d'imposition:")
        avis_imposition_link.click()

        demandes_impression_image = driver.find_element(
            By.XPATH, '//img[@alt="Demandes d\'impression"]')
        demandes_impression_image.click()

        element_siret_label = driver.find_element(
            By.XPATH, "//td[contains(text(), 'N° SIRET')]")

        element_siret_value = element_siret_label.find_element(
            By.XPATH, "following-sibling::td")
        siret = element_siret_value.text

        # Vérification de la présence du lien "Tout le document"
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "Tout le document")))
        tout_document_link = driver.find_element(
            By.LINK_TEXT, "Tout le document")
        tout_document_link.click()

        driver.switch_to.window(driver.window_handles[-1])

        print("Vérification de la présence du PDF")
        wait = WebDriverWait(driver, 30)
        try:
            # Tentative d'enregistrement du fichier PDF
            print_image = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//img[contains(@alt, 'Imprimer - PDF')]")))
            print_image.click()
        except:
            # Gestion d'erreur, si le PDF n'est pas trouvé ou s'il n'y a pas de lien "Tout effacer"
            try:
                wait = WebDriverWait(driver, 5)
                tout_effacer_link = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))
                tout_effacer_link.click()
                print("Pas de PDF trouvé, Nouvelle tentative.")
                driver.close()
                driver.switch_to.window(driver.window_handles[1])
                driver.back()
                sleep(10)
                return False
            except:
                Fermer_link = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'Fermer')]")))
                Fermer_link.click()
                print("Erreur lors de la récupération du fichier, nouvelle tentative.")
                driver.close()
                driver.switch_to.window(driver.window_handles[1])
                driver.back()
                sleep(10)
                return False

        wait = WebDriverWait(driver, 90)
        tout_effacer_link = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))
        tout_effacer_link.click()
        print("Le lien 'Tout effacer' a été cliqué avec succès.")

        sleep(2)
        rename_downloaded_pdf(code,  name, os.getcwd(), siret)

        driver.close()
        driver.switch_to.window(driver.window_handles[1])
        driver.back()
        sleep(2)
        return True

    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
    except:
        driver.quit()
        print("Pas d'avis d'imposition")
        return

    avis_imposition_links = driver.find_elements(
        By.LINK_TEXT, "Avis d'imposition")
    print(f"Nombre d'avis d'imposition: {len(avis_imposition_links)}")
    i = 0
    while i < len(avis_imposition_links):
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))
        avis_imposition_links = driver.find_elements(
            By.LINK_TEXT, "Avis d'imposition")
        if process_single_link(avis_imposition_links[i]):
            i = i + 1
    driver.quit()


def open_avis_cfe(driver, siren):
    print("Connexion à la page d'accueil")
    driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")

    print("clique sur Avis CFE")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(
        (By.XPATH, "//a[contains(text(), 'Avis CFE')]")))
    avis_cfe_link = driver.find_element(
        By.XPATH, "//a[contains(text(), 'Avis CFE')]")
    avis_cfe_link.click()

    for i in range(9):
        siren_input = driver.find_element(By.ID, f"siren{i}")
        siren_input.send_keys(siren[i])

    consulter_button = driver.find_element(
        By.NAME, "button.submitValider")
    consulter_button.click()

    window_handles = driver.window_handles
    driver.switch_to.window(window_handles[-1])

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]")))
        acces_cfe_button = driver.find_element(
            By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]")
        acces_cfe_button.click()
        print("Clique sur Accès aux avis de CFE")
    except:
        print("Pas de CFE, passage au SIREN suivant.")
        logging.info(";PAS DE CFE; SIREN; " + siren)
        driver.quit()
        return False
    return True


def process_siren(driver, siren, name, code):
    if open_avis_cfe(driver, siren):
        process_avis_imposition_link(driver, code, name)
    return


def main():
    logging.basicConfig(filename='error_log.txt',
                        level=logging.ERROR, format='%(asctime)s - %(message)s')

    print("Création de la liste de SIREN")
    siren_numbers = extract_valid_siren_numbers(file_path)
    print(siren_numbers)

    print("Création de la liste des noms d'entreprises:")
    name_company_list = read_siren_data(file_path)
    print(name_company_list)

    print("Création de la liste des codes:")
    file_code = read_code(file_path)
    print(file_code)

    compteur = 0

    # Pour chacun des SIREN
    while compteur < len(siren_numbers):
        siren = siren_numbers[compteur]
        name = name_company_list[compteur]
        code = file_code[compteur]
        print(f"\n{name} & ID: {code} & Compteur : {compteur}")

        driver = initialize_driver()
        driver = connect_to_website_with_credentials(
            driver, url, credentials_file)
        process_siren(driver, siren, name, code)
        compteur = compteur + 1

    print("Script terminé !")


if __name__ == "__main__":
    main()
