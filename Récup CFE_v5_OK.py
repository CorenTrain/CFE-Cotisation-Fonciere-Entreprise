from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
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


def rename_downloaded_pdf(code, company_name, download_directory):
    # Get actual year
    year = datetime.date.today().year - 1
    original_file = os.path.join(download_directory, "doc.pdf")
    new_file_name = f"{code}_{company_name.replace(' ', '_')}_CFE_{year}.pdf"
    new_file = os.path.join(download_directory, new_file_name)

    if os.path.exists(original_file):
        os.rename(original_file, new_file)
        print(f"Le fichier PDF a été renommé en : {new_file}")
    else:
        print("Le fichier 'doc.pdf' n'a pas été trouvé.")


def read_siren_data(file_path):
    siren_data = []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(",", 2)
            if len(parts) == 3:
                company_name = parts[1].strip()
                # Ajoutez le nom de l'entreprise à la liste
                siren_data.append(company_name)
    return siren_data


def extract_valid_siren_numbers(file_path):
    siren_numbers = []

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(",", 2)
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
            parts = line.strip().split(",", 2)
            if len(parts) == 3:
                code = parts[2].strip()
                # Ajouter le code à la liste
                code_list.append(code)
    return code_list


def main():

    # Création de la liste des SIREN à traiter
    print("Création de la liste de SIREN")
    siren_numbers = extract_valid_siren_numbers(file_path)
    print(siren_numbers)

    # Création de la liste des noms d'entreprises
    print("Création de la liste des noms d'entreprises:")
    name_company_list = read_siren_data(file_path)
    print(name_company_list)

    # Création de la liste des codes
    print("Création de la liste des codes:")
    file_code = read_code(file_path)
    print(file_code)

    compteur = 0

    # Pour chacun des SIREN
    while compteur < siren_numbers.__len__():
        siren = siren_numbers[compteur]
        name = name_company_list[compteur]
        code = file_code[compteur]
        print(f"\n{name} & ID: {code} & Compteur : {compteur}")

        driver = initialize_driver()
        driver = connect_to_website_with_credentials(
            driver, url, credentials_file)

        print("Connexion à la page d'accueil")
        driver.get("https://cfspro.impots.gouv.fr/mire/accueil.do")

        print("Je clique sur Avis CFE")
        avis_cfe_link = driver.find_element(
            By.XPATH, "//a[contains(text(), 'Avis CFE')]")
        avis_cfe_link.click()

        for i in range(9):
            print(f"Traitement du SIREN {siren}")
            siren_input = driver.find_element(By.ID, f"siren{i}")
            siren_input.send_keys(siren[i])

        consulter_button = driver.find_element(
            By.NAME, "button.submitValider")
        consulter_button.click()

        # sleep(2)

        window_handles = driver.window_handles
        driver.switch_to.window(window_handles[-1])

        # sleep(2)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]")))
        except:
            print("Pas de CFE, passage au suivant.")
            driver.quit()
            compteur = compteur + 1
            continue

        acces_cfe_button = driver.find_element(
            By.XPATH, "//span[contains(text(), 'Accès aux avis de CFE')]")
        acces_cfe_button.click()
        print("Je clique sur Accès aux avis de CFE")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "Avis d'imposition")))

        avis_imposition_link = driver.find_element(
            By.LINK_TEXT, "Avis d'imposition")
        avis_imposition_link.click()

        demandes_impression_image = driver.find_element(
            By.XPATH, '//img[@alt="Demandes d\'impression"]')
        demandes_impression_image.click()

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "Tout le document")))
        tout_document_link = driver.find_element(
            By.LINK_TEXT, "Tout le document")
        tout_document_link.click()

        driver.switch_to.window(driver.window_handles[-1])

        wait = WebDriverWait(driver, 20)
        try:
            print_image = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//img[@alt='Imprimer - PDF 33 Ko']")))
        except:
            try:
                print("Pas de PDF trouvé, passage au suivant.")
                wait = WebDriverWait(driver, 5)
                Tout_effacer_link = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))
                Tout_effacer_link.click()
            except:
                Fermer_link = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'Fermer')]")))
                Fermer_link.click()
            print("Erreur lors de la récupération du fichier, nouvelle tentative.")
            driver.quit()
            continue

        # Si l'image est présente, vous pouvez cliquer dessus ou effectuer d'autres actions
        print_image.click()
        wait = WebDriverWait(driver, 90)
        tout_effacer_link = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//a[contains(text(), 'Tout effacer')]")))

        # Si le lien "Tout effacer" est présent, cliquez dessus
        tout_effacer_link.click()
        print("Le lien 'Tout effacer' a été cliqué avec succès.")

        rename_downloaded_pdf(code,  name, os.getcwd())

        # Fermez le navigateur à la fin
        driver.quit()

        compteur = compteur + 1

    print("Script terminé !")


if __name__ == "__main__":
    main()
