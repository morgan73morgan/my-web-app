from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse
import csv

from guardian.admin import GuardedModelAdmin

# --- audit-log ---
from auditlog.registry import auditlog
from auditlog.models import LogEntry as AuditLog

# --- project models ---
from .models import (
    Patient,
    PatientDocument,
    Specialization,
    SpecialistProfile,
    Ward,
    Bed,
    PatientAdmission,
    SystemSettings,
    IntegrationSettings,
)
from documents.models import Document

# ---------------------------------------------------------------------------
#  Audit Log admin
# ---------------------------------------------------------------------------
# Сначала убираем регистрацию, которую автоматически сделал django-auditlog,
# чтобы избежать AlreadyRegistered.
try:
    admin.site.unregister(AuditLog)
except admin.sites.NotRegistered:
    pass


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "actor", "action", "content_type", "object_pk")
    list_filter = ("action", "actor", "content_type", "timestamp")
    search_fields = ("action", "actor__username", "object_pk", "changes")
    date_hierarchy = "timestamp"
    readonly_fields = [f.name for f in AuditLog._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
#  Inlines
# ---------------------------------------------------------------------------
class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = (
        "title",
        "category",
        "status",
        "file",
        "approved_by",
        "approved_at",
        "created_at",
        "download_link",
    )
    readonly_fields = ("created_at", "approved_by", "approved_at", "download_link")
    show_change_link = True
    can_delete = False

    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>Скачать</a>', obj.file.url)
        return "-"

    download_link.short_description = "Скачать файл"


class BedInline(admin.TabularInline):
    model = Bed
    extra = 1
    fields = ("number", "bed_type", "is_available", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("number",)


class PatientAdmissionInline(admin.TabularInline):
    model = PatientAdmission
    extra = 0
    fields = (
        "patient",
        "admission_date",
        "discharge_date",
        "doctor",
        "diagnosis_short",
    )
    readonly_fields = ("admission_date", "diagnosis_short")
    ordering = ("-admission_date",)

    def diagnosis_short(self, obj):
        return (
            obj.diagnosis[:50] + "..."
            if obj.diagnosis and len(obj.diagnosis) > 50
            else obj.diagnosis or "-"
        )

    diagnosis_short.short_description = "Диагноз (кратко)"


# ---------------------------------------------------------------------------
#  Filters
# ---------------------------------------------------------------------------
class DocumentCountFilter(admin.SimpleListFilter):
    title = "Количество документов"
    parameter_name = "document_count"

    def lookups(self, request, model_admin):
        return [
            ("0", "Нет документов"),
            ("1-5", "1-5"),
            ("6-20", "6-20"),
            ("21+", "21 и более"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.annotate(doc_count=Count("documents")).filter(doc_count=0)
        if self.value() == "1-5":
            return queryset.annotate(doc_count=Count("documents")).filter(
                doc_count__gte=1, doc_count__lte=5
            )
        if self.value() == "6-20":
            return queryset.annotate(doc_count=Count("documents")).filter(
                doc_count__gte=6, doc_count__lte=20
            )
        if self.value() == "21+":
            return queryset.annotate(doc_count=Count("documents")).filter(
                doc_count__gte=21
            )
        return queryset


# ---------------------------------------------------------------------------
#  Patient admin
# ---------------------------------------------------------------------------
@admin.register(Patient)
class PatientAdmin(GuardedModelAdmin):
    list_display = (
        "get_full_name",
        "date_of_birth",
        "phone_number",
        "email",
        "document_count",
        "documents_link",
    )
    list_filter = ("gender", "user__is_active", DocumentCountFilter)
    search_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "phone_number",
        "email",
        "insurance_number",
    )
    date_hierarchy = "created_at"
    inlines = [DocumentInline]
    fieldsets = (
        (_("Personal Information"), {"fields": ("last_name", "first_name", "middle_name", "date_of_birth", "gender")}),
        (_("Contacts"), {"fields": ("phone_number", "email", "insurance_number")}),
        (_("Extra"), {"fields": ("user",)}),
    )
    actions = ["export_as_csv"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = "ФИО"
    get_full_name.admin_order_field = "last_name"

    def document_count(self, obj):
        return obj.documents.count()

    document_count.short_description = "Документов"

    def documents_link(self, obj):
        url = (
            f"/admin/documents/document/?patient__id__exact={obj.pk}"
        )
        return format_html(f'<a href="{url}">Смотреть ({obj.documents.count()})</a>')

    documents_link.short_description = "Документы"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename=patients.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Экспортировать выбранных пациентов в CSV"


# ---------------------------------------------------------------------------
#  Ward admin
# ---------------------------------------------------------------------------
@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "department",
        "floor",
        "capacity",
        "available_beds",
        "is_active",
    )
    list_filter = ("department", "floor", "is_active")
    search_fields = ("name", "department", "description")
    inlines = [BedInline]
    actions = ["export_as_csv", "activate_wards", "deactivate_wards"]

    def available_beds(self, obj):
        return obj.beds.filter(is_available=True).count()

    available_beds.short_description = "Свободно коек"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename=wards.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Экспортировать выбранные палаты в CSV"

    def activate_wards(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано палат: {updated}")

    activate_wards.short_description = "Активировать выбранные палаты"

    def deactivate_wards(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано палат: {updated}")

    deactivate_wards.short_description = "Деактивировать выбранные палаты"


# ---------------------------------------------------------------------------
#  Bed admin
# ---------------------------------------------------------------------------
@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "ward_name",
        "bed_type_display",
        "status",
        "current_patient",
        "admission_date",
        "is_available",
    )
    list_filter = ("ward", "bed_type", "is_available")
    search_fields = ("number", "ward__name")
    date_hierarchy = "created_at"
    actions = ["export_as_csv", "set_beds_available", "set_beds_unavailable"]
    autocomplete_fields = ["ward"]

    def ward_name(self, obj):
        return obj.ward.name

    ward_name.short_description = "Палата"
    ward_name.admin_order_field = "ward__name"

    def bed_type_display(self, obj):
        return obj.get_bed_type_display()

    bed_type_display.short_description = "Тип"

    def status(self, obj):
        return "Занята" if not obj.is_available else "Свободна"

    status.short_description = "Статус"

    def current_patient(self, obj):
        if hasattr(obj, "patientadmission") and obj.patientadmission.patient:
            return f"{obj.patientadmission.patient.get_full_name()}"
        return "-"

    current_patient.short_description = "Пациент"

    def admission_date(self, obj):
        if hasattr(obj, "patientadmission") and obj.patientadmission.admission_date:
            return obj.patientadmission.admission_date.strftime("%d.%m.%Y")
        return "-"

    admission_date.short_description = "Дата поступления"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename=beds.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Экспортировать выбранные койки в CSV"

    def set_beds_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'Коек переведено в "Свободна": {updated}')

    set_beds_available.short_description = 'Отметить "Свободна"'

    def set_beds_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'Коек переведено в "Не доступна": {updated}')

    set_beds_unavailable.short_description = 'Отметить "Не доступна"'


# ---------------------------------------------------------------------------
#  Patient Admission admin
# ---------------------------------------------------------------------------
@admin.register(PatientAdmission)
class PatientAdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "patient_name",
        "bed_info",
        "admission_date",
        "discharge_date",
        "doctor_info",
        "diagnosis_short",
    )
    list_filter = ("admission_date", "discharge_date", "doctor", "bed")
    search_fields = (
        "patient__last_name",
        "patient__first_name",
        "bed__number",
        "bed__ward__name",
        "diagnosis",
    )
    list_select_related = ("patient", "bed__ward", "doctor")
    date_hierarchy = "admission_date"
    actions = ["export_as_csv", "discharge_selected"]
    autocomplete_fields = ["patient", "bed", "doctor"]

    def patient_name(self, obj):
        return obj.patient.get_full_name()

    patient_name.short_description = "Пациент"
    patient_name.admin_order_field = "patient__last_name"

    def bed_info(self, obj):
        return f"{obj.bed.ward.name}, койка {obj.bed.number}"

    bed_info.short_description = "Место размещения"
    bed_info.admin_order_field = "bed__ward__name"

    def doctor_info(self, obj):
        return obj.doctor.get_full_name() if obj.doctor else "-"

    doctor_info.short_description = "Лечащий врач"

    def diagnosis_short(self, obj):
        return (
            obj.diagnosis[:50] + "..."
            if obj.diagnosis and len(obj.diagnosis) > 50
            else obj.diagnosis or "—"
        )

    diagnosis_short.short_description = "Диагноз"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename=admissions.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Экспортировать выбранные госпитализации в CSV"

    def discharge_selected(self, request, queryset):
        updated = queryset.update(discharge_date=timezone.now())
        self.message_user(request, f"Выписано пациентов: {updated}")

    discharge_selected.short_description = "Выписать выбранных пациентов"


# ---------------------------------------------------------------------------
#  Patient Document admin
# ---------------------------------------------------------------------------
@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ("patient", "description", "uploaded_at", "file_link")
    list_filter = ("patient", "uploaded_at")
    search_fields = ("description", "patient__last_name", "patient__first_name")
    actions = ["export_as_csv"]
    autocomplete_fields = ["patient"]

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>Скачать</a>', obj.file.url)
        return "-"

    file_link.short_description = "Файл"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename=patient_documents.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Экспортировать документы в CSV"


# ---------------------------------------------------------------------------
#  Specialization & SpecialistProfile admins
# ---------------------------------------------------------------------------
@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_specializations")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    raw_id_fields = ("user",)
    filter_horizontal = ("specializations",)

    def get_specializations(self, obj):
        return ", ".join(s.name for s in obj.specializations.all())

    get_specializations.short_description = "Специализации"


# ---------------------------------------------------------------------------
#  Simple model registrations
# ---------------------------------------------------------------------------
admin.site.register(SystemSettings)
admin.site.register(IntegrationSettings)

# ---------------------------------------------------------------------------
#  audit-log registrations for business models
# ---------------------------------------------------------------------------
auditlog.register(Patient)
auditlog.register(PatientDocument)
auditlog.register(Ward)
auditlog.register(Bed)
auditlog.register(PatientAdmission)