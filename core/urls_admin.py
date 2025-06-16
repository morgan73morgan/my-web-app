from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views_admin

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views_admin.admin_dashboard, name='dashboard'),
    
    # Patients
    path('patients/', views_admin.patient_list, name='patient_list'),
    path('patients/<int:pk>/', views_admin.patient_detail_admin, name='patient_detail'),
    
    # Documents
    path('patients/<int:pk>/documents/upload/', 
         views_admin.PatientDocumentUploadView.as_view(), 
         name='upload_document'),
    path('documents/<int:pk>/delete/', 
         views_admin.delete_document, 
         name='delete_document'),
    
    # Admissions
    path('admissions/create/', 
         views_admin.create_admission, 
         name='create_admission'),
    path('admissions/<int:pk>/update/', 
         views_admin.update_admission, 
         name='update_admission'),
    path('admissions/<int:pk>/discharge/', 
         views_admin.discharge_patient, 
         name='discharge_patient'),
    
    # API Endpoints
    path('api/wards/<int:ward_id>/beds/', 
         views_admin.get_available_beds, 
         name='api_ward_beds'),
    path('api/patients/search/', 
         views_admin.search_patients, 
         name='api_patient_search'),
]    # Add more admin URLs here
