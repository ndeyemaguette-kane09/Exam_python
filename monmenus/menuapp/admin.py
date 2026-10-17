from django.contrib import admin
from .models import Favori, Historique, Ingredient, Recette, RecetteIngredient, Repas


class RecetteIngredientInline(admin.TabularInline):
    model = RecetteIngredient
    extra = 1
    autocomplete_fields = ['ingredient']


@admin.register(Recette)
class RecetteAdmin(admin.ModelAdmin):
    inlines = [RecetteIngredientInline]
    list_display = ('nom', 'cout_estime', 'temps_preparation', 'portions')
    search_fields = ('nom',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'quantite', 'unite', 'seuil_alerte', 'categorie', 'lieu')
    list_filter = ('lieu', 'categorie')
    search_fields = ('nom',)


@admin.register(Historique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ('recette', 'date_validation')


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('recette', 'date_ajout')


@admin.register(Repas)
class RepasAdmin(admin.ModelAdmin):
    list_display = ('date', 'moment', 'recette')
    list_filter = ('moment',)
