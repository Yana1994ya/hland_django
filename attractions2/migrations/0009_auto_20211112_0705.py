# Generated by Django 3.2.9 on 2021-11-12 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0008_googleuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_created=True)),
                ('last_visited', models.DateTimeField(auto_now_add=True)),
                ('attraction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.attraction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.googleuser')),
            ],
        ),
        migrations.AddIndex(
            model_name='history',
            index=models.Index(fields=['user', '-last_visited'], name='attractions_user_id_bc2327_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='history',
            unique_together={('user', 'attraction')},
        ),
    ]