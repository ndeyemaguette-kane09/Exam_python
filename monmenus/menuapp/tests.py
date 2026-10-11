from django.test import TestCase
from django.urls import reverse

from .models import Favori, Historique, Ingredient, Recette


class StockTests(TestCase):
    def setUp(self):
        self.riz = Ingredient.objects.create(nom='riz', quantite=500, unite='g', categorie='Riz', lieu='Placard')
        self.oeufs = Ingredient.objects.create(nom='oeufs', quantite=6, unite='pièces', categorie='Œufs', lieu='Frigo')

    def test_pages_principales(self):
        for nom in ['accueil', 'frigo', 'placard', 'recettes', 'generer_menu', 'historique', 'mes_favoris']:
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200, nom)

    def test_frigo_et_placard_separes(self):
        frigo = self.client.get(reverse('frigo'))
        self.assertContains(frigo, 'oeufs')
        self.assertNotContains(frigo, 'riz')

    def test_ajout_ingredient(self):
        reponse = self.client.post(reverse('ajouter_ingredient'), {
            'nom': ' lait ', 'quantite': '1', 'unite': 'L', 'categorie': 'Produits laitiers', 'lieu': 'Frigo',
        })
        self.assertRedirects(reponse, reverse('frigo'))
        self.assertTrue(Ingredient.objects.filter(nom='lait', lieu='Frigo').exists())

    def test_quantite_invalide_refusee(self):
        for valeur in ['abc', '-3', '']:
            reponse = self.client.post(reverse('ajouter_ingredient'), {'nom': 'x', 'quantite': valeur, 'lieu': 'Frigo'})
            self.assertEqual(reponse.status_code, 200, valeur)
        self.assertFalse(Ingredient.objects.filter(nom='x').exists())

    def test_modification_conserve_unite_et_categorie(self):
        self.client.post(reverse('modifier_ingredient', args=[self.riz.id]), {
            'nom': 'riz', 'quantite': '300', 'unite': 'g', 'categorie': 'Riz', 'lieu': 'Placard',
        })
        self.riz.refresh_from_db()
        self.assertEqual((self.riz.quantite, self.riz.unite, self.riz.categorie), (300, 'g', 'Riz'))

    def test_suppression_redirige_vers_le_bon_lieu(self):
        reponse = self.client.post(reverse('supprimer_ingredient', args=[self.riz.id]))
        self.assertRedirects(reponse, reverse('placard'))

    def test_ingredient_inexistant_404(self):
        self.assertEqual(self.client.get(reverse('modifier_ingredient', args=[999])).status_code, 404)


class RecetteTests(TestCase):
    def setUp(self):
        self.riz = Ingredient.objects.create(nom='riz', quantite=500, unite='g', lieu='Placard')
        self.oeufs = Ingredient.objects.create(nom='oeufs', quantite=6, unite='pièces', lieu='Frigo')
        self.recette = Recette.objects.create(nom='Riz sauté', cout_estime=1500, temps_preparation=20, instructions='Cuire.')
        self.recette.ingredients.add(self.riz, self.oeufs)

    def test_recette_inexistante_404(self):
        for nom in ['detail_recette', 'confirmer_recette', 'export_pdf']:
            self.assertEqual(self.client.get(reverse(nom, args=[999])).status_code, 404, nom)

    def test_confirmation_decremente_le_stock(self):
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
        self.client.post(url)
        self.assertEqual(Favori.objects.count(), 0)
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_export_pdf(self):
        reponse = self.client.get(reverse('export_pdf', args=[self.recette.id]))
        self.assertEqual(reponse['Content-Type'], 'application/pdf')
        self.assertTrue(reponse.content.startswith(b'%PDF'))
