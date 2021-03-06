# Generated by Django 3.2.9 on 2022-02-11 10:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0029_auto_20220211_0942'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrailActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='trailattraction',
            options={},
        ),
        migrations.AlterModelOptions(
            name='trailsuitability',
            options={},
        ),
        migrations.RenameField(
            model_name='trail',
            old_name='suitability',
            new_name='suitabilities',
        ),
        migrations.AddField(
            model_name='trail',
            name='attractions',
            field=models.ManyToManyField(related_name='trails_with_attraction', to='attractions2.TrailAttraction'),
        ),
        migrations.AddField(
            model_name='trailattraction',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='trailsuitability',
            name='date_modified',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='museumdomain',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='trailattraction',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='trailsuitability',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AddField(
            model_name='trail',
            name='activities',
            field=models.ManyToManyField(related_name='trails_with_activity', to='attractions2.TrailActivity'),
        ),
    ]
