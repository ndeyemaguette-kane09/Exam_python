from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Favori, Historique, Ingredient, Recette, RecetteIngredient, Repas


class Donnees(TestCase):
    def setUp(self):
        self.riz = Ingredient.objects.create(nom='riz', quantite=500, unite='g', categorie='Riz', lieu='Placard', seuil_alerte=100)
        self.oeufs = Ingredient.objects.create(nom='oeufs', quantite=6, unite='pièces', categorie='Œufs', lieu='Frigo', seuil_alerte=2)
        self.ail = Ingredient.objects.create(nom='Ail', quantite=0, unite='g', lieu='Placard')
        self.recette = Recette.objects.create(nom='Riz sauté', cout_estime=1500, temps_preparation=20,
                                              instructions="Étapes :\n1️⃣ cuire le riz\n\n- ajouter les œufs")
        RecetteIngredient.objects.create(recette=self.recette, ingredient=self.riz, quantite=200)
        RecetteIngredient.objects.create(recette=self.recette, ingredient=self.oeufs, quantite=2)
        self.autre = Recette.objects.create(nom='Riz à l’ail', cout_estime=800, temps_preparation=10, instructions='Cuire.')
        RecetteIngredient.objects.create(recette=self.autre, ingredient=self.riz, quantite=100)
        RecetteIngredient.objects.create(recette=self.autre, ingredient=self.ail, quantite=10)


class ModeleTests(Donnees):
    def test_statut_du_stock(self):
        self.assertEqual(self.riz.statut, 'ok')
        self.assertEqual(self.ail.statut, 'rupture')
        self.oeufs.quantite = 2
        self.assertEqual(self.oeufs.statut, 'bas')

    def test_faisabilite(self):
        self.assertTrue(self.recette.faisabilite()['faisable'])
        etat = self.autre.faisabilite()
        self.assertFalse(etat['faisable'])
        self.assertEqual(etat['score'], 50)
        self.assertEqual([l.ingredient for l in etat['manquants']], [self.ail])
        self.assertEqual(etat['manquants'][0].manque, 10)

    def test_etapes_nettoyees(self):
        self.assertEqual(self.recette.etapes, ['Cuire le riz', 'Ajouter les œufs'])


class PagesTests(Donnees):
    def test_pages_principales(self):
        for nom in ['accueil', 'frigo', 'placard', 'recettes', 'creer_recette', 'generer_menu',
                    'planning', 'historique', 'mes_favoris']:
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200, nom)
        for nom in ['detail_recette', 'modifier_recette', 'supprimer_recette', 'confirmer_recette']:
            self.assertEqual(self.client.get(reverse(nom, args=[self.recette.id])).status_code, 200, nom)

    def test_inexistant_404(self):
        for nom in ['detail_recette', 'confirmer_recette', 'export_pdf', 'modifier_recette']:
            self.assertEqual(self.client.get(reverse(nom, args=[999])).status_code, 404, nom)
        self.assertEqual(self.client.get(reverse('modifier_ingredient', args=[999])).status_code, 404)

    def test_accueil_signale_les_alertes(self):
        reponse = self.client.get(reverse('accueil'))
        self.assertEqual(reponse.context['nb_faisables'], 1)
        self.assertEqual(reponse.context['ingredients_rupture'], [self.ail])


class StockTests(Donnees):
    def test_frigo_et_placard_separes(self):
        frigo = self.client.get(reverse('frigo'))
        self.assertContains(frigo, 'oeufs')
        self.assertNotContains(frigo, '>riz<')

    def test_ajout_ingredient(self):
        reponse = self.client.post(reverse('ajouter_ingredient'), {
            'nom': ' lait ', 'quantite': '1', 'unite': 'L', 'seuil_alerte': '0.5',
            'categorie': 'Produits laitiers', 'lieu': 'Frigo',
        })
        self.assertRedirects(reponse, reverse('frigo'))
        self.assertTrue(Ingredient.objects.filter(nom='lait', seuil_alerte=0.5).exists())

    def test_quantite_invalide_refusee(self):
        for valeur in ['abc', '-3', '']:
            reponse = self.client.post(reverse('ajouter_ingredient'), {'nom': 'x', 'quantite': valeur, 'seuil_alerte': '0', 'lieu': 'Frigo'})
            self.assertEqual(reponse.status_code, 200, valeur)
        self.assertFalse(Ingredient.objects.filter(nom='x').exists())

    def test_ingredient_utilise_non_supprimable(self):
        reponse = self.client.post(reverse('supprimer_ingredient', args=[self.riz.id]))
        self.assertRedirects(reponse, reverse('placard'))
        self.assertTrue(Ingredient.objects.filter(id=self.riz.id).exists())

    def test_ingredient_libre_supprimable(self):
        sel = Ingredient.objects.create(nom='sel', quantite=10, unite='g', lieu='Placard')
        self.client.post(reverse('supprimer_ingredient', args=[sel.id]))
        self.assertFalse(Ingredient.objects.filter(id=sel.id).exists())


class RecetteTests(Donnees):
    def donnees_formulaire(self, **extra):
        donnees = {
            'nom': 'Omelette', 'cout_estime': '700', 'temps_preparation': '10', 'portions': '1',
            'instructions': 'Battre\nCuire',
            'lignes-TOTAL_FORMS': '2', 'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-ingredient': str(self.oeufs.id), 'lignes-0-quantite': '3',
            'lignes-1-ingredient': '', 'lignes-1-quantite': '',
        }
        donnees.update(extra)
        return donnees

    def test_creer_recette(self):
        reponse = self.client.post(reverse('creer_recette'), self.donnees_formulaire())
        recette = Recette.objects.get(nom='Omelette')
        self.assertRedirects(reponse, reverse('detail_recette', args=[recette.id]))
        self.assertEqual(recette.lignes.get().quantite, 3)

    def test_recette_sans_ingredient_refusee(self):
        self.client.post(reverse('creer_recette'), self.donnees_formulaire(**{'lignes-0-ingredient': '', 'lignes-0-quantite': ''}))
        self.assertFalse(Recette.objects.filter(nom='Omelette').exists())

    def test_ingredient_en_double_refuse(self):
        self.client.post(reverse('creer_recette'), self.donnees_formulaire(**{
            'lignes-1-ingredient': str(self.oeufs.id), 'lignes-1-quantite': '1'}))
        self.assertFalse(Recette.objects.filter(nom='Omelette').exists())

    def test_modifier_recette(self):
        lignes = list(self.recette.lignes.all())
        donnees = {
            'nom': 'Riz sauté maison', 'cout_estime': '1500', 'temps_preparation': '25', 'portions': '2',
            'instructions': 'Cuire',
            'lignes-TOTAL_FORMS': '2', 'lignes-INITIAL_FORMS': '2',
            'lignes-MIN_NUM_FORMS': '0', 'lignes-MAX_NUM_FORMS': '1000',
        }
        for i, ligne in enumerate(lignes):
            donnees.update({f'lignes-{i}-id': str(ligne.id), f'lignes-{i}-recette': str(self.recette.id),
                            f'lignes-{i}-ingredient': str(ligne.ingredient_id), f'lignes-{i}-quantite': str(ligne.quantite)})
        donnees['lignes-1-DELETE'] = 'on'
        self.client.post(reverse('modifier_recette', args=[self.recette.id]), donnees)
        self.recette.refresh_from_db()
        self.assertEqual(self.recette.nom, 'Riz sauté maison')
        self.assertEqual(self.recette.lignes.count(), 1)

    def test_supprimer_recette(self):
        self.client.post(reverse('supprimer_recette', args=[self.autre.id]))
        self.assertFalse(Recette.objects.filter(id=self.autre.id).exists())
        self.assertTrue(Ingredient.objects.filter(id=self.ail.id).exists())

    def test_filtres(self):
        reponse = self.client.get(reverse('recettes'), {'faisable': '1'})
        self.assertEqual([r.nom for r in reponse.context['recettes']], ['Riz sauté'])
        reponse = self.client.get(reverse('recettes'), {'budget': '1000'})
        self.assertEqual([r.nom for r in reponse.context['recettes']], ['Riz à l’ail'])
        reponse = self.client.get(reverse('recettes'), {'q': 'oeuf'})
        self.assertEqual([r.nom for r in reponse.context['recettes']], ['Riz sauté'])

    def test_generer_menu_privilegie_le_stock(self):
        for _ in range(10):
            reponse = self.client.get(reverse('generer_menu'))
            self.assertEqual(reponse.context['recette'], self.recette)

    def test_confirmation_prerremplie_et_decremente(self):
        page = self.client.get(reverse('confirmer_recette', args=[self.recette.id]))
        self.assertContains(page, f'name="quantite_{self.riz.id}" value="200"')
        self.client.post(reverse('confirmer_recette', args=[self.recette.id]), {
            f'quantite_{self.riz.id}': '200', f'quantite_{self.oeufs.id}': '',
        })
        self.riz.refresh_from_db()
        self.oeufs.refresh_from_db()
        self.assertEqual(self.riz.quantite, 300)
        self.assertEqual(self.oeufs.quantite, 6)
        self.assertEqual(Historique.objects.count(), 1)

    def test_stock_jamais_negatif(self):
        self.client.post(reverse('confirmer_recette', args=[self.recette.id]), {f'quantite_{self.riz.id}': '9999'})
        self.riz.refresh_from_db()
        self.assertEqual(self.riz.quantite, 0)

    def test_saisie_invalide_ne_touche_pas_au_stock(self):
        self.client.post(reverse('confirmer_recette', args=[self.recette.id]), {f'quantite_{self.riz.id}': 'beaucoup'})
        self.riz.refresh_from_db()
        self.assertEqual(self.riz.quantite, 500)
        self.assertEqual(Historique.objects.count(), 0)

    def test_favori_bascule_sans_doublon(self):
        url = reverse('basculer_favori', args=[self.recette.id])
        self.client.post(url)
        self.assertEqual(Favori.objects.count(), 1)
        self.client.post(url, {'next': reverse('mes_favoris')})
        self.assertEqual(Favori.objects.count(), 0)
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_favori_refuse_redirection_externe(self):
        reponse = self.client.post(reverse('basculer_favori', args=[self.recette.id]), {'next': 'https://exemple.com/'})
        self.assertRedirects(reponse, reverse('detail_recette', args=[self.recette.id]))

    def test_export_pdf(self):
        reponse = self.client.get(reverse('export_pdf', args=[self.recette.id]))
        self.assertEqual(reponse['Content-Type'], 'application/pdf')
        self.assertTrue(reponse.content.startswith(b'%PDF'))


class HistoriqueTests(Donnees):
    def test_statistiques(self):
        Historique.objects.create(recette=self.recette)
        Historique.objects.create(recette=self.recette)
        ancien = Historique.objects.create(recette=self.autre)
        Historique.objects.filter(id=ancien.id).update(date_validation=timezone.now() - timedelta(days=400))
        reponse = self.client.get(reverse('historique'))
        self.assertEqual(reponse.context['nb_total'], 3)
        self.assertEqual(reponse.context['nb_mois'], 2)
        self.assertEqual(reponse.context['budget_mois'], 3000)
        self.assertEqual(reponse.context['top']['recette__nom'], 'Riz sauté')


class PlanningTests(Donnees):
    def test_planifier_remplacer_retirer(self):
        jour = timezone.localdate()
        self.client.post(reverse('planifier_repas'), {'date': jour.isoformat(), 'moment': 'diner', 'recette': self.recette.id})
        self.client.post(reverse('planifier_repas'), {'date': jour.isoformat(), 'moment': 'diner', 'recette': self.autre.id})
        repas = Repas.objects.get()
        self.assertEqual(repas.recette, self.autre)
        self.client.post(reverse('retirer_repas', args=[repas.id]))
        self.assertFalse(Repas.objects.exists())

    def test_liste_de_courses_de_la_semaine(self):
        lundi = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        for i in range(3):
            Repas.objects.create(date=lundi + timedelta(days=i), moment='dejeuner', recette=self.recette)
        Repas.objects.create(date=lundi, moment='diner', recette=self.autre)
        Repas.objects.create(date=lundi + timedelta(days=7), moment='diner', recette=self.autre)
        reponse = self.client.get(reverse('planning'), {'semaine': lundi.isoformat()})
        courses = {c['ingredient'].nom: c['manque'] for c in reponse.context['courses']}
        self.assertEqual(courses, {'riz': 200, 'Ail': 10})
        self.assertEqual(reponse.context['nb_repas'], 4)
        self.assertEqual(reponse.context['budget'], 3 * 1500 + 800)

    def test_semaine_invalide_retombe_sur_la_semaine_courante(self):
        reponse = self.client.get(reverse('planning'), {'semaine': 'nimporte'})
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.context['lundi'].weekday(), 0)
