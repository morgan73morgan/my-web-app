from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.db import models
from django.utils import timezone
from .models import Patient, Ward, Bed, PatientAdmission, PatientDocument, Staff
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import PatientForm, PatientDocumentForm, SystemSettingsForm, IntegrationSettingsForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .forms import UserCreateForm, UserEditForm, RoleChangeForm
from django import forms
import csv
from django.http import HttpResponse, JsonResponse

from medical_history.forms import MedicalRecordForm
from rehab_programs.forms import RehabilitationProgramForm
from django.contrib.auth import get_user_model
from .models import SystemSettings, IntegrationSettings, AuditLog

User = get_user_model()

from django.urls import reverse
from .models import Ward, Bed, PatientAdmission
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test


def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def settings_hub(request):
    # Получаем или создаём singleton объекты
    system_settings, _ = SystemSettings.objects.get_or_create(pk=1)
    integration_settings, _ = IntegrationSettings.objects.get_or_create(pk=1)

    system_form = SystemSettingsForm(request.POST or None, request.FILES or None, instance=system_settings)
    integration_form = IntegrationSettingsForm(request.POST or None, instance=integration_settings)

    active_tab = request.POST.get('active_tab', 'general')
    updated = False

    if request.method == 'POST':
        if 'save_system' in request.POST and system_form.is_valid():
            old_values = {f: getattr(system_settings, f) for f in system_form.fields}
            system_form.save()
            updated = True
            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model='SystemSettings',
                object_id=system_settings.pk,
                old_value=str(old_values),
                new_value=str({f: getattr(system_settings, f) for f in system_form.fields})
            )
            messages.success(request, 'Основные настройки успешно сохранены.')
            active_tab = 'general'
        elif 'save_integration' in request.POST and integration_form.is_valid():
            old_values = {f: getattr(integration_settings, f) for f in integration_form.fields}
            integration_form.save()
            updated = True
            # Audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model='IntegrationSettings',
                object_id=integration_settings.pk,
                old_value=str(old_values),
                new_value=str({f: getattr(integration_settings, f) for f in integration_form.fields})
            )
            messages.success(request, 'Интеграции успешно сохранены.')
            active_tab = 'integration'

    # --- Пользователи и роли ---
    users = User.objects.all().select_related()
    groups = Group.objects.all()
    user_form = UserCreateForm()
    group_form = None  # Можно добавить форму создания групп при необходимости

    # --- Экспорт/импорт ---
    export_patients_url = reverse('core:export_patients')
    export_admissions_url = reverse('core:export_admissions')
    import_patients_url = reverse('core:import_patients')
    import_admissions_url = reverse('core:import_admissions')

    # --- Кастомизация интерфейса ---
    # (используется system_form: logo, color_theme)

    context = {
        'system_form': system_form,
        'integration_form': integration_form,
        'active_tab': active_tab,
        'users': users,
        'groups': groups,
        'user_form': user_form,
        'export_patients_url': export_patients_url,
        'export_admissions_url': export_admissions_url,
        'import_patients_url': import_patients_url,
        'import_admissions_url': import_admissions_url,
    }
    return render(request, 'core/settings.html', context)


@login_required
@user_passes_test(is_superuser)
def create_user(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Пользователь успешно создан.')
            return redirect('core:settings')
        else:
            messages.error(request, 'Ошибка при создании пользователя.')
    else:
        form = UserCreateForm()
    return render(request, 'core/user_form.html', {'form': form})

@login_required
@user_passes_test(is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пользователь успешно обновлён.')
            return redirect('core:settings')
        else:
            messages.error(request, 'Ошибка при обновлении пользователя.')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'core/user_form.html', {'form': form, 'edit': True, 'user_obj': user})

@login_required
@user_passes_test(is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Пользователь удалён.')
        return redirect('core:settings')
    return render(request, 'core/user_confirm_delete.html', {'user_obj': user})

@login_required
@user_passes_test(is_superuser)
def change_user_role(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = RoleChangeForm(request.POST)
        if form.is_valid():
            user.groups.set(form.cleaned_data['groups'])
            user.save()
            messages.success(request, 'Роли пользователя обновлены.')
            return redirect('core:settings')
        else:
            messages.error(request, 'Ошибка при обновлении ролей.')
    else:
        form = RoleChangeForm(initial={'groups': user.groups.all()})
    return render(request, 'core/user_role_form.html', {'form': form, 'user_obj': user})

# AJAX: смена темы оформления
@login_required
@user_passes_test(is_superuser)
def set_theme(request):
    if request.method == 'POST' and request.is_ajax():
        theme = request.POST.get('theme')
        settings = SystemSettings.objects.get(pk=1)
        settings.color_theme = theme
        settings.save()
        return JsonResponse({'status': 'ok', 'theme': theme})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
@user_passes_test(is_superuser)
def export_patients(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=patients.csv'
    writer = csv.writer(response)
    fields = ['id', 'last_name', 'first_name', 'middle_name', 'date_of_birth', 'gender', 'phone_number', 'email', 'address']
    writer.writerow(fields)
    for p in Patient.objects.all():
        writer.writerow([getattr(p, f) for f in fields])
    return response

@login_required
@user_passes_test(is_superuser)
def export_admissions(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=admissions.csv'
    writer = csv.writer(response)
    fields = ['id', 'patient_id', 'ward_id', 'bed_id', 'admission_date', 'discharge_date', 'doctor_id', 'diagnosis']
    writer.writerow(fields)
    for adm in PatientAdmission.objects.all():
        writer.writerow([getattr(adm, f) for f in fields])
    return response

@login_required
@user_passes_test(is_superuser)
def import_patients(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        decoded = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        for row in reader:
            Patient.objects.update_or_create(
                id=row['id'],
                defaults={k: v for k, v in row.items() if k != 'id'}
            )
        messages.success(request, 'Пациенты успешно импортированы.')
        return redirect('core:settings')
    return render(request, 'core/import_patients.html')

@login_required
@user_passes_test(is_superuser)
def import_admissions(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        decoded = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        for row in reader:
            PatientAdmission.objects.update_or_create(
                id=row['id'],
                defaults={k: v for k, v in row.items() if k != 'id'}
            )
        messages.success(request, 'Госпитализации успешно импортированы.')
        return redirect('core:settings')
    return render(request, 'core/import_admissions.html')

class WardCreateView(CreateView):
    model = Ward
    fields = ['name', 'department', 'floor', 'capacity', 'description', 'is_active']
    template_name = 'core/ward_form.html'
    success_url = '/bed-management/'

class WardUpdateView(UpdateView):
    model = Ward
    fields = ['name', 'department', 'floor', 'capacity', 'description', 'is_active']
    template_name = 'core/ward_form.html'
    success_url = '/bed-management/'

class WardDeleteView(DeleteView):
    model = Ward
    template_name = 'core/ward_confirm_delete.html'
    success_url = '/bed-management/'

class BedCreateView(CreateView):
    model = Bed
    fields = ['ward', 'number', 'bed_type', 'is_available']
    template_name = 'core/bed_form.html'
    success_url = '/bed-management/'
    
    def get_initial(self):
        initial = super().get_initial()
        ward_id = self.kwargs.get('ward_id')
        if ward_id:
            initial['ward'] = ward_id
        return initial

class BedUpdateView(UpdateView):
    model = Bed
    fields = ['ward', 'number', 'bed_type', 'is_available']
    template_name = 'core/bed_form.html'
    success_url = '/bed-management/'

class BedDeleteView(DeleteView):
    model = Bed
    template_name = 'core/bed_confirm_delete.html'
    success_url = '/bed-management/'

class AdmissionCreateView(CreateView):
    model = PatientAdmission
    fields = ['patient', 'ward', 'bed', 'admission_date', 'doctor', 'diagnosis']
    template_name = 'core/admission_form.html'
    success_url = '/bed-management/'
    
    def get_initial(self):
        initial = super().get_initial()
        bed_id = self.kwargs.get('bed_id')
        if bed_id:
            initial['bed'] = bed_id
        return initial

class AdmissionDischargeView(UpdateView):
    model = PatientAdmission
    fields = ['discharge_date']
    template_name = 'core/admission_discharge_form.html'
    success_url = '/bed-management/'

class AdmissionHistoryView(ListView):
    model = PatientAdmission
    template_name = 'core/admission_history.html'
    context_object_name = 'admissions'
    
    def get_queryset(self):
        return PatientAdmission.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-admission_date')

class StaffListView(ListView):
    model = Staff
    template_name = 'core/staff_list.html'
    context_object_name = 'staff_list'
    paginate_by = 20

class StaffCreateView(CreateView):
    model = Staff
    fields = ['first_name', 'last_name', 'middle_name', 'position', 'department', 'email', 'phone', 'status', 'hire_date', 'fire_date', 'user']
    template_name = 'core/staff_form.html'
    success_url = reverse_lazy('core:staff_list')

class StaffUpdateView(UpdateView):
    model = Staff
    fields = ['first_name', 'last_name', 'middle_name', 'position', 'department', 'email', 'phone', 'status', 'hire_date', 'fire_date', 'user']
    template_name = 'core/staff_form.html'
    success_url = reverse_lazy('core:staff_list')

class StaffDeleteView(DeleteView):
    model = Staff
    template_name = 'core/staff_confirm_delete.html'
    success_url = reverse_lazy('core:staff_list')

def patient_detail(request, pk):
    # Ensure pk is treated as string
    patient = get_object_or_404(Patient, pk=str(pk))
    document_form = PatientDocumentForm()

    if request.method == 'POST':
        # Handle document upload
        form = PatientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.patient = patient
            document.save()
            return redirect('core:patient_detail', pk=str(patient.pk))
    
    # Get related data first
    documents = patient.documents.all()
    medical_records = patient.medical_records.all()
    medical_record_form = MedicalRecordForm()
    rehab_programs = patient.rehabilitation_programs.all()
    rehab_program_form = RehabilitationProgramForm()
    
    # Prepare patient data with string conversion
    patient_data = {
        'id': str(patient.id) if patient.id else '',
        'first_name': str(patient.first_name) if patient.first_name else '',
        'last_name': str(patient.last_name) if patient.last_name else '',
        'middle_name': str(patient.middle_name) if patient.middle_name else '',
        'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else '',
        'gender': str(patient.get_gender_display()) if hasattr(patient, 'get_gender_display') else '',
        'address': str(patient.address) if patient.address else '',
        'phone_number': str(patient.phone_number) if patient.phone_number else 'Не указан',
        'email': str(patient.email) if patient.email else 'Не указан',
        'curator': str(patient.curator.get_full_name()) if (patient.curator and hasattr(patient.curator, 'get_full_name')) else 'Не назначен',
        'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(patient, 'created_at') and patient.created_at else '',
        'updated_at': patient.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(patient, 'updated_at') and patient.updated_at else '',
    }
    
    # Get related data
    documents = patient.documents.all()
    medical_records = patient.medical_records.all()
    medical_record_form = MedicalRecordForm()
    rehab_programs = patient.rehabilitation_programs.all()
    rehab_program_form = RehabilitationProgramForm()

    context = {
        'patient': patient,
        'patient_data': patient_data,  # Add the processed patient data
        'documents': documents,
        'document_form': document_form,
        'medical_records': medical_records,
        'medical_record_form': medical_record_form,
        'rehab_programs': rehab_programs,
        'rehab_program_form': rehab_program_form
    }
    return render(request, 'core/patient_detail.html', context)

def patient_update(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('core:patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'core/patient_form.html', {'form': form, 'patient': patient})

def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:patient_list')
    else:
        form = PatientForm()
    return render(request, 'core/patient_form.html', {'form': form})

def patient_list(request):
    patients = Patient.objects.all()
    context = {
        'patients': patients
    }
    return render(request, 'core/patient_list.html', context)

def format_number(value):
    """Format number with spaces as thousand separators"""
    if value is None:
        return '0'
    try:
        return "{:,}".format(int(value)).replace(",", " ")
    except (ValueError, TypeError):
        return str(value)

def dashboard(request):
    # Format numbers with spaces as thousand separators
    def format_number(value):
        if value is None:
            return '0'
        try:
            return "{:,}".format(int(value)).replace(",", " ")
        except (ValueError, TypeError):
            return str(value)

    try:
        # Try to get real data from the database
        from django.db.models import Count, Sum, Q
        from datetime import datetime, timedelta
        
        # Get counts for dashboard cards
        patients_count = Patient.objects.count()
        active_programs = 45  # Placeholder - replace with actual query
        available_beds = 32   # Placeholder - replace with actual query
        staff_count = 28      # Placeholder - replace with actual query
        
        # Get recent patients (last 3)
        recent_patients = Patient.objects.order_by('-created_at')[:3]
        recent_patients_data = [
            {
                'name': f"{p.last_name} {p.first_name}",
                'admission_date': p.created_at.strftime('%Y-%m-%d') if hasattr(p, 'created_at') else 'Неизвестно',
                'program': 'Стандартная'  # Placeholder - replace with actual program data
            }
            for p in recent_patients
        ]
        
        # Ensure we have at least 3 patients
        while len(recent_patients_data) < 3:
            recent_patients_data.append({
                'name': 'Нет данных',
                'admission_date': '--',
                'program': '--'
            })
        
        # Sample data for services stats
        services_stats = {
            'total_revenue': 1250000,
            'top_services': [
                {'name': 'Консультация врача', 'total_revenue': 250000, 'count': 125},
                {'name': 'Массаж', 'total_revenue': 380000, 'count': 190},
                {'name': 'Физиотерапия', 'total_revenue': 620000, 'count': 310},
            ]
        }
        
        context = {
            # Card data
            'patients_count': format_number(patients_count),
            'active_programs': format_number(active_programs),
            'available_beds': format_number(available_beds),
            'staff_count': format_number(staff_count),
            
            # Recent patients
            'recent_patients': recent_patients_data,
            
            # Upcoming appointments (sample data for now)
            'upcoming_appointments': [
                {'time': '10:00', 'patient': 'Иванов Иван', 'type': 'Консультация'},
                {'time': '11:30', 'patient': 'Петрова Анна', 'type': 'Процедура'},
                {'time': '14:15', 'patient': 'Сидоров Алексей', 'type': 'Осмотр'},
            ],
            
            # Services stats
            'services_stats': services_stats
        }
        
    except Exception as e:
        # Fallback to sample data if there's any error
        print(f"Error in dashboard view: {str(e)}")
        context = {
            'patients_count': format_number(150),
            'active_programs': format_number(45),
            'available_beds': format_number(32),
            'staff_count': format_number(28),
            'recent_patients': [
                {'name': 'Иванов Иван', 'admission_date': '2023-06-10', 'program': 'Стандартная'},
                {'name': 'Петрова Анна', 'admission_date': '2023-06-09', 'program': 'Интенсив'},
                {'name': 'Сидоров Алексей', 'admission_date': '2023-06-08', 'program': 'Премиум'},
            ],
            'upcoming_appointments': [
                {'time': '10:00', 'patient': 'Иванов Иван', 'type': 'Консультация'},
                {'time': '11:30', 'patient': 'Петрова Анна', 'type': 'Процедура'},
                {'time': '14:15', 'patient': 'Сидоров Алексей', 'type': 'Осмотр'},
            ],
            'services_stats': {
                'total_revenue': 1250000,
                'top_services': [
                    {'name': 'Консультация врача', 'total_revenue': 250000, 'count': 125},
                    {'name': 'Массаж', 'total_revenue': 380000, 'count': 190},
                    {'name': 'Физиотерапия', 'total_revenue': 620000, 'count': 310},
                ]
            }
        }
    
    return render(request, 'core/dashboard_clean.html', context)


def bed_management(request):
    """
    View for displaying and managing hospital beds
    """
    # Get all active wards with their beds and patient admissions
    wards = Ward.objects.filter(is_active=True).prefetch_related(
        models.Prefetch(
            'bed_set',
            queryset=Bed.objects.select_related('ward').prefetch_related(
                models.Prefetch(
                    'patient_admission',
                    queryset=PatientAdmission.objects.filter(
                        discharge_date__isnull=True
                    ).select_related('patient', 'doctor'),
                    to_attr='active_admissions'
                )
            ),
            to_attr='beds_with_admissions'
        )
    )
    
    # Prepare data for the template
    wards_data = []
    for ward in wards:
        beds_data = []
        for bed in ward.beds_with_admissions:
            # Get active admission if exists
            active_admission = bed.active_admissions[0] if hasattr(bed, 'active_admissions') and bed.active_admissions else None
            
            bed_data = {
                'id': bed.id,
                'number': bed.number,
                'bed_type': bed.get_bed_type_display(),
                'is_available': bed.is_available,
                'is_occupied': active_admission is not None,
                'patient': None,
                'admission_date': None,
                'doctor': None,
                'diagnosis': None
            }
            
            if active_admission:
                bed_data.update({
                    'patient': {
                        'id': active_admission.patient.id,
                        'full_name': active_admission.patient.get_full_name(),
                        'birth_date': active_admission.patient.date_of_birth.strftime('%d.%m.%Y') if active_admission.patient.date_of_birth else '—',
                    },
                    'admission_date': active_admission.admission_date.strftime('%d.%m.%Y'),
                    'doctor': active_admission.doctor.get_full_name() if active_admission.doctor else 'Не назначен',
                    'diagnosis': active_admission.diagnosis or '—'
                })
            
            beds_data.append(bed_data)
        
        wards_data.append({
            'id': ward.id,
            'name': ward.name,
            'department': ward.department or '—',
            'floor': ward.floor,
            'capacity': ward.capacity,
            'available_beds': ward.get_available_beds_count(),
            'beds': beds_data
        })
    
    context = {
        'wards': wards_data,
        'current_date': timezone.now().strftime('%d %B %Y')
    }
    
    return render(request, 'core/bed_management.html', context)
    
    return render(request, 'core/bed_management.html', context)
