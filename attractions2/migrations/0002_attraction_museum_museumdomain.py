# Generated by Django 3.2.9 on 2021-11-07 15:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('lat', models.FloatField()),
                ('long', models.FloatField()),
                ('additional_images', models.ManyToManyField(related_name='attraction_additional_image', to='attractions2.ImageAsset')),
                ('main_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='attractions2.imageasset')),
            ],
        ),
        migrations.CreateModel(
            name='MuseumDomain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Museum',
            fields=[
                ('attraction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='attractions2.attraction')),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.museumdomain')),
            ],
            bases=('attractions2.attraction',),
        ),
    ]
