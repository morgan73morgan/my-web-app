from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import F, Q, Count, Case, When, Value, IntegerField
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Patient, Ward, Bed, PatientAdmission, PatientDocument, Specialization, SpecialistProfile
from .forms import PatientAdmissionForm, PatientDocumentForm, PatientSearchForm

User = get_user_model()

def staff_required(view_func):
    """Decorator for views that checks that the user is a staff member."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'У вас нет прав доступа к этой странице.')
            return redirect('admin_panel:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@staff_required
def admin_dashboard(request):
    """Admin dashboard with key metrics and recent activities."""
    # Basic statistics
    total_patients = Patient.objects.count()
    active_admissions = PatientAdmission.objects.filter(discharge_date__isnull=True).count()
    available_beds = Bed.objects.filter(is_available=True).count()
    total_wards = Ward.objects.count()
    
    # Admission statistics
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    monthly_admissions = PatientAdmission.objects.filter(
        admission_date__year=month_start.year,
        admission_date__month=month_start.month
    ).count()
    
    monthly_discharges = PatientAdmission.objects.filter(
        discharge_date__year=month_start.year,
        discharge_date__month=month_start.month
    ).count()
    
    # Ward occupancy
    wards = Ward.objects.annotate(
        total_beds=Count('bed'),
        occupied_beds=Count('bed', filter=Q(bed__patientadmission__discharge_date__isnull=True)),
        available_beds=Count('bed', filter=Q(bed__is_available=True))
    ).order_by('name')
    
    # Recent admissions
    recent_admissions = PatientAdmission.objects.select_related(
        'patient', 'bed__ward', 'doctor'
    ).order_by('-admission_date')[:5]
    
    # Patient demographics
    gender_distribution = Patient.objects.values('gender').annotate(
        count=Count('id'),
        percentage=Count('id') * 100.0 / Patient.objects.count()
    )
    
    # Age distribution
    age_groups = Patient.objects.annotate(
        age_group=Case(
            When(age__lt=18, then=Value('0-17')),
            When(age__range=(18, 30), then=Value('18-30')),
            When(age__range=(31, 45), then=Value('31-45')),
            When(age__range=(46, 65), then=Value('46-65')),
            When(age__gt=65, then=Value('65+')),
            default=Value('Unknown'),
            output_field=models.CharField(),
        )
    ).values('age_group').annotate(
        count=Count('id'),
        percentage=Count('id') * 100.0 / Patient.objects.count()
    ).order_by('age_group')
    
    context = {
        # Statistics
        'stats': {
            'total_patients': total_patients,
            'active_admissions': active_admissions,
            'available_beds': available_beds,
            'total_wards': total_wards,
            'monthly_admissions': monthly_admissions,
            'monthly_discharges': monthly_discharges,
            'occupancy_rate': round((1 - (available_beds / Bed.objects.count())) * 100, 1) if Bed.objects.exists() else 0,
        },
        
        # Data for charts
        'gender_distribution': list(gender_distribution),
        'age_distribution': list(age_groups),
        'wards_data': [
            {
                'name': ward.name,
                'total': ward.total_beds,
                'occupied': ward.occupied_beds,
                'available': ward.available_beds,
                'occupancy_rate': round((ward.occupied_beds / ward.total_beds) * 100, 1) if ward.total_beds > 0 else 0
            } for ward in wards
        ],
        
        # Recent activities
        'recent_admissions': recent_admissions,
        'recent_documents': PatientDocument.objects.select_related('patient')
                                                 .order_by('-uploaded_at')[:5],
        'recent_wards': wards[:5],
        
        # Current date for the dashboard
        'current_date': timezone.now().strftime('%d %B %Y'),
    }
    
    return render(request, 'core/admin/dashboard.html', context)

class PatientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Patient
    template_name = 'core/admin/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('curator').prefetch_related('admissions')
        
        # Search functionality
        self.search_query = self.request.GET.get('q', '')
        if self.search_query:
            queryset = queryset.filter(
                Q(last_name__icontains=self.search_query) |
                Q(first_name__icontains=self.search_query) |
                Q(middle_name__icontains=self.search_query) |
                Q(phone_number__icontains=self.search_query) |
                Q(email__icontains=self.search_query) |
                Q(address__icontains=self.search_query)
            )
        
        # Filter by status
        self.status_filter = self.request.GET.get('status', '')
        if self.status_filter == 'admitted':
            queryset = queryset.filter(admissions__discharge_date__isnull=True)
        elif self.status_filter == 'discharged':
            queryset = queryset.filter(admissions__discharge_date__isnull=False)
        
        # Filter by gender
        self.gender_filter = self.request.GET.get('gender', '')
        if self.gender_filter in ['M', 'F']:
            queryset = queryset.filter(gender=self.gender_filter)
        
        # Filter by age group
        self.age_filter = self.request.GET.get('age', '')
        if self.age_filter == 'child':
            queryset = queryset.filter(age__lt=18)
        elif self.age_filter == 'adult':
            queryset = queryset.filter(age__range=(18, 65))
        elif self.age_filter == 'senior':
            queryset = queryset.filter(age__gt=65)
        
        # Ordering
        self.ordering = self.request.GET.get('ordering', 'last_name')
        if self.ordering in ['last_name', 'first_name', 'date_of_birth', 'created_at']:
            if self.ordering.startswith('-'):
                queryset = queryset.order_by(self.ordering)
            else:
                queryset = queryset.order_by(self.ordering)
        
        # Annotate with admission status
        queryset = queryset.annotate(
            is_admitted=Case(
                When(admissions__discharge_date__isnull=True, then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField()
            )
        )
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter parameters to context
        context.update({
            'search_query': self.search_query,
            'status_filter': self.status_filter,
            'gender_filter': self.gender_filter,
            'age_filter': self.age_filter,
            'current_ordering': self.ordering,
            'total_patients': self.get_queryset().count(),
            'admitted_count': Patient.objects.filter(admissions__discharge_date__isnull=True).count(),
            'discharged_count': Patient.objects.filter(admissions__discharge_date__isnull=False).count(),
            'gender_choices': Patient.GENDER_CHOICES,
        })
        
        return context

patient_list = PatientListView.as_view()

class PatientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Patient
    template_name = 'core/admin/patient_detail.html'
    context_object_name = 'patient'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        
        # Get current admission with related data
        current_admission = PatientAdmission.objects.filter(
            patient=patient,
            discharge_date__isnull=True
        ).select_related('bed__ward', 'doctor').first()
        
        # Get all admissions in reverse chronological order
        admission_history = PatientAdmission.objects.filter(
            patient=patient
        ).select_related('bed__ward', 'doctor').order_by('-admission_date')
        
        # Get patient documents with pagination
        documents = PatientDocument.objects.filter(
            patient=patient
        ).order_by('-uploaded_at')
        
        # Document form for uploads
        document_form = PatientDocumentForm()
        document_form.fields['document_type'].initial = 'other'
        
        # Admission form if needed
        admission_form = None
        if not current_admission:
            admission_form = PatientAdmissionForm()
            admission_form.fields['bed'].queryset = Bed.objects.filter(
                is_available=True
            ).select_related('ward')
        
        # Get related data
        related_patients = Patient.objects.filter(
            Q(phone_number=patient.phone_number) |
            Q(email=patient.email) |
            Q(address=patient.address)
        ).exclude(pk=patient.pk).distinct()
        
        # Get statistics
        total_admissions = admission_history.count()
        total_days = sum(
            (admission.discharge_date or timezone.now().date()) - admission.admission_date
            for admission in admission_history
            if admission.admission_date
        )
        
        context.update({
            'current_admission': current_admission,
            'admission_history': admission_history,
            'documents': documents,
            'document_form': document_form,
            'admission_form': admission_form,
            'related_patients': related_patients,
            'stats': {
                'total_admissions': total_admissions,
                'total_days': total_days.days if total_admissions > 0 else 0,
                'documents_count': documents.count(),
                'avg_stay_days': total_days.days // total_admissions if total_admissions > 0 else 0,
            },
            'now': timezone.now(),
        })
        
        return context

patient_detail_admin = PatientDetailView.as_view()

@method_decorator(csrf_exempt, name='dispatch')
class PatientDocumentUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PatientDocument
    form_class = PatientDocumentForm
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.patient_id = self.kwargs['pk']
        self.object = form.save()
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'document': {
                    'id': self.object.id,
                    'name': self.object.document.name.split('/')[-1],
                    'type': self.object.get_document_type_display(),
                    'uploaded_at': self.object.uploaded_at.strftime('%d.%m.%Y %H:%M'),
                    'url': self.object.document.url,
                }
            })
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('admin_panel:patient_detail', kwargs={'pk': self.kwargs['pk']})

@require_http_methods(['POST'])
@login_required
@staff_required
def delete_document(request, pk):
    document = get_object_or_404(PatientDocument, pk=pk)
    patient_pk = document.patient.pk
    document.delete()
    messages.success(request, 'Документ успешно удален')
    return redirect('admin_panel:patient_detail', pk=patient_pk)

# Admission Management
@login_required
@staff_required
def create_admission(request):
    if request.method == 'POST':
        form = PatientAdmissionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                admission = form.save(commit=False)
                admission.admitted_by = request.user
                admission.save()
                
                # Mark bed as occupied
                bed = admission.bed
                bed.is_available = False
                bed.save()
                
                messages.success(request, 'Пациент успешно госпитализирован')
                return redirect('admin_panel:patient_detail', pk=admission.patient.pk)
    else:
        form = PatientAdmissionForm()
    
    return render(request, 'core/admin/admission_form.html', {'form': form})

@login_required
@staff_required
def update_admission(request, pk):
    admission = get_object_or_404(PatientAdmission, pk=pk)
    old_bed = admission.bed
    
    if request.method == 'POST':
        form = PatientAdmissionForm(request.POST, instance=admission)
        if form.is_valid():
            with transaction.atomic():
                new_admission = form.save(commit=False)
                new_bed = new_admission.bed
                
                # If bed changed, update availability
                if old_bed != new_bed:
                    old_bed.is_available = True
                    old_bed.save()
                    new_bed.is_available = False
                    new_bed.save()
                
                new_admission.save()
                messages.success(request, 'Госпитализация успешно обновлена')
                return redirect('admin_panel:patient_detail', pk=admission.patient.pk)
    else:
        form = PatientAdmissionForm(instance=admission)
    
    return render(request, 'core/admin/admission_form.html', {
        'form': form,
        'admission': admission,
    })

@require_http_methods(['POST'])
@login_required
@staff_required
def discharge_patient(request, pk):
    admission = get_object_or_404(PatientAdmission, pk=pk)
    patient_pk = admission.patient.pk
    
    if not admission.discharge_date:
        with transaction.atomic():
            admission.discharge_date = timezone.now().date()
            admission.discharged_by = request.user
            admission.save()
            
            # Mark bed as available
            bed = admission.bed
            bed.is_available = True
            bed.save()
            
            messages.success(request, 'Пациент успешно выписан')
    
    return redirect('admin_panel:patient_detail', pk=patient_pk)

# API Endpoints
@login_required
@staff_required
def get_available_beds(request, ward_id):
    """API endpoint to get available beds for a ward"""
    beds = Bed.objects.filter(
        ward_id=ward_id,
        is_available=True
    ).values('id', 'bed_number')
    
    return JsonResponse({
        'success': True,
        'beds': list(beds)
    })

@login_required
@staff_required
def search_patients(request):
    """API endpoint for patient search with autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    patients = Patient.objects.filter(
        Q(last_name__icontains=query) |
        Q(first_name__icontains=query) |
        Q(phone_number__icontains=query) |
        Q(insurance_number__icontains=query)
    ).values('id', 'last_name', 'first_name', 'middle_name', 'birth_date')[:10]
    
    results = [{
        'id': p['id'],
        'text': f"{p['last_name']} {p['first_name']} {p.get('middle_name', '')} ({p['birth_date'].year if p['birth_date'] else 'н/д'})",
        'birth_date': p['birth_date'].strftime('%d.%m.%Y') if p['birth_date'] else 'н/д'
    } for p in patients]
    
    return JsonResponse({'results': results})
