import os

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from .forms import IngredientForm
from .models import Favori, Historique, Ingredient, Recette

PAGES_STOCK = {'Frigo': 'frigo', 'Placard': 'placard'}


def accueil(request):
    total_ingredients = Ingredient.objects.count()
    ingredients_rupture = Ingredient.objects.filter(quantite__lte=0)
    return render(request, 'menuapp/accueil.html', {
        'total_ingredients': total_ingredients,
        'ingredients_rupture': ingredients_rupture
    })


def stock(request, lieu):
    ingredients = Ingredient.objects.filter(lieu=lieu).order_by('categorie', 'nom')
    return render(request, 'menuapp/stock.html', {'ingredients': ingredients, 'lieu': lieu})


def ajouter_ingredient(request, lieu):
    form = IngredientForm(request.POST or None, initial={'lieu': lieu})
    if request.method == 'POST' and form.is_valid():
        ingredient = form.save()
        messages.success(request, f"{ingredient.nom} ajouté ✅")
        return redirect(PAGES_STOCK[ingredient.lieu])
    return render(request, 'menuapp/ingredient_form.html', {
        'form': form,
        'titre': f"Ajouter un ingrédient — {lieu}",
        'retour': PAGES_STOCK[lieu],
    })


def modifier_ingredient(request, id):
    ingredient = get_object_or_404(Ingredient, id=id)
    retour = PAGES_STOCK[ingredient.lieu]
    form = IngredientForm(request.POST or None, instance=ingredient)
    if request.method == 'POST' and form.is_valid():
        ingredient = form.save()
        messages.success(request, f"{ingredient.nom} mis à jour ✅")
        return redirect(PAGES_STOCK[ingredient.lieu])
    return render(request, 'menuapp/ingredient_form.html', {
        'form': form,
        'titre': f"Modifier {form.initial.get('nom', '')}",
        'retour': retour,
    })


def supprimer_ingredient(request, id):
    ingredient = get_object_or_404(Ingredient, id=id)
    retour = PAGES_STOCK[ingredient.lieu]
    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, f"{ingredient.nom} supprimé")
        return redirect(retour)
    return render(request, 'menuapp/supprimer_ingredient.html', {'ingredient': ingredient, 'retour': retour})


def recettes(request):
    recettes = Recette.objects.all()
    return render(request, 'menuapp/recettes.html', {'recettes': recettes})


def detail_recette(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    est_favori = Favori.objects.filter(recette=recette).exists()
    return render(request, 'menuapp/detail_recette.html', {'recette': recette, 'est_favori': est_favori})


def generer_menu(request):
    recette = Recette.objects.order_by('?').first()
    return render(request, 'menuapp/generer_menu.html', {'recette': recette})


def lien_media_pdf(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        chemin = os.path.join(settings.MEDIA_ROOT, uri.removeprefix(settings.MEDIA_URL))
        if os.path.isfile(chemin):
            return chemin
    return uri


def export_pdf(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    html = get_template('menuapp/pdf_template.html').render({'recette': recette})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="menu_{slugify(recette.nom)}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=lien_media_pdf)
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    return response


def lire_quantite(valeur):
    try:
        return max(float(valeur.replace(',', '.')), 0)
    except ValueError:
        return None


def confirmer_recette(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    ingredients = recette.ingredients.all()

    if request.method == 'POST':
        quantites = {}
        erreurs = []
        for ing in ingredients:
            saisie = request.POST.get(f'quantite_{ing.id}', '').strip()
            qte = lire_quantite(saisie) if saisie else 0
            if qte is None:
                erreurs.append(ing.nom)
            quantites[ing] = qte

        if erreurs:
            messages.error(request, "Quantité invalide pour : " + ", ".join(erreurs))
        else:
            for ing, qte_utilisee in quantites.items():
                ing.quantite = max(ing.quantite - qte_utilisee, 0)
                ing.save()
            # ➜ Enregistre l’action dans Historique ✅
            Historique.objects.create(recette=recette)
            messages.success(request, f"{recette.nom} validée, stock mis à jour 🍽️")
            return redirect('historique')

    return render(request, 'menuapp/confirmer_recette.html', {
        'recette': recette,
        'ingredients': ingredients
    })


def historique(request):
    historiques = Historique.objects.select_related('recette').order_by('-date_validation')
    return render(request, 'menuapp/historique.html', {'historiques': historiques})


@require_POST
def basculer_favori(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    supprimes, _ = Favori.objects.filter(recette=recette).delete()
    if supprimes:
        messages.info(request, f"{recette.nom} retirée des favoris")
    else:
        Favori.objects.create(recette=recette)
        messages.success(request, f"{recette.nom} ajoutée aux favoris ❤️")
    return redirect('detail_recette', recette_id=recette.id)


def mes_favoris(request):
    favoris = Favori.objects.select_related('recette').order_by('-date_ajout')
    return render(request, 'menuapp/mes_favoris.html', {'favoris': favoris})
