from django.db import migrations

QUANTITES = {
    'pâtes au pesto': {'sel': 5, 'poivre': 1, 'ail': 5, 'pesto': 50, 'spaghetti': 200},
    'riz au boeuf sauté': {'boeuf': 300, 'riz': 200, 'huile': 0.03, 'moutarde': 10, 'sel': 5, 'poivre': 2, 'piment': 2, 'oignons': 150},
    'omelette aux champignons': {'huile': 0.01, 'sel': 2, 'oeufs': 3, 'poivre': 1, 'champignons': 150},
    'steak frites maison': {'huile': 0.2, 'sel': 5, 'poivre': 2, 'piment': 1, 'steak': 2, 'pomme de terre': 400},
    'djolof rice (riz wolof)': {'riz': 300, 'huile': 0.05, 'sel': 5, 'poivre': 2, 'piment': 2, 'oignons': 150, 'ail': 10, 'poisson': 1, 'cube maggi': 2, 'poivron rouge': 1, 'tomate concentrée': 70},
    'bowl “yassa light”': {'riz': 100, 'poivre': 1, 'piment': 1, 'oignons': 200, 'ail': 5, 'poisson': 1, 'cube maggi': 1, 'poivron rouge': 0.5, 'tomate cerise': 100, 'citron': 2, 'quinoa': 150, 'carottes': 1, 'concombre': 1},
    'pâtes au thon et sauce tomate': {'huile': 0.02, 'sel': 5, 'poivre': 1, 'oignons': 100, 'ail': 5, 'cube maggi': 1, 'tomate concentrée': 70, 'spaghetti': 200, 'thon': 1, 'herbes de provence': 2},
    'pâtes façon carbonara': {'sel': 5, 'oeufs': 2, 'poivre': 2, 'ail': 5, 'spaghetti': 200, 'fromage râpé': 50, 'jambon de boeuf': 4},
    'riz sauté veggie aux œufs': {'riz': 200, 'sel': 3, 'oeufs': 2, 'poivre': 1, 'piment': 1, 'oignons': 50, 'ail': 5, 'poivron rouge': 0.5, 'carottes': 1},
}


def seuil_par_defaut(ingredient):
    unite = ingredient.unite.strip().lower()
    if unite in ('g', 'gr', 'grammes'):
        return 10 if ingredient.categorie == 'Épices' else 100
    if unite in ('kg',):
        return 0.2
    if unite in ('l', 'litre', 'litres'):
        return 0.25
    if unite in ('ml', 'cl'):
        return 100 if unite == 'ml' else 10
    return 1


def reprendre(apps, schema_editor):
    Recette = apps.get_model('menuapp', 'Recette')
    Ingredient = apps.get_model('menuapp', 'Ingredient')
    RecetteIngredient = apps.get_model('menuapp', 'RecetteIngredient')

    for ingredient in Ingredient.objects.all():
        ingredient.seuil_alerte = seuil_par_defaut(ingredient)
        ingredient.save(update_fields=['seuil_alerte'])

    for recette in Recette.objects.all():
        quantites = QUANTITES.get(recette.nom.strip().lower(), {})
        for ingredient in recette.ingredients.all():
            RecetteIngredient.objects.get_or_create(
                recette=recette,
                ingredient=ingredient,
                defaults={'quantite': quantites.get(ingredient.nom.strip().lower(), 1)},
            )


def annuler(apps, schema_editor):
    RecetteIngredient = apps.get_model('menuapp', 'RecetteIngredient')
    for ligne in RecetteIngredient.objects.all():
        ligne.recette.ingredients.add(ligne.ingredient)


class Migration(migrations.Migration):

    dependencies = [
        ('menuapp', '0008_quantites_planning'),
    ]

    operations = [
        migrations.RunPython(reprendre, annuler),
    ]
