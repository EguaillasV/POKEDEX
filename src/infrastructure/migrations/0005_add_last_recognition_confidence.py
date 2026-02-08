# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0004_add_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='animalmodel',
            name='last_recognition_confidence',
            field=models.FloatField(blank=True, null=True, help_text='Última confianza del modelo YOLO'),
        ),
    ]
