# ÉquiTable

Application web de gestion de cuisine : suivi du stock (frigo et placard), recettes, planning des repas de la semaine et liste de courses. Les recettes de démo incluent des plats sénégalais comme le Djolof Rice et le Yassa.

Projet commencé pour l'examen de Python et repris depuis.

Ndeye Maguette Kane, 2025

Le [cahier des charges](docs/EquiTable_cahier_des_charges.pdf) décrit la conception de l'application, son modèle de données et les technologies utilisées.

## Fonctionnalités

- Gestion du frigo et du placard : quantité, unité, catégorie, seuil d'alerte
- Alertes sur l'accueil pour les ingrédients en rupture ou en stock bas
- Recettes avec photo, coût en FCFA, temps, portions et quantités par ingrédient
- Pour chaque recette : ingrédients disponibles, ingrédients manquants et liste de courses
- Recherche et filtres par nom, ingrédient, budget, temps de préparation et disponibilité
- Suggestion de recette en fonction du stock
- Validation d'une recette cuisinée, avec mise à jour automatique du stock
- Planning des déjeuners et dîners de la semaine, avec liste de courses et budget
- Historique des repas et statistiques du mois
- Favoris, export PDF et partage de la liste de courses sur WhatsApp

## Lancer le projet

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

cd monmenus
python manage.py migrate
python manage.py loaddata donnees_demo
python manage.py runserver
```

L'application est disponible sur http://127.0.0.1:8000. Sous Windows, l'environnement s'active avec `env\Scripts\activate`.

Le projet peut aussi être ouvert dans GitHub Codespaces : l'installation, la base de démo et le serveur sont lancés automatiquement.

[![Ouvrir dans GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ndeyemaguette-kane09/Exam_python)

Pour l'interface d'administration (`/admin`), créer un compte avec `python manage.py createsuperuser`.

## Tests

```bash
cd monmenus
python manage.py test menuapp
```

## Configuration

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | Clé secrète Django |
| `DJANGO_DEBUG` | `1` en développement, `0` en production |
| `DJANGO_ALLOWED_HOSTS` | Domaines autorisés, séparés par des virgules |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origines HTTPS autorisées pour les formulaires |

Sans ces variables, les valeurs par défaut conviennent au développement local.

## Technologies

Django 5.2, SQLite, Bootstrap 5, Tabler Icons, xhtml2pdf
