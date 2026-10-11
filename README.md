# ÉquiTable 🍽️

Des menus sains, sans se ruiner. ÉquiTable gère ce qu'il y a dans ton frigo et ton placard, te propose des recettes (dont des classiques sénégalais comme le Djolof Rice ou le Yassa) et met ton stock à jour quand tu cuisines.

Projet Django réalisé à l'origine pour l'examen de Python, repris et amélioré depuis.

## Fonctionnalités

- **Frigo & Placard** : ajout, modification, suppression d'ingrédients, avec catégorie, unité et lieu de stockage
- **Ruptures de stock** signalées sur l'accueil et sur les fiches
- **Recettes** avec photo, coût estimé (FCFA) et temps de préparation
- **Générer un menu** : une recette tirée au hasard
- **Cuisiner une recette** : tu indiques les quantités utilisées, le stock est décrémenté et la recette part dans l'historique
- **Favoris**, **historique** et **export PDF** d'une recette

## Lancer le projet

```bash
python3 -m venv env
source env/bin/activate        # Windows : env\Scripts\activate
pip install -r requirements.txt

cd monmenus
python manage.py migrate
python manage.py loaddata donnees_demo
python manage.py runserver
```

Puis ouvre http://127.0.0.1:8000.

Pour accéder à l'admin Django (`/admin`) : `python manage.py createsuperuser`.

## Tests

```bash
cd monmenus
python manage.py test menuapp
```

## Configuration

Les valeurs par défaut conviennent au développement local. En dehors, définis :

| Variable | Rôle |
|---|---|
| `DJANGO_SECRET_KEY` | clé secrète Django |
| `DJANGO_DEBUG` | `1` en dev, `0` en production |
| `DJANGO_ALLOWED_HOSTS` | domaines autorisés, séparés par des virgules |

## Stack

Django 5.2 · SQLite · Bootstrap 5 · xhtml2pdf
