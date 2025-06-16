# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import RehabilitationProgram, RehabActivity, ScheduledActivity

@admin.register(RehabilitationProgram)
class RehabilitationProgramAdmin(admin.ModelAdmin):
    list_display = ('patient', 'program_type', 'start_date', 'end_date', 'status', 'specialist')
    list_filter = ('program_type', 'status', 'start_date')
    search_fields = ('patient__last_name', 'patient__first_name', 'goal')
    autocomplete_fields = ['patient', 'specialist']


@admin.register(RehabActivity)
class RehabActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'default_duration')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    # Поля для формы редактирования
    fields = ('name', 'category', 'description', 'default_duration', 'required_equipment')


@admin.register(ScheduledActivity)
class ScheduledActivityAdmin(admin.ModelAdmin):
    list_display = ('program', 'activity', 'scheduled_date', 'status')
    list_filter = ('status', 'scheduled_date', 'activity')
    search_fields = ('program__patient__last_name', 'activity__name')
    autocomplete_fields = ['program', 'activity']
