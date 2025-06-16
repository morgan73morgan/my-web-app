# -*- coding: utf-8 -*-
from django import forms
from .models import RehabilitationProgram, ScheduledActivity

class RehabilitationProgramForm(forms.ModelForm):
    class Meta:
        model = RehabilitationProgram
        fields = ['program_type', 'specialist', 'start_date', 'end_date', 'goal']
        widgets = {
            'program_type': forms.Select(attrs={'class': 'form-select'}),
            'specialist': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'goal': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ScheduledActivityForm(forms.ModelForm):
    class Meta:
        model = ScheduledActivity
        fields = ['activity', 'specialist', 'scheduled_date', 'specialist_notes']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'specialist': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'specialist_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
