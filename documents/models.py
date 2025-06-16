from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# Assuming the Patient model is in the 'core' app.
# If not, this import will need to be adjusted.
from core.models import Patient

User = get_user_model()

class DocumentCategory(models.Model):
    """
    A category for organizing documents, e.g., 'Medical Records', 'Contracts'.
    """
    name = models.CharField(_('Category Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)

    class Meta:
        verbose_name = _('Document Category')
        verbose_name_plural = _('Document Categories')
        ordering = ['name']

    def __str__(self):
        return self.name

def get_document_upload_path(instance, filename):
    """
    Generates the upload path for a document file.
    Files will be stored in: MEDIA_ROOT/documents/<patient_id>/<filename>
    """
    return f'documents/{instance.patient.id}/{filename}'

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Document(models.Model):
    description = models.TextField('Описание', blank=True)
    """
    Represents a single document in the system.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending_approval', _('Pending Approval')),
        ('approved', _('Approved')),
        ('archived', _('Archived')),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='managed_documents',
        verbose_name=_('Patient')
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Category')
    )
    title = models.CharField(_('Title'), max_length=255)
    file = models.FileField(_('File'), upload_to=get_document_upload_path)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_uploaded_documents',
        verbose_name=_('Uploaded by')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_documents',
        verbose_name=_('Approved by')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved at')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-created_at']
        permissions = [
            ('approve_document', _('Can approve document')),
        ]

    def __str__(self):
        return f'{self.title} - {self.patient.get_full_name()}'

class DocumentVersion(models.Model):
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='versions', verbose_name='Оригинал документа')
    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    file = models.FileField('Файл', upload_to='document_versions/', blank=True, null=True)
    status = models.CharField('Статус', max_length=32)
    category = models.ForeignKey('DocumentCategory', on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey('core.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Изменил')
    created_at = models.DateTimeField('Дата версии', auto_now_add=True)

    class Meta:
        verbose_name = 'Версия документа'
        verbose_name_plural = 'Версии документа'
        ordering = ['-created_at']

    def __str__(self):
        return f"Версия {self.title} ({self.created_at:%d.%m.%Y %H:%M})"

from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Document)
def create_document_version(sender, instance, **kwargs):
    if not instance.pk:
        return  # Не создавать версию для новых документов
    try:
        old = Document.objects.get(pk=instance.pk)
    except Document.DoesNotExist:
        return
    # Сохраняем только если есть изменения
    fields = ['title', 'description', 'file', 'status', 'category', 'patient']
    changed = any(getattr(old, f) != getattr(instance, f) for f in fields)
    if changed:
        DocumentVersion.objects.create(
            document=old,
            title=old.title,
            description=old.description,
            file=old.file,
            status=old.status,
            category=old.category,
            patient=old.patient,
            changed_by=getattr(instance, '_changed_by', None)
        )
