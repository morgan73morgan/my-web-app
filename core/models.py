# -*- coding: utf-8 -*-
from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class SystemSettings(models.Model):
    """Singleton-модель для хранения системных настроек центра."""
    singleton_id = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    clinic_name = models.CharField(max_length=255, default="Реабилитационный центр", verbose_name=_('Название клиники'))
    timezone = models.CharField(max_length=64, default="Europe/Moscow", verbose_name=_('Часовой пояс'))
    date_format = models.CharField(max_length=32, default="DD.MM.YYYY", verbose_name=_('Формат даты'))
    language = models.CharField(max_length=8, default="ru", verbose_name=_('Язык'))
    maintenance_mode = models.BooleanField(default=False, verbose_name=_('Техническое обслуживание'))
    logo = models.ImageField(upload_to='branding/', blank=True, null=True, verbose_name=_('Логотип'))
    color_theme = models.CharField(max_length=32, default="default", verbose_name=_('Цветовая схема'))
    
    def save(self, *args, **kwargs):
        self.singleton_id = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(singleton_id=1)
        return obj
    
    class Meta:
        verbose_name = _('Системные настройки')
        verbose_name_plural = _('Системные настройки')

class IntegrationSettings(models.Model):
    """Модель для хранения ключей и параметров интеграций."""
    service_1c_url = models.URLField(blank=True, verbose_name=_('1С: URL сервиса'))
    service_1c_key = models.CharField(max_length=128, blank=True, verbose_name=_('1С: API-ключ'))
    sms_provider = models.CharField(max_length=64, blank=True, verbose_name=_('SMS-провайдер'))
    sms_api_key = models.CharField(max_length=128, blank=True, verbose_name=_('SMS API-ключ'))
    email_host = models.CharField(max_length=128, blank=True, verbose_name=_('SMTP сервер'))
    email_user = models.CharField(max_length=128, blank=True, verbose_name=_('SMTP пользователь'))
    email_password = models.CharField(max_length=128, blank=True, verbose_name=_('SMTP пароль'))
    webhook_url = models.URLField(blank=True, verbose_name=_('Webhook URL'))
    
    class Meta:
        verbose_name = _('Интеграции и API')
        verbose_name_plural = _('Интеграции и API')

class AuditLog(models.Model):
    """Модель для аудита изменений настроек и действий админов."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_('Пользователь'))
    action = models.CharField(max_length=255, verbose_name=_('Действие'))
    model = models.CharField(max_length=100, blank=True, verbose_name=_('Модель'))
    object_id = models.CharField(max_length=64, blank=True, verbose_name=_('ID объекта'))
    old_value = models.TextField(blank=True, verbose_name=_('Старое значение'))
    new_value = models.TextField(blank=True, verbose_name=_('Новое значение'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Время'))
    
    class Meta:
        verbose_name = _('Журнал аудита')
        verbose_name_plural = _('Журнал аудита')
        ordering = ['-timestamp']

class Staff(models.Model):
    STATUS_CHOICES = [
        ('active', _('Активен')),
        ('inactive', _('Неактивен')),
    ]
    first_name = models.CharField(max_length=100, verbose_name=_('Имя'))
    last_name = models.CharField(max_length=100, verbose_name=_('Фамилия'))
    middle_name = models.CharField(max_length=100, blank=True, verbose_name=_('Отчество'))
    position = models.CharField(max_length=100, verbose_name=_('Должность'))
    department = models.CharField(max_length=100, blank=True, verbose_name=_('Отдел'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    phone = models.CharField(max_length=30, blank=True, verbose_name=_('Телефон'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name=_('Статус'))
    hire_date = models.DateField(verbose_name=_('Дата приёма'))
    fire_date = models.DateField(null=True, blank=True, verbose_name=_('Дата увольнения'))
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_('Пользователь'))

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    class Meta:
        verbose_name = _('Сотрудник')
        verbose_name_plural = _('Сотрудники')
        ordering = ['last_name', 'first_name']

class Patient(models.Model):
    """
    Модель пациента реабилитационного центра.
    """
    GENDER_CHOICES = [
        ('M', _('Мужской')),
        ('F', _('Женский')),
    ]

    first_name = models.CharField(max_length=100, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=100, verbose_name=_("Фамилия"))
    middle_name = models.CharField(max_length=100, blank=True, verbose_name=_("Отчество"))
    date_of_birth = models.DateField(verbose_name=_("Дата рождения"))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name=_("Пол"))
    
    address = models.TextField(verbose_name=_("Адрес проживания"))
    phone_number = models.CharField(max_length=20, blank=True, verbose_name=_("Номер телефона"))
    email = models.EmailField(blank=True, verbose_name=_("Электронная почта"))

    # Учетная запись для входа в личный кабинет
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_profile', verbose_name=_("Учетная запись"))

    # Связь со специалистом (куратором)
    curator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='curating_patients', verbose_name=_("Куратор"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания записи"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления записи"))

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        """Возвращает полное имя пациента."""
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    class Meta:
        verbose_name = _("Пациент")
        verbose_name_plural = _("Пациенты")
        ordering = ['last_name', 'first_name']

def patient_directory_path(instance, filename):
    # Файл будет загружен в MEDIA_ROOT/patient_<id>/<filename>
    return f'patient_{instance.patient.id}/{filename}'

class PatientDocument(models.Model):
    """Модель для хранения документов пациента."""
    
    DOCUMENT_TYPES = [
        ('referral', _('Направление')),
        ('medical_report', _('Медицинское заключение')),
        ('test_results', _('Результаты анализов')),
        ('prescription', _('Рецепт')),
        ('insurance', _('Страховой полис')),
        ('id_document', _('Удостоверение личности')),
        ('consent', _('Согласие на лечение')),
        ('discharge_summary', _('Выписка из истории болезни')),
        ('other', _('Другое')),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents', verbose_name=_("Пациент"))
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        default='other',
        verbose_name=_("Тип документа")
    )
    description = models.CharField(max_length=255, verbose_name=_("Описание документа"), blank=True)
    document = models.FileField(
        upload_to=patient_directory_path, 
        verbose_name=_("Файл"),
        help_text=_("Поддерживаемые форматы: PDF, DOC, DOCX, JPG, PNG (макс. 10 МБ)")
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата загрузки"))
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='uploaded_documents',
        verbose_name=_("Загружено пользователем")
    )
    is_private = models.BooleanField(
        default=True,
        verbose_name=_("Конфиденциальный документ"),
        help_text=_("Если отмечено, документ будет виден только администраторам и лечащим врачам")
    )
    notes = models.TextField(blank=True, verbose_name=_("Примечания"))

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.patient.get_full_name()}"
        
    def save(self, *args, **kwargs):
        # При первом сохранении установить загрузившего пользователя
        if not self.pk and hasattr(self, 'request') and hasattr(self.request, 'user'):
            self.uploaded_by = self.request.user
        super().save(*args, **kwargs)
        
        # Обновить имя файла, чтобы включить ID документа
        if self.document and not self.document.name.startswith(f'patient_{self.patient.id}/{self.pk}_'):
            import os
            from django.core.files.storage import default_storage
            old_path = self.document.path
            file_extension = os.path.splitext(self.document.name)[1]
            new_name = f'patient_{self.patient.id}/{self.pk}_{self.document_type}{file_extension}'
            
            if default_storage.exists(old_path):
                new_path = default_storage.save(new_name, self.document.file)
                self.document.name = new_name
                super().save(update_fields=['document'])
                default_storage.delete(old_path)

    class Meta:
        verbose_name = _("Документ пациента")
        verbose_name_plural = _("Документы пациентов")
        ordering = ['-uploaded_at']
        permissions = [
            ('view_private_document', 'Может просматривать конфиденциальные документы'),
        ]


class Specialization(models.Model):
    """
    Модель для хранения специализаций врачей и других специалистов.
    """
    name = models.CharField(max_length=150, unique=True, verbose_name=_("Название специализации"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Специализация")
        verbose_name_plural = _("Специализации")
        ordering = ['name']


class SpecialistProfile(models.Model):
    """
    Профиль специалиста, расширяющий стандартную модель User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='specialist_profile', verbose_name=_("Пользователь"))
    specializations = models.ManyToManyField(Specialization, blank=True, verbose_name=_("Специализации"))
    bio = models.TextField(blank=True, verbose_name=_("Биография или заметки"))

    def __str__(self):
        return f"{self.user.get_full_name()} - {', '.join([s.name for s in self.specializations.all()])}"

    class Meta:
        verbose_name = _("Профиль специалиста")
        verbose_name_plural = _("Профили специалистов")


class Ward(models.Model):
    """
    Модель палаты в стационаре.
    """
    name = models.CharField(max_length=100, verbose_name=_("Название палаты"))
    department = models.CharField(max_length=100, blank=True, verbose_name=_("Отделение"))
    floor = models.PositiveSmallIntegerField(verbose_name=_("Этаж"), default=1)
    capacity = models.PositiveSmallIntegerField(verbose_name=_("Вместимость"), default=1)
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активна"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    def __str__(self):
        return f"{self.name} ({self.department or 'Общее'}) - {self.get_available_beds_count()}/{self.capacity} мест"

    def get_available_beds_count(self):
        """Возвращает количество свободных коек в палате."""
        return self.bed_set.filter(patient_admission__isnull=True).count()

    class Meta:
        verbose_name = _("Палата")
        verbose_name_plural = _("Палаты")
        ordering = ['department', 'name']


class Bed(models.Model):
    """
    Модель койки в палате.
    """
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, verbose_name=_("Палата"))
    number = models.CharField(max_length=20, verbose_name=_("Номер койки"))
    bed_type = models.CharField(
        max_length=50,
        choices=[
            ('standard', _('Стандартная')),
            ('intensive', _('Интенсивная терапия')),
            ('post_op', _('Послеоперационная')),
            ('isolation', _('Изоляционная')),
        ],
        default='standard',
        verbose_name=_("Тип койки")
    )
    is_available = models.BooleanField(default=True, verbose_name=_("Доступна"))
    notes = models.TextField(blank=True, verbose_name=_("Примечания"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    def __str__(self):
        return f"{self.ward.name} - {self.number}"

    @property
    def is_occupied(self):
        """Проверяет, занята ли койка."""
        return hasattr(self, 'patientadmission') and self.patientadmission.discharge_date is None

    class Meta:
        verbose_name = _("Койка")
        verbose_name_plural = _("Койки")
        ordering = ['ward__name', 'number']
        unique_together = [['ward', 'number']]


class PatientAdmission(models.Model):
    """
    Модель для учета госпитализаций пациентов.
    """
    ADMISSION_TYPES = [
        ('planned', _('Плановая')),
        ('emergency', _('Экстренная')),
        ('transfer', _('Перевод из другого учреждения')),
    ]

    PAYMENT_TYPES = [
        ('oms', _('ОМС')),
        ('dms', _('ДМС')),
        ('paid', _('Платно')),
        ('other', _('Иное')),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name=_("Пациент"), related_name='admissions')
    admission_type = models.CharField(
        max_length=20,
        choices=ADMISSION_TYPES,
        default='planned',
        verbose_name=_("Тип госпитализации")
    )
    admission_date = models.DateTimeField(verbose_name=_("Дата и время поступления"), default=timezone.now)
    discharge_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Дата и время выписки"))
    
    # Информация о койке
    ward = models.ForeignKey(
        Ward, 
        on_delete=models.SET_NULL,  # Changed from PROTECT to SET_NULL
        null=True,  # Allow NULL in database
        blank=True,  # Allow blank in forms
        verbose_name=_("Палата"), 
        related_name='admissions'
    )
    bed = models.OneToOneField(
        Bed, 
        on_delete=models.PROTECT, 
        verbose_name=_("Койка"), 
        related_name='patient_admission',
        null=True,
        blank=True
    )
    room_number = models.CharField(max_length=20, blank=True, verbose_name=_("Номер комнаты"))
    
    # Медицинская информация
    referral_diagnosis = models.TextField(blank=True, verbose_name=_("Диагноз при направлении"))
    diagnosis = models.TextField(blank=True, verbose_name=_("Клинический диагноз"))
    treatment_plan = models.TextField(blank=True, verbose_name=_("План лечения"))
    
    # Персонал
    attending_physician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attending_admissions',
        verbose_name=_("Лечащий врач")
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admitted_patients',
        verbose_name=_("Врач, оформивший госпитализацию")
    )
    
    # Страховая информация
    insurance_provider = models.CharField(max_length=100, blank=True, verbose_name=_("Страховая компания"))
    insurance_policy_number = models.CharField(max_length=50, blank=True, verbose_name=_("Номер полиса"))
    payment_type = models.CharField(
        max_length=10,
        choices=PAYMENT_TYPES,
        default='oms',
        verbose_name=_("Тип оплаты")
    )
    
    # Дополнительная информация
    notes = models.TextField(blank=True, verbose_name=_("Примечания"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активная госпитализация"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_admissions',
        verbose_name=_("Кем создана")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    def __str__(self):
        status = 'активна' if not self.discharge_date else 'завершена'
        return f"{self.patient} - {self.admission_date.strftime('%d.%m.%Y %H:%M')} ({status})"

    def save(self, *args, **kwargs):
        # При создании новой записи
        if not self.pk:
            # Автоматически отмечаем койку как занятую
            if self.bed:
                self.bed.is_available = False
                self.bed.save()
                if not self.ward_id:
                    self.ward = self.bed.ward
            # Сохраняем пользователя, создавшего запись
            from django.contrib.auth import get_user
            user = get_user(kwargs.get('request', None))
            if user and user.is_authenticated and not self.created_by_id:
                self.created_by = user
        
        # При выписке освобождаем койку
        elif self.discharge_date and not self._state.adding:
            self.is_active = False
            if self.bed:
                self.bed.is_available = True
                self.bed.save()
        
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Возвращает продолжительность госпитализации в днях."""
        end_date = self.discharge_date or timezone.now()
        duration = end_date - self.admission_date
        return duration.days

    class Meta:
        verbose_name = _("Госпитализация")
        verbose_name_plural = _("Госпитализации")
        ordering = ['-admission_date']
        indexes = [
            models.Index(fields=['admission_date']),
            models.Index(fields=['discharge_date']),
        ]
