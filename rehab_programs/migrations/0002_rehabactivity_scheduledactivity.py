# Generated by Django 5.2.3 on 2025-06-11 18:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rehab_programs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RehabActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название процедуры/занятия')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Реабилитационная процедура',
                'verbose_name_plural': 'Справочник процедур',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ScheduledActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_date', models.DateTimeField(verbose_name='Дата и время проведения')),
                ('status', models.CharField(choices=[('PLANNED', 'Запланировано'), ('COMPLETED', 'Проведено'), ('CANCELLED', 'Отменено'), ('MISSED', 'Пропущено')], default='PLANNED', max_length=20, verbose_name='Статус')),
                ('specialist_notes', models.TextField(blank=True, verbose_name='Заметки специалиста')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rehab_programs.rehabactivity', verbose_name='Процедура/занятие')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_activities', to='rehab_programs.rehabilitationprogram', verbose_name='Программа реабилитации')),
            ],
            options={
                'verbose_name': 'Запланированная процедура',
                'verbose_name_plural': 'Запланированные процедуры',
                'ordering': ['scheduled_date'],
            },
        ),
    ]
