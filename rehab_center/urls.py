"""
URL configuration for rehab_center project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from commissions.admin_site import admin_site as commissions_admin_site

# Use our custom admin site
urlpatterns = [
    path('admin/', commissions_admin_site.urls),

    # App URLs
    path('rehab/', include('rehab_programs.urls', namespace='rehab_programs')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('portal/', include('patient_portal.urls', namespace='patient_portal')),
    path('commissions/', include('commissions.urls', namespace='commissions')),
    path('emr/', include('emr.urls', namespace='emr')),
    path('medical/', include('medical_history.urls')),
    path('inpatient/', include('inpatient.urls', namespace='inpatient')),
    path('services/', include('services.urls', namespace='services')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('select2/', include('django_select2.urls')),

    # Auth URLs
    path('accounts/', include('django.contrib.auth.urls')),

    # Core URL (should be last)
    path('', include('core.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Auto-register all models with our custom admin site
from django.apps import apps
for app_config in apps.get_app_configs():
    app_models = app_config.get_models()
    for model in app_models:
        try:
            commissions_admin_site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
