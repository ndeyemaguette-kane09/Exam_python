# ÉquiTable 🍽️

Des menus sains, sans se ruiner. ÉquiTable gère ce qu'il y a dans ton frigo et ton placard, te propose des recettes (dont des classiques sénégalais comme le Djolof Rice ou le Yassa) et met ton stock à jour quand tu cuisines.

Projet Django réalisé à l'origine pour l'examen de Python, repris et amélioré depuis.

## Fonctionnalités

- **Frigo & Placard** : ingrédients rangés par catégorie, avec unité, lieu et seuil de stock bas
- **Alertes** : l'accueil signale ce qui est en rupture et ce qui va bientôt manquer
- **Recettes** avec photo, coût (FCFA), temps, portions et quantités par ingrédient ; ajout, modification et suppression depuis l'appli
- **Faisabilité** : chaque recette indique si elle est faisable avec ton stock, et ce qu'il manque
- **Recherche et filtres** par nom, ingrédient, budget, temps ou « faisable maintenant »
- **Que cuisiner ?** : une suggestion en priorité avec ce que tu as déjà, ou au hasard
- **Cuisiner une recette** : les quantités sont pré-remplies, le stock est décrémenté et le repas part dans l'historique
- **Planning de la semaine** (déjeuner et dîner) avec liste de courses globale et budget estimé
- **Historique** en tableau de bord : repas et budget du mois, recette la plus cuisinée, chronologie
- **Favoris**, **export PDF** mis en page et partage WhatsApp de la liste de courses

## Tester sans rien installer

[![Ouvrir dans GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/ndeyemaguette-kane09/Exam_python)

Codespaces installe les dépendances, crée la base avec les données de démo et lance le serveur tout seul. L'appli s'ouvre dans un nouvel onglet au bout d'une minute environ. Si l'onglet ne s'ouvre pas, va dans l'onglet **Ports** de VS Code et clique sur l'icône 🌐 du port 8000.

Pense à arrêter le Codespace quand tu as fini (menu **Codespaces → Stop Current Codespace**) pour ne pas consommer ton quota.

## Lancer le projet en local

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
| `DJANGO_CSRF_TRUSTED_ORIGINS` | origines HTTPS de confiance pour les formulaires, séparées par des virgules |

## Stack

Django 5.2 · SQLite · Bootstrap 5 · Tabler Icons · xhtml2pdf
