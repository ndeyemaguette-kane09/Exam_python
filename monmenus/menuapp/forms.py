from django import forms
from django.forms import inlineformset_factory

from .models import Ingredient, Recette, RecetteIngredient, Repas


def sans_decimale_inutile(form, *champs):
    for champ in champs:
        valeur = form.initial.get(champ)
        if isinstance(valeur, float) and valeur.is_integer():
            form.initial[champ] = int(valeur)


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['nom', 'quantite', 'unite', 'seuil_alerte', 'categorie', 'lieu']
        labels = {
            'nom': 'Nom',
            'quantite': 'Quantité',
            'unite': 'Unité',
            'seuil_alerte': 'Seuil de stock bas',
            'categorie': 'Catégorie',
            'lieu': 'Lieu de stockage',
        }
        help_texts = {
            'seuil_alerte': "En dessous de cette quantité, l'accueil te prévient avant la rupture.",
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: g, kg, L, pièces...'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'lieu': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].choices = [('', '-- Choisir une catégorie --')] + Ingredient.CATEGORIES_CHOICES
        sans_decimale_inutile(self, 'quantite', 'seuil_alerte')

    def clean_nom(self):
        return self.cleaned_data['nom'].strip()

    def clean_quantite(self):
        quantite = self.cleaned_data['quantite']
        if quantite < 0:
            raise forms.ValidationError("La quantité ne peut pas être négative.")
        return quantite

    def clean_seuil_alerte(self):
        seuil = self.cleaned_data['seuil_alerte']
        if seuil < 0:
            raise forms.ValidationError("Le seuil ne peut pas être négatif.")
        return seuil


class RecetteForm(forms.ModelForm):
    class Meta:
        model = Recette
        fields = ['nom', 'cout_estime', 'temps_preparation', 'portions', 'image', 'instructions']
        labels = {
            'nom': 'Nom de la recette',
            'cout_estime': 'Coût (FCFA)',
            'temps_preparation': 'Temps (min)',
            'portions': 'Portions',
            'image': 'Photo',
            'instructions': 'Étapes',
        }
        help_texts = {
            'instructions': 'Une étape par ligne.',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'cout_estime': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '50'}),
            'temps_preparation': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'portions': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }

    def clean_nom(self):
        return self.cleaned_data['nom'].strip()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sans_decimale_inutile(self, 'cout_estime')

    def clean_cout_estime(self):
        cout = self.cleaned_data['cout_estime']
        if cout < 0:
            raise forms.ValidationError("Le coût ne peut pas être négatif.")
        return cout

    def clean_temps_preparation(self):
        temps = self.cleaned_data['temps_preparation']
        if temps <= 0:
            raise forms.ValidationError("Le temps doit être supérieur à 0.")
        return temps


class IngredientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj} ({obj.unite})" if obj.unite else str(obj)


class RecetteIngredientForm(forms.ModelForm):
    ingredient = IngredientChoiceField(
        queryset=Ingredient.objects.all(),
        label='Ingrédient',
        empty_label='Choisir un ingrédient',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = RecetteIngredient
        fields = ['ingredient', 'quantite']
        labels = {'quantite': 'Quantité'}
        widgets = {
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Qté'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sans_decimale_inutile(self, 'quantite')

    def clean_quantite(self):
        quantite = self.cleaned_data['quantite']
        if quantite <= 0:
            raise forms.ValidationError("La quantité doit être supérieure à 0.")
        return quantite


class BaseLignesFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        vus = set()
        restantes = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data') or not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            ingredient = form.cleaned_data.get('ingredient')
            if ingredient is None:
                continue
            if ingredient.pk in vus:
                raise forms.ValidationError(f"« {ingredient} » est présent deux fois.")
            vus.add(ingredient.pk)
            restantes += 1
        if restantes == 0:
            raise forms.ValidationError("Ajoute au moins un ingrédient.")


LignesFormSet = inlineformset_factory(
    Recette,
    RecetteIngredient,
    form=RecetteIngredientForm,
    formset=BaseLignesFormSet,
    extra=3,
    can_delete=True,
)


class RepasForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'))
    moment = forms.ChoiceField(choices=Repas.MOMENTS, widget=forms.Select(attrs={'class': 'form-select'}))
    recette = forms.ModelChoiceField(queryset=Recette.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
