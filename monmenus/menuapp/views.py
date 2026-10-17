import base64
import io
import os
import random
from collections import defaultdict
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db import transaction
from django.db.models import Count, ProtectedError, Sum
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps
from xhtml2pdf import pisa

from .forms import IngredientForm, LignesFormSet, RecetteForm, RepasForm
from .models import Favori, Historique, Ingredient, Recette, Repas

PAGES_STOCK = {'Frigo': 'frigo', 'Placard': 'placard'}


def recettes_avec_faisabilite(queryset=None):
    queryset = queryset if queryset is not None else Recette.objects.all()
    recettes = list(queryset.prefetch_related('lignes__ingredient'))
    for recette in recettes:
        recette.etat = recette.faisabilite()
    return recettes


def redirection_suivante(request, defaut, **kwargs):
    suivante = request.POST.get('next') or request.GET.get('next')
    if suivante and url_has_allowed_host_and_scheme(suivante, allowed_hosts={request.get_host()}):
        return redirect(suivante)
    return redirect(defaut, **kwargs)


def debut_semaine(jour):
    return jour - timedelta(days=jour.weekday())


def accueil(request):
    ingredients = list(Ingredient.objects.all())
    ruptures = [i for i in ingredients if i.en_rupture]
    stocks_bas = [i for i in ingredients if i.stock_bas]
    recettes = recettes_avec_faisabilite()
    faisables = [r for r in recettes if r.etat['faisable']]
    aujourd_hui = timezone.localdate()
    return render(request, 'menuapp/accueil.html', {
        'total_ingredients': len(ingredients),
        'ingredients_rupture': ruptures,
        'ingredients_bas': stocks_bas,
        'nb_faisables': len(faisables),
        'nb_recettes': len(recettes),
        'suggestion': random.choice(faisables) if faisables else None,
        'repas_du_jour': Repas.objects.filter(date=aujourd_hui).select_related('recette'),
    })


def stock(request, lieu):
    ingredients = list(Ingredient.objects.filter(lieu=lieu).order_by('categorie', Lower('nom')))
    return render(request, 'menuapp/stock.html', {
        'ingredients': ingredients,
        'lieu': lieu,
        'nb_alertes': sum(1 for i in ingredients if i.statut != 'ok'),
    })


def ajouter_ingredient(request, lieu):
    form = IngredientForm(request.POST or None, initial={'lieu': lieu})
    if request.method == 'POST' and form.is_valid():
        ingredient = form.save()
        messages.success(request, f"{ingredient} ajouté")
        return redirect(PAGES_STOCK[ingredient.lieu])
    return render(request, 'menuapp/ingredient_form.html', {
        'form': form,
        'titre': "Ajouter un ingrédient",
        'sous_titre': f"Dans ton {lieu.lower()}",
        'retour': PAGES_STOCK[lieu],
    })


def modifier_ingredient(request, id):
    ingredient = get_object_or_404(Ingredient, id=id)
    retour = PAGES_STOCK[ingredient.lieu]
    nom = str(ingredient)
    form = IngredientForm(request.POST or None, instance=ingredient)
    if request.method == 'POST' and form.is_valid():
        ingredient = form.save()
        messages.success(request, f"{ingredient} mis à jour")
        return redirect(PAGES_STOCK[ingredient.lieu])
    return render(request, 'menuapp/ingredient_form.html', {
        'form': form,
        'titre': f"Modifier {nom}",
        'retour': retour,
    })


def supprimer_ingredient(request, id):
    ingredient = get_object_or_404(Ingredient, id=id)
    retour = PAGES_STOCK[ingredient.lieu]
    recettes = Recette.objects.filter(lignes__ingredient=ingredient).distinct()
    if request.method == 'POST':
        try:
            ingredient.delete()
        except ProtectedError:
            messages.error(request, f"{ingredient} est utilisé dans une recette. Mets sa quantité à 0 pour le marquer en rupture.")
            return redirect(retour)
        messages.success(request, f"{ingredient} supprimé")
        return redirect(retour)
    return render(request, 'menuapp/supprimer_ingredient.html', {
        'ingredient': ingredient,
        'retour': retour,
        'recettes': recettes,
    })


def recettes(request):
    q = request.GET.get('q', '').strip()
    budget = request.GET.get('budget', '')
    temps = request.GET.get('temps', '')
    faisable = request.GET.get('faisable') == '1'
    tri = request.GET.get('tri', 'nom')

    queryset = Recette.objects.all()
    if q:
        queryset = queryset.filter(nom__icontains=q) | queryset.filter(lignes__ingredient__nom__icontains=q)
        queryset = queryset.distinct()
    if budget.isdigit():
        queryset = queryset.filter(cout_estime__lte=int(budget))
    if temps.isdigit():
        queryset = queryset.filter(temps_preparation__lte=int(temps))

    liste = recettes_avec_faisabilite(queryset)
    if faisable:
        liste = [r for r in liste if r.etat['faisable']]

    tris = {
        'nom': lambda r: r.nom.lower(),
        'cout': lambda r: r.cout_estime,
        'temps': lambda r: r.temps_preparation,
        'stock': lambda r: -r.etat['score'],
    }
    liste.sort(key=tris.get(tri, tris['nom']))

    favoris = set(Favori.objects.values_list('recette_id', flat=True))
    return render(request, 'menuapp/recettes.html', {
        'recettes': liste,
        'favoris': favoris,
        'filtres': {'q': q, 'budget': budget, 'temps': temps, 'faisable': faisable, 'tri': tri},
        'filtre_actif': bool(q or budget or temps or faisable),
    })


def detail_recette(request, recette_id):
    recette = get_object_or_404(Recette.objects.prefetch_related('lignes__ingredient'), id=recette_id)
    return render(request, 'menuapp/detail_recette.html', {
        'recette': recette,
        'etat': recette.faisabilite(),
        'est_favori': Favori.objects.filter(recette=recette).exists(),
        'nb_cuisinee': Historique.objects.filter(recette=recette).count(),
        'repas_form': RepasForm(initial={
            'date': timezone.localdate(),
            'moment': 'dejeuner' if timezone.localtime().hour < 15 else 'diner',
            'recette': recette,
        }),
    })


def formulaire_recette(request, recette=None):
    form = RecetteForm(request.POST or None, request.FILES or None, instance=recette)
    lignes = LignesFormSet(request.POST or None, instance=recette or Recette(), prefix='lignes')
    if request.method == 'POST' and form.is_valid() and lignes.is_valid():
        with transaction.atomic():
            recette = form.save()
            lignes.instance = recette
            lignes.save()
        messages.success(request, f"{recette.nom} enregistrée")
        return redirect('detail_recette', recette_id=recette.id)
    return render(request, 'menuapp/recette_form.html', {
        'form': form,
        'lignes': lignes,
        'recette': recette,
        'aucun_ingredient': not Ingredient.objects.exists(),
    })


def creer_recette(request):
    return formulaire_recette(request)


def modifier_recette(request, recette_id):
    return formulaire_recette(request, get_object_or_404(Recette, id=recette_id))


def supprimer_recette(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    if request.method == 'POST':
        recette.delete()
        messages.success(request, f"{recette.nom} supprimée")
        return redirect('recettes')
    return render(request, 'menuapp/supprimer_recette.html', {
        'recette': recette,
        'nb_historique': Historique.objects.filter(recette=recette).count(),
        'nb_repas': recette.repas.count(),
    })


def generer_menu(request):
    mode = request.GET.get('mode', 'stock')
    exclure = request.GET.get('exclure', '')
    recettes = recettes_avec_faisabilite()
    if exclure.isdigit() and len(recettes) > 1:
        recettes = [r for r in recettes if r.id != int(exclure)]

    candidates = recettes
    if mode == 'stock' and recettes:
        meilleur = max(r.etat['score'] for r in recettes)
        candidates = [r for r in recettes if r.etat['score'] == meilleur]

    recette = random.choice(candidates) if candidates else None
    return render(request, 'menuapp/generer_menu.html', {
        'recette': recette,
        'etat': recette.etat if recette else None,
        'mode': mode,
    })


def lien_media_pdf(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        chemin = os.path.join(settings.MEDIA_ROOT, uri.removeprefix(settings.MEDIA_URL))
        if os.path.isfile(chemin):
            return chemin
    if uri.startswith(settings.STATIC_URL):
        chemin = finders.find(uri.removeprefix(settings.STATIC_URL))
        if chemin:
            return chemin
    return uri


def photo_bandeau(recette, ratio=2.2, largeur=1400):
    if not recette.image:
        return None
    try:
        with Image.open(recette.image.path) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            hauteur = round(largeur / ratio)
            image = ImageOps.fit(image, (largeur, hauteur), Image.Resampling.LANCZOS)
            tampon = io.BytesIO()
            image.save(tampon, format='JPEG', quality=82)
    except (OSError, ValueError):
        return None
    return 'data:image/jpeg;base64,' + base64.b64encode(tampon.getvalue()).decode()


def export_pdf(request, recette_id):
    recette = get_object_or_404(Recette.objects.prefetch_related('lignes__ingredient'), id=recette_id)
    html = get_template('menuapp/pdf_template.html').render({
        'recette': recette,
        'photo': photo_bandeau(recette),
        'date_export': timezone.localdate(),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="recette_{slugify(recette.nom)}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=lien_media_pdf, encoding='utf-8')
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
    lignes = list(recette.lignes.select_related('ingredient'))

    if request.method == 'POST':
        quantites = {}
        erreurs = []
        for ligne in lignes:
            saisie = request.POST.get(f'quantite_{ligne.ingredient_id}', '').strip()
            qte = lire_quantite(saisie) if saisie else 0
            if qte is None:
                erreurs.append(str(ligne.ingredient))
            quantites[ligne.ingredient] = qte

        if erreurs:
            messages.error(request, "Quantité invalide pour : " + ", ".join(erreurs))
        else:
            with transaction.atomic():
                for ing, qte_utilisee in quantites.items():
                    ing.quantite = max(ing.quantite - qte_utilisee, 0)
                    ing.save(update_fields=['quantite'])
                # ➜ Enregistre l’action dans Historique ✅
                Historique.objects.create(recette=recette)
            messages.success(request, f"{recette.nom} : stock mis à jour")
            return redirect('historique')

    return render(request, 'menuapp/confirmer_recette.html', {
        'recette': recette,
        'lignes': lignes,
    })


def historique(request):
    maintenant = timezone.localtime()
    debut_mois = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    historiques = Historique.objects.select_related('recette').order_by('-date_validation')
    du_mois = historiques.filter(date_validation__gte=debut_mois)

    top = (
        Historique.objects.values('recette__id', 'recette__nom')
        .annotate(nb=Count('id'))
        .order_by('-nb', 'recette__nom')
        .first()
    )
    entrees = list(historiques)
    for entree in entrees:
        entree.jour = timezone.localtime(entree.date_validation).date()
    return render(request, 'menuapp/historique.html', {
        'historiques': entrees,
        'nb_total': len(entrees),
        'nb_mois': du_mois.count(),
        'budget_mois': du_mois.aggregate(total=Sum('recette__cout_estime'))['total'] or 0,
        'budget_total': historiques.aggregate(total=Sum('recette__cout_estime'))['total'] or 0,
        'top': top,
        'mois': maintenant,
    })


@require_POST
def basculer_favori(request, recette_id):
    recette = get_object_or_404(Recette, id=recette_id)
    supprimes, _ = Favori.objects.filter(recette=recette).delete()
    if supprimes:
        messages.info(request, f"{recette.nom} retirée des favoris")
    else:
        Favori.objects.create(recette=recette)
        messages.success(request, f"{recette.nom} ajoutée aux favoris")
    return redirection_suivante(request, 'detail_recette', recette_id=recette.id)


def mes_favoris(request):
    favoris = list(Favori.objects.select_related('recette').prefetch_related('recette__lignes__ingredient').order_by('-date_ajout'))
    for favori in favoris:
        favori.etat = favori.recette.faisabilite()
    return render(request, 'menuapp/mes_favoris.html', {'favoris': favoris})


def liste_courses(repas):
    besoins = defaultdict(float)
    ingredients = {}
    for un_repas in repas:
        for ligne in un_repas.recette.lignes.all():
            besoins[ligne.ingredient_id] += ligne.quantite
            ingredients[ligne.ingredient_id] = ligne.ingredient
    courses = []
    for ingredient_id, besoin in besoins.items():
        ingredient = ingredients[ingredient_id]
        manque = besoin - ingredient.quantite
        if manque > 1e-9:
            courses.append({'ingredient': ingredient, 'besoin': besoin, 'manque': manque})
    courses.sort(key=lambda c: (c['ingredient'].categorie or 'zz', c['ingredient'].nom.lower()))
    return courses


def planning(request):
    aujourd_hui = timezone.localdate()
    try:
        reference = date.fromisoformat(request.GET.get('semaine', ''))
    except ValueError:
        reference = aujourd_hui
    lundi = debut_semaine(reference)
    jours = [lundi + timedelta(days=i) for i in range(7)]

    repas = list(
        Repas.objects.filter(date__range=(jours[0], jours[-1]))
        .select_related('recette')
        .prefetch_related('recette__lignes__ingredient')
    )
    par_creneau = {(r.date, r.moment): r for r in repas}
    semaine = [
        {
            'date': jour,
            'aujourdhui': jour == aujourd_hui,
            'creneaux': [
                {'moment': code, 'libelle': libelle, 'repas': par_creneau.get((jour, code))}
                for code, libelle in Repas.MOMENTS
            ],
        }
        for jour in jours
    ]

    grille = [
        {
            'libelle': libelle,
            'cases': [{'jour': jour, 'creneau': jour['creneaux'][i]} for jour in semaine],
        }
        for i, (code, libelle) in enumerate(Repas.MOMENTS)
    ]

    return render(request, 'menuapp/planning.html', {
        'semaine': semaine,
        'grille': grille,
        'lundi': lundi,
        'dimanche': jours[-1],
        'precedente': lundi - timedelta(days=7),
        'suivante': lundi + timedelta(days=7),
        'courante': debut_semaine(aujourd_hui),
        'recettes': Recette.objects.all(),
        'courses': liste_courses(repas),
        'nb_repas': len(repas),
        'budget': sum(r.recette.cout_estime for r in repas),
    })


@require_POST
def planifier_repas(request):
    form = RepasForm(request.POST)
    if form.is_valid():
        repas, _ = Repas.objects.update_or_create(
            date=form.cleaned_data['date'],
            moment=form.cleaned_data['moment'],
            defaults={'recette': form.cleaned_data['recette']},
        )
        messages.success(request, f"{repas.recette} prévue pour le {repas.get_moment_display().lower()} du {repas.date:%d/%m}")
        semaine = debut_semaine(repas.date).isoformat()
    else:
        messages.error(request, "Repas non planifié : date, moment ou recette manquant.")
        semaine = ''
    if request.POST.get('next'):
        return redirection_suivante(request, 'planning')
    return redirect(f"{reverse('planning')}?semaine={semaine}" if semaine else 'planning')


@require_POST
def retirer_repas(request, repas_id):
    repas = get_object_or_404(Repas, id=repas_id)
    semaine = debut_semaine(repas.date).isoformat()
    repas.delete()
    messages.info(request, "Repas retiré du planning")
    return redirect(f"{reverse('planning')}?semaine={semaine}")
