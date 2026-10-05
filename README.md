# python_day1
Python day 1: OOP

проект с базовой объектной моделью банковских счетов.

Реализованы:

- абстрактный класс AbstractAccount;
- банковский счёт BankAccount;
- статусы active, frozen и closed;
- валюты RUB, USD, EUR, KZT и CNY;
- пополнение и снятие средств;
- проверка входящих данных;
- пользовательские исключения;
- автоматическая генерация короткого UUID;
- unit-тесты.

## Запуск

Из корневой директории проекта:

```bash
python src/main.py
```

Тесты:

```bash
python -m unittest discover -s tests
```

Логи запуска и тестов: tests/logs.txt