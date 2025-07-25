# Чек-лист соответствия МИС требованиям Росздравнадзора

## 1. Электронная медицинская карта (ЭМК)
- [x] Ведение ЭМК по приказам Минздрава (911н, 972н, 965н)
- [x] Хранение истории, диагнозов, назначений, анализов
- [x] Уникальный номер ЭМК, контроль доступа

## 2. Учёт медицинских услуг и ОМС
- [x] Учёт оказанных услуг (связь с пациентом, визитом, ЭМК)
- [x] Выгрузка реестров услуг в формате ФОМС (XML)
- [x] Справочник услуг, поддержка тарифов ОМС

## 3. Справочники
- [x] Импорт МКБ-10, номенклатуры услуг
- [x] Автозаполнение и валидация кодов

## 4. Отчетность
- [x] Формы №30, №12, выгрузка в Excel/PDF
- [x] REST API для отчетов

## 5. Интеграция с ЕГИСЗ, ОМС
- [x] REST и SOAP-интеграция с ЕГИСЗ Москвы
- [x] Логирование всех обменов (IntegrationLog)

## 6. Аудит и безопасность
- [x] Аудит действий пользователей (AuditLog)
- [x] Аудит интеграций (IntegrationLog)
- [x] RBAC, разграничение доступа, хранение логов >5 лет

## 7. Документация и шаблоны
- [x] Архитектура, примеры API, инструкции по интеграции и аудиту
- [x] Примеры выгрузки логов и отчетов

---

# Примеры выгрузки логов и отчетов

## Пример выгрузки лога AuditLog (CSV)
| id | user | action | model | object_id | timestamp |
|----|------|--------|-------|-----------|-----------|
| 1  | admin| export_report_30 | MedicalRecord | 123 | 2025-06-15 |

## Пример выгрузки IntegrationLog (CSV)
| id | user | operation | status | timestamp | error |
|----|------|-----------|--------|-----------|-------|
| 1  | admin| send_patient | success | 2025-06-15 | |

## Пример выгрузки отчета (форма 30, Excel)
| Организация | Период | Пациентов | Услуг |
|-------------|--------|-----------|-------|
| Медцентр    |2025-06-01| 123      | 456   |
