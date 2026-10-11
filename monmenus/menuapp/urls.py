from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('frigo/', views.stock, {'lieu': 'Frigo'}, name='frigo'),
    path('placard/', views.stock, {'lieu': 'Placard'}, name='placard'),
    path('frigo/ajouter/', views.ajouter_ingredient, {'lieu': 'Frigo'}, name='ajouter_ingredient'),
    path('placard/ajouter/', views.ajouter_ingredient, {'lieu': 'Placard'}, name='ajouter_ingredient_placard'),
    path('ingredient/<int:id>/modifier/', views.modifier_ingredient, name='modifier_ingredient'),
    path('ingredient/<int:id>/supprimer/', views.supprimer_ingredient, name='supprimer_ingredient'),
    path('recettes/', views.recettes, name='recettes'),
    path('recette/<int:recette_id>/', views.detail_recette, name='detail_recette'),
    path('recette/<int:recette_id>/confirmer/', views.confirmer_recette, name='confirmer_recette'),
    path('recette/<int:recette_id>/favori/', views.basculer_favori, name='basculer_favori'),
    path('export-pdf/<int:recette_id>/', views.export_pdf, name='export_pdf'),
    path('generer-menu/', views.generer_menu, name='generer_menu'),
    path('historique/', views.historique, name='historique'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
]
