# Generated by Django 3.2.9 on 2022-02-19 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0032_alter_usercomment_content_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='RockClimbingType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WaterSportsAttractionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WaterSports',
            fields=[
                ('attraction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='attractions2.attraction')),
                ('attraction_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.watersportsattractiontype')),
            ],
            bases=('attractions2.attraction',),
        ),
        migrations.CreateModel(
            name='RockClimbing',
            fields=[
                ('attraction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='attractions2.attraction')),
                ('attraction_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.rockclimbingtype')),
            ],
            bases=('attractions2.attraction',),
        ),
    ]
