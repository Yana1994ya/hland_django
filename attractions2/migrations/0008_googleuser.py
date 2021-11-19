# Generated by Django 3.2.9 on 2021-11-12 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0007_museumdomain_date_modified'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleUser',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('sub', models.CharField(blank=True, max_length=250, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('email_verified', models.BooleanField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=250, null=True)),
                ('given_name', models.CharField(blank=True, max_length=250, null=True)),
                ('family_name', models.CharField(blank=True, max_length=250, null=True)),
                ('picture', models.CharField(blank=True, max_length=250, null=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('anonymized', models.BooleanField()),
            ],
        ),
    ]