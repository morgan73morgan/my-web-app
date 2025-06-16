import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from medical_codes.models import ICD10Code

# Путь к файлу с данными МКБ-10
DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data',
    'icd10_data.txt'
)

class Command(BaseCommand):
    help = 'Импорт кодов МКБ-10 из внешнего источника'
    
    def handle(self, *args, **options):
        """
        Импортирует коды МКБ-10 из локального файла.
        """
        self.stdout.write('Начало импорта кодов МКБ-10...')
        
        try:
            # Проверяем существование файла
            if not os.path.exists(DATA_FILE):
                raise FileNotFoundError(f'Файл с данными МКБ-10 не найден: {DATA_FILE}')
            
            # Очищаем существующие данные
            self.stdout.write('Очистка старых данных...')
            ICD10Code.objects.all().delete()
            
            # Словарь для хранения родительских категорий
            categories = {}
            
            # Читаем данные из файла
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Обрабатываем каждую строку
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Парсим строку (формат: КОД[\t]НАИМЕНОВАНИЕ)
                parts = re.split(r'\t+', line, maxsplit=1)
                if len(parts) != 2:
                    continue
                    
                code, name = parts
                code = code.strip()
                name = name.strip()
                
                # Определяем, является ли запись категорией (A00-B99)
                is_category = bool(re.match(r'^[A-Z]\d{2}-[A-Z]\d{2}$', code))
                
                # Создаем или обновляем запись
                with transaction.atomic():
                    if is_category:
                        # Это категория, сохраняем её
                        category = ICD10Code.objects.create(
                            code=code,
                            name=name,
                            is_category=True
                        )
                        categories[code] = category
                        self.stdout.write(f'Добавлена категория: {code} - {name}')
                    else:
                        # Это конкретный код, находим родительскую категорию
                        parent_code = f"{code[0]}00-{code[0]}99"
                        parent = categories.get(parent_code)
                        
                        ICD10Code.objects.create(
                            code=code,
                            name=name,
                            parent=parent,
                            is_category=False
                        )
            
            self.stdout.write(self.style.SUCCESS('Импорт кодов МКБ-10 успешно завершен!'))
            
        except Exception as e:
            self.stderr.write(f'Ошибка при импорте кодов МКБ-10: {str(e)}')
