import re

from django.db import models
from django.db.models.functions import Lower


class Ingredient(models.Model):
    CATEGORIES_CHOICES = [
    ('Légumes frais', 'Légumes frais'),
    ('Fruits frais', 'Fruits frais'),
    ('Viandes', 'Viandes'),
    ('Poissons', 'Poissons'),
    ('Produits laitiers', 'Produits laitiers'),
    ('Œufs', 'Œufs'),
    ('Charcuterie', 'Charcuterie'),
    ('Plats cuisinés', 'Plats cuisinés'),
    ('Pâtes', 'Pâtes'),
    ('Riz', 'Riz'),
    ('Légumineuses', 'Légumineuses'),
    ('Conserves', 'Conserves'),
    ('Épices', 'Épices'),
    ('Céréales', 'Céréales'),
    ('Biscuits & Snacks', 'Biscuits & Snacks'),
    ('Huiles & Vinaigres', 'Huiles & Vinaigres'),
    ('Farine & Sucre', 'Farine & Sucre'),
    ('Autre', 'Autre'),
]
    LIEU_CHOICES = [
        ('Frigo', 'Frigo'),
        ('Placard', 'Placard'),
    ]
    ICONES = {
        'Légumes frais': 'carrot',
        'Fruits frais': 'apple',
        'Viandes': 'meat',
        'Poissons': 'fish',
        'Produits laitiers': 'milk',
        'Œufs': 'egg',
        'Charcuterie': 'sausage',
        'Plats cuisinés': 'soup',
        'Pâtes': 'tools-kitchen-2',
        'Riz': 'bowl',
        'Légumineuses': 'seedling',
        'Conserves': 'package',
        'Épices': 'salt',
        'Céréales': 'wheat',
        'Biscuits & Snacks': 'cookie',
        'Huiles & Vinaigres': 'bottle',
        'Farine & Sucre': 'cake',
    }

    nom = models.CharField(max_length=100)
    quantite = models.FloatField()
    unite = models.CharField(max_length=50, blank=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES_CHOICES, blank=True)
    lieu = models.CharField(max_length=50, choices=LIEU_CHOICES, default='Frigo')
    seuil_alerte = models.FloatField(default=0)

    class Meta:
        ordering = [Lower('nom')]

    @property
    def icone(self):
        return self.ICONES.get(self.categorie, 'box')

    @property
    def en_rupture(self):
        return self.quantite <= 0

    @property
    def stock_bas(self):
        return not self.en_rupture and self.quantite <= self.seuil_alerte

    @property
    def statut(self):
        if self.en_rupture:
            return 'rupture'
        if self.stock_bas:
            return 'bas'
        return 'ok'

    def __str__(self):
        return self.nom.strip()


class Recette(models.Model):
    nom = models.CharField(max_length=100)
    cout_estime = models.FloatField()
    temps_preparation = models.IntegerField()  # En minutes
    portions = models.PositiveIntegerField(default=2)
    instructions = models.TextField()
    image = models.ImageField(upload_to='recettes/', blank=True, null=True)

    class Meta:
        ordering = [Lower('nom')]

    def __str__(self):
        return self.nom

    @property
    def etapes(self):
        etapes = []
        for ligne in self.instructions.splitlines():
            ligne = re.sub(r'^[\s\-–•*]*(\d+\s*[\.\)]|\d️?⃣)?\s*', '', ligne).strip()
            if not ligne or re.fullmatch(r'étapes\s*:?', ligne, re.IGNORECASE):
                continue
            etapes.append(ligne[0].upper() + ligne[1:])
        return etapes

    def faisabilite(self):
        lignes = list(self.lignes.all())
        manquants = [ligne for ligne in lignes if not ligne.disponible]
        total = len(lignes)
        score = round(100 * (total - len(manquants)) / total) if total else 0
        return {
            'faisable': total > 0 and not manquants,
            'score': score,
            'manquants': manquants,
            'total': total,
        }


class RecetteIngredient(models.Model):
    recette = models.ForeignKey(Recette, on_delete=models.CASCADE, related_name='lignes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name='utilisations')
    quantite = models.FloatField()

    class Meta:
        ordering = [Lower('ingredient__nom')]
        constraints = [
            models.UniqueConstraint(fields=['recette', 'ingredient'], name='ingredient_unique_par_recette'),
        ]

    @property
    def disponible(self):
        return self.ingredient.quantite >= self.quantite

    @property
    def manque(self):
        return max(self.quantite - self.ingredient.quantite, 0)

    def __str__(self):
        return f"{self.ingredient} ({self.quantite} {self.ingredient.unite})"


class Historique(models.Model):
    recette = models.ForeignKey('Recette', on_delete=models.CASCADE)
    date_validation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recette.nom} — {self.date_validation.strftime('%d/%m/%Y %H:%M')}"


class Favori(models.Model):
    recette = models.ForeignKey('Recette', on_delete=models.CASCADE)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recette.nom} — {self.date_ajout.strftime('%d/%m/%Y %H:%M')}"


class Repas(models.Model):
    MOMENTS = [
        ('dejeuner', 'Déjeuner'),
        ('diner', 'Dîner'),
    ]
    date = models.DateField()
    moment = models.CharField(max_length=10, choices=MOMENTS)
    recette = models.ForeignKey(Recette, on_delete=models.CASCADE, related_name='repas')

    class Meta:
        ordering = ['date', 'moment']
        constraints = [
            models.UniqueConstraint(fields=['date', 'moment'], name='un_repas_par_creneau'),
        ]

    def __str__(self):
        return f"{self.get_moment_display()} du {self.date:%d/%m/%Y} : {self.recette}"
