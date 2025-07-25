# Generated by Django 5.2.3 on 2025-06-12 05:31

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_specialization_specialistprofile'),
        ('inpatient', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hospitalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_admitted', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата и время госпитализации')),
                ('date_discharged', models.DateTimeField(blank=True, null=True, verbose_name='Дата и время выписки')),
                ('is_active', models.BooleanField(default=True, help_text='Отмечает, находится ли пациент в стационаре в данный момент по этой записи.', verbose_name='Активная госпитализация')),
                ('bed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospitalizations', to='inpatient.bed', verbose_name='Койка')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospitalizations', to='core.patient', verbose_name='Пациент')),
            ],
            options={
                'verbose_name': 'Госпитализация',
                'verbose_name_plural': 'Госпитализации',
                'ordering': ['-date_admitted'],
            },
        ),
    ]
