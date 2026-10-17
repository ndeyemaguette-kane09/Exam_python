import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menuapp', '0007_favori'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': [django.db.models.functions.text.Lower('nom')]},
        ),
        migrations.AlterModelOptions(
            name='recette',
            options={'ordering': [django.db.models.functions.text.Lower('nom')]},
        ),
        migrations.AddField(
            model_name='ingredient',
            name='seuil_alerte',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='recette',
            name='portions',
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.CreateModel(
            name='RecetteIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantite', models.FloatField()),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='utilisations', to='menuapp.ingredient')),
                ('recette', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='menuapp.recette')),
            ],
            options={
                'ordering': [django.db.models.functions.text.Lower('ingredient__nom')],
                'constraints': [models.UniqueConstraint(fields=('recette', 'ingredient'), name='ingredient_unique_par_recette')],
            },
        ),
        migrations.CreateModel(
            name='Repas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('moment', models.CharField(choices=[('dejeuner', 'Déjeuner'), ('diner', 'Dîner')], max_length=10)),
                ('recette', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repas', to='menuapp.recette')),
            ],
            options={
                'ordering': ['date', 'moment'],
                'constraints': [models.UniqueConstraint(fields=('date', 'moment'), name='un_repas_par_creneau')],
            },
        ),
    ]
