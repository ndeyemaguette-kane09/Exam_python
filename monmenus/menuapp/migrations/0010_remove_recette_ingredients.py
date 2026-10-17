from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menuapp', '0009_reprise_quantites'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recette',
            name='ingredients',
        ),
    ]
