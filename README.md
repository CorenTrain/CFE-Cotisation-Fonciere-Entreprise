# Automatisation de la récupération des avis de CFE

![Python Version](https://img.shields.io/badge/python-3%2B-blue.svg)
![Selenium](https://img.shields.io/badge/selenium-4.21.0-green.svg)

Ce script Python utilise Selenium pour automatiser la récupération des avis de Contribution Foncière des Entreprises (CFE) sur le site des impôts français. Il télécharge automatiquement les documents en format PDF et les renomme en utilisant le code dossier, le nom de l'entreprise et le numéro SIREN, facilitant ainsi la gestion documentaire pour les professionnels et le classement dans la GED (Gestion Electronique des Données) du cabinet.

## Fonctionnalités

- Connexion automatique au site des impôts avec des identifiants pré-enregistrés dans le fichier identifiants.txt (il faut renseigner le login et mot de passe).
- Recherche et téléchargement des avis de CFE pour une liste de SIREN qui sont indiqués dans le fichier SIREN.txt
- Renommage automatique des fichiers PDF téléchargés selon le SIREN et le nom de l'entreprise indiqués dans le fichier SIREN.txt.
- Logging des actions pour un suivi facile pour le debuggage.

## Prérequis

- Aucun

## Installation

Téléchargez la dernière version du script située dans la section Release à droite.

## Configuration

1. Créez et assurez-vous que votre fichier de SIREN contient la liste comprenant numéros SIREN, noms d'entreprises et codes dossiers à traiter pour lesquels le cabinet a un accès délégué, chaque ligne doit être au format suivant : `SIREN;NOM;NUM DOSSIER`.

## Utilisation

1. Lancez le script en exécutant le fichier téléchargé.
2. Saisissez vos identifiants impots professionnels (Aucun identifiant n'est stocké pendant le processus, ils ne sont utilisés que pour vous connecter et sont supprimés).
3. Renseignez le fichier contenant vos SIREN.
4. Choisissez l'emplacement où vous voulez que vos fichiers soient téléchargés. 
