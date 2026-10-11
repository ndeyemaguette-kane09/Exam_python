from django import forms

from .models import Ingredient


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['nom', 'quantite', 'unite', 'categorie', 'lieu']
        labels = {
            'nom': 'Nom',
            'quantite': 'Quantité',
            'unite': 'Unité',
            'categorie': 'Catégorie',
            'lieu': 'Lieu de stockage',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: g, kg, L, pièces...'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'lieu': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].choices = [('', '-- Choisir une catégorie --')] + [
            (valeur, f"{libelle} {Ingredient.EMOJIS.get(valeur, '🗃️')}")
            for valeur, libelle in Ingredient.CATEGORIES_CHOICES
        ]

    def clean_nom(self):
        return self.cleaned_data['nom'].strip()

    def clean_quantite(self):
        quantite = self.cleaned_data['quantite']
        if quantite < 0:
            raise forms.ValidationError("La quantité ne peut pas être négative.")
        return quantite
