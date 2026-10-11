from django.contrib import admin
from .models import Favori, Historique, Ingredient, Recette


@admin.register(Recette)
class RecetteAdmin(admin.ModelAdmin):
    filter_horizontal = ('ingredients',)
    list_display = ('nom', 'cout_estime', 'temps_preparation')
    search_fields = ('nom',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'quantite', 'unite', 'categorie', 'lieu')
    list_filter = ('lieu', 'categorie')
    search_fields = ('nom',)


@admin.register(Historique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ('recette', 'date_validation')


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('recette', 'date_ajout')
