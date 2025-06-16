from django.db import models
from django.utils.translation import gettext_lazy as _

class ICD10Code(models.Model):
    """Модель для хранения кодов МКБ-10"""
    class Meta:
        verbose_name = _('Код МКБ-10')
        verbose_name_plural = _('Коды МКБ-10')
        ordering = ['code']
    
    code = models.CharField(_('Код'), max_length=10, unique=True)
    name = models.TextField(_('Наименование'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='children', verbose_name=_('Родительская категория'))
    is_category = models.BooleanField(_('Это категория?'), default=False)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
