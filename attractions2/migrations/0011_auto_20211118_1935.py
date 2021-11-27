# Generated by Django 3.2.9 on 2021-11-18 19:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('attractions2', '0010_auto_20211114_0548'),
    ]

    operations = [
        migrations.CreateModel(
            name='Suitability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
            ],
        ),
        migrations.CreateModel(
            name='Winery',
            fields=[
                ('attraction_ptr', models.OneToOneField(auto_created=True,
                                                        on_delete=django.db.models.deletion.CASCADE,
                                                        parent_link=True, primary_key=True,
                                                        serialize=False,
                                                        to='attractions2.attraction')),
            ],
            bases=('attractions2.attraction',),
        ),
        migrations.AddField(
            model_name='attraction',
            name='suitability',
            field=models.ManyToManyField(to='attractions2.Suitability'),
        ),
    ]
