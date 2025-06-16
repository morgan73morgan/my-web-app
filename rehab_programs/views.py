# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from core.models import Patient
from .models import RehabilitationProgram, ScheduledActivity
from .forms import RehabilitationProgramForm, ScheduledActivityForm
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import CreateView, UpdateView, DeleteView

# ---
# CRUD для ScheduledActivity (действия календаря)
class ScheduledActivityCreateView(LoginRequiredMixin, CreateView):
    model = ScheduledActivity
    form_class = ScheduledActivityForm
    template_name = 'rehab_programs/scheduled_activity_form.html'

    def get_initial(self):
        initial = super().get_initial()
        program_id = self.request.GET.get('program')
        if program_id:
            initial['program'] = program_id
        return initial

    def get_success_url(self):
        return reverse_lazy('rehab_programs:calendar')

class ScheduledActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = ScheduledActivity
    form_class = ScheduledActivityForm
    template_name = 'rehab_programs/scheduled_activity_form.html'

    def get_success_url(self):
        return reverse_lazy('rehab_programs:calendar')

class ScheduledActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = ScheduledActivity
    template_name = 'rehab_programs/scheduled_activity_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('rehab_programs:calendar')

# ---
# NEW CLASS-BASED VIEWS FOR FULL CRUD

class RehabilitationProgramListView(LoginRequiredMixin, ListView):
    model = RehabilitationProgram
    template_name = 'rehab_programs/rehab_program_list.html'
    context_object_name = 'programs'
    paginate_by = 20

class RehabilitationProgramCreateView(LoginRequiredMixin, CreateView):
    model = RehabilitationProgram
    form_class = RehabilitationProgramForm
    template_name = 'rehab_programs/rehab_program_form.html'
    success_url = reverse_lazy('rehab_programs:rehab_program_list')

class RehabilitationProgramUpdateView(LoginRequiredMixin, UpdateView):
    model = RehabilitationProgram
    form_class = RehabilitationProgramForm
    template_name = 'rehab_programs/rehab_program_form.html'
    success_url = reverse_lazy('rehab_programs:rehab_program_list')

class RehabilitationProgramDeleteView(LoginRequiredMixin, DeleteView):
    model = RehabilitationProgram
    template_name = 'rehab_programs/rehab_program_confirm_delete.html'
    success_url = reverse_lazy('rehab_programs:rehab_program_list')

from django.template.loader import render_to_string

@login_required
def add_rehab_program(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == 'POST':
        form = RehabilitationProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.patient = patient
            program.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                program_row_html = render_to_string('rehab_programs/program_row.html', {'program': program}, request=request)
                return JsonResponse({'success': True, 'program_row_html': program_row_html})
            return redirect('core:patient_detail', pk=patient.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors_html = render_to_string('rehab_programs/program_create_modal.html', {'form': form, 'patient': patient}, request=request)
                return JsonResponse({'success': False, 'errors_html': errors_html})
    # This view only handles POST, so we redirect on GET
    return redirect('core:patient_detail', pk=patient.pk)



@login_required
def rehab_program_detail(request, program_pk):
    program = get_object_or_404(RehabilitationProgram, pk=program_pk)
    scheduled_activities = program.scheduled_activities.all()
    form = ScheduledActivityForm()
    
    context = {
        'program': program,
        'scheduled_activities': scheduled_activities,
        'form': form
    }
    return render(request, 'rehab_programs/rehab_program_detail.html', context)


@login_required
def add_scheduled_activity(request, program_pk):
    program = get_object_or_404(RehabilitationProgram, pk=program_pk)
    if request.method == 'POST':
        form = ScheduledActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.program = program
            activity.save()
            return redirect('rehab_programs:rehab_program_detail', program_pk=program.pk)
    
    return redirect('rehab_programs:rehab_program_detail', program_pk=program.pk)


@login_required
def calendar_view(request):
    specialists = User.objects.filter(is_staff=True).order_by('last_name', 'first_name')
    patients = Patient.objects.all().order_by('last_name', 'first_name')
    context = {
        'specialists': specialists,
        'patients': patients,
    }
    return render(request, 'rehab_programs/calendar.html', context)


@login_required
def all_activities_api(request):
    specialist_id = request.GET.get('specialist_id')
    patient_id = request.GET.get('patient_id')

    activities = ScheduledActivity.objects.select_related('activity', 'program__patient', 'specialist').all()

    if specialist_id:
        activities = activities.filter(specialist_id=specialist_id)
    
    if patient_id:
        activities = activities.filter(program__patient_id=patient_id)

    events = []
    for activity in activities:
        title = f"{activity.activity.name} - {activity.program.patient.get_full_name()}"
        if activity.specialist:
            title += f" ({activity.specialist.get_full_name() or activity.specialist.username})"

        events.append({
            'title': title,
            'start': activity.scheduled_date.isoformat(),
            'url': activity.program.get_absolute_url(),
        })
    return JsonResponse(events, safe=False)
