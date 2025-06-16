from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from . import views
from .views_theme import toggle_theme

app_name = 'core'

# Admin URLs (using custom admin site)
admin_urls = [
    path('', include('core.urls_admin')),
    # Add more admin-related URLs here
]

# Main site URLs
urlpatterns = [
    # Paid services module
    path('services/', include('services.urls')),
    # Public pages
    path('', views.dashboard, name='dashboard'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='core/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:dashboard'), name='logout'),
    
    # Admin panel
    path('admin-panel/', include(admin_urls)),
    
    # Patient management
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_create, name='patient_add'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_update, name='patient_edit'),
    
    # Bed management
    path('bed-management/', views.bed_management, name='bed_management'),
    path('wards/add/', views.WardCreateView.as_view(), name='ward_create'),
    path('wards/<int:pk>/edit/', views.WardUpdateView.as_view(), name='ward_update'),
    path('wards/<int:pk>/delete/', views.WardDeleteView.as_view(), name='ward_delete'),
    path('wards/<int:ward_id>/beds/add/', views.BedCreateView.as_view(), name='bed_create'),
    path('beds/<int:pk>/edit/', views.BedUpdateView.as_view(), name='bed_update'),
    path('beds/<int:pk>/delete/', views.BedDeleteView.as_view(), name='bed_delete'),
    path('beds/<int:bed_id>/admission/', views.AdmissionCreateView.as_view(), name='admission_create'),
    path('admissions/<int:pk>/discharge/', views.AdmissionDischargeView.as_view(), name='admission_discharge'),
    path('admissions/<int:patient_id>/history/', views.AdmissionHistoryView.as_view(), name='admission_history'),
    
    # Calendar
    path('calendar/', TemplateView.as_view(template_name='core/calendar.html'), name='calendar'),
    
    # Programs
    path('programs/', TemplateView.as_view(template_name='core/programs.html'), name='programs'),
    
    # Reports
    path('reports/', TemplateView.as_view(template_name='core/reports.html'), name='reports'),
    
    # Staff
    path('staff/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/add/', views.StaffCreateView.as_view(), name='staff_create'),
    path('staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('staff/<int:pk>/delete/', views.StaffDeleteView.as_view(), name='staff_delete'),
    
    # Documents
    path('documents/', TemplateView.as_view(template_name='core/documents.html'), name='documents'),
    
    # Settings
    path('settings/', views.settings_hub, name='settings'),
    path('create_user/', views.create_user, name='create_user'),
    path('edit_user/<int:pk>/', views.edit_user, name='edit_user'),
    path('delete_user/<int:pk>/', views.delete_user, name='delete_user'),
    path('change_user_role/<int:pk>/', views.change_user_role, name='change_user_role'),
    path('set_theme/', views.set_theme, name='set_theme'),
    
    # Export/Import
    path('export_patients/', views.export_patients, name='export_patients'),
    path('import_patients/', views.import_patients, name='import_patients'),
    path('export_admissions/', views.export_admissions, name='export_admissions'),
    path('import_admissions/', views.import_admissions, name='import_admissions'),
    
    # Django admin (kept for superusers)
    path('django-admin/', admin.site.urls),
    
    # Theme toggle
    path('theme/toggle/', require_POST(toggle_theme), name='theme_toggle'),
]
