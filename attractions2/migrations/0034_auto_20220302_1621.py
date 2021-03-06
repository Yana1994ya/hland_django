# Generated by Django 3.2.9 on 2022-03-02 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attractions2', '0033_rockclimbing_rockclimbingtype_watersports_watersportsattractiontype'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrailHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('last_visited', models.DateTimeField()),
                ('trail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.trail')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.googleuser')),
            ],
        ),
        migrations.CreateModel(
            name='TrailFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('trail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.trail')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='attractions2.googleuser')),
            ],
        ),
        migrations.AddIndex(
            model_name='trailhistory',
            index=models.Index(fields=['user', '-last_visited'], name='attractions_user_id_199e51_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='trailhistory',
            unique_together={('user', 'trail')},
        ),
        migrations.AddIndex(
            model_name='trailfavorite',
            index=models.Index(fields=['user', '-created'], name='attractions_user_id_3016d6_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='trailfavorite',
            unique_together={('user', 'trail')},
        ),
    ]
