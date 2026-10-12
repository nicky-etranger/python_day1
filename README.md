# Banking OOP Project

Учебный проект банковской системы на Python, последовательно развиваемый в течение 7 дней.

## Установка

```bash
python -m pip install -r requirements.txt
```

## День 1 — Базовая модель счетов

Реализованы `AbstractAccount` и `BankAccount`, статусы счетов, валюты, пополнение и снятие средств, валидация финансовых сумм и пользовательские исключения.

Файлы:
- `src/models.py`
- `src/utils.py`
- `src/main.py`
- `tests/test_main.py`

Запуск:

```bash
python src/main.py
python -m unittest tests/test_main.py
```

## День 2 — Продвинутые типы счетов

Добавлены `SavingsAccount`, `PremiumAccount` и `InvestmentAccount`: минимальный остаток, ежемесячные проценты, овердрафт, комиссии и инвестиционный портфель.

Файлы:
- `src/account_types.py`
- `src/main2.py`
- `tests/test_main2.py`

Запуск:

```bash
python src/main2.py
python -m unittest tests/test_main2.py
```

## День 3 — Система Bank

Добавлены клиенты и управляющий класс банка: открытие, закрытие, заморозка и разморозка счетов, поиск, аутентификация и блокировка после неудачных попыток входа.

Файлы:
- `src/client.py`
- `src/bank.py`
- `src/main3.py`
- `tests/test_main3.py`

Запуск:

```bash
python src/main3.py
python -m unittest tests/test_main3.py
```

## День 4 — Система транзакций

Реализованы транзакции, очередь с приоритетом и отложенным выполнением, отмена операций, комиссии, конвертация валют, повторные попытки и фиксация ошибок.

Файлы:
- `src/transaction.py`
- `src/transaction_queue.py`
- `src/transaction_processor.py`
- `src/main4.py`
- `tests/test_main4.py`

Запуск:

```bash
python src/main4.py
python -m unittest tests/test_main4.py
```

## День 5 — Аудит и риск-анализ

Добавлены журнал аудита, анализ подозрительных операций, уровни риска, блокировка опасных транзакций и отчёты по рискам и ошибкам.

Файлы:
- `src/audit.py`
- `src/risk.py`
- `src/audit_reports.py`
- `src/secure_transaction_processor.py`
- `src/main5.py`
- `tests/test_main5.py`

Запуск:

```bash
python src/main5.py
python -m unittest tests/test_main5.py
```

## День 6 — Демонстрационная программа

Создана комплексная симуляция банковской системы с клиентами, счетами, очередью транзакций, успешными, ошибочными и подозрительными операциями и итоговой статистикой.

Файлы:
- `src/demo.py`
- `src/main6.py`
- `tests/test_main6.py`

Запуск:

```bash
python src/main6.py
python -m unittest tests/test_main6.py
```

## День 7 — Отчётность и визуализация

Добавлена генерация отчётов по клиенту, банку и рискам в текстовом, JSON и CSV форматах, а также построение графиков через `matplotlib`.

Файлы:
- `src/report_builder.py`
- `src/main7.py`
- `tests/test_main7.py`

Запуск:

```bash
python src/main7.py
python -m unittest tests/test_main7.py
```

После запуска Дня 7 отчёты и графики сохраняются в директорию `reports_day7`.

## Все тесты

```bash
python -m unittest discover -s tests
```