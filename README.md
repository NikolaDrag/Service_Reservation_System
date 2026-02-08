# Система за резервации - Сервизи

REST API за резервация на часове в сервизи (смяна на масло, ремонт, диагностика).

## Инсталация

```bash
git clone <repo-url>
cd Service_Reservation_System

# Вариант 1: С pyproject.toml (препоръчително)
pip install -e .
pip install -e ".[dev]"   # + тестови инструменти

# Вариант 2: Класически
pip install -r requirements.txt
```

## Стартиране

```bash
python main.py
```

Сървърът стартира на **http://127.0.0.1:5000** (Flask default port).
Проверете demonstration.txt за примерни команди за използване на feature-ите.
GitHub линк към проекта: https://github.com/NikolaDrag/Service_Reservation_System

## Структура на проекта

```
├── models/           # Data Models & Business Logic
│   ├── user.py       # Потребителска йерархия (Guest/User/Provider/Admin)
│   ├── service.py    # Управление на услуги
│   ├── reservation.py # Резервации и график
│   ├── favorite.py   # Модул "Любими"
│   ├── review.py     # Модул "Ревюта"
│   └── notification.py # Модул "Известия"
├── routes/           # API Endpoints
│   ├── auth.py       # Аутентикация и профили
│   ├── services.py   # CRUD за услуги
│   ├── reservations.py # Резервационен процес
│   ├── favorites.py  # Endpoints за любими
│   ├── reviews.py    # Endpoints за ревюта
│   └── notifications.py # Endpoints за известия
├── tests/            # Тестове (Unit/Integration)
├── pyproject.toml    # Project metadata & dependencies
├── config.py         # App configuration
├── db.py             # Database initialization
└── main.py           # Application entry point
```

## Примерни акаунти

| Роля | Email | Парола |
|------|-------|--------|
| Admin | admin@reservations.com | admin123 |
| Provider | service@autoservice.bg | provider123 |

**Забележка:** При автоматичното създаване на базата, Admin получава `ID=1`, а Provider получава `ID=2`. Използвайте тези ID-та за хедъра `X-User-Id` в демонстрационните команди.

**Важно за сигурността:** Използвах `X-User-Id` хедър **само за целите на демонстрацията и тестването на API-то**, за да можем лесно да симулираме различни роли без нужда от сложна сесийна логика в curl скриптовете.

В реален Production код, това се премахва напълно и се заменя със система за сесии (Flask-Login) или JWT Токени, които са криптографски подписани със `SECRET_KEY`, за да се предотврати фалшификация на самоличността.

## Начални услуги

При стартиране автоматично се създават 5 демо услуги:  
- Смяна на масло (89.99 eur, 30 мин)
- Смяна на накладки (120 eur, 60 мин)
- Компютърна диагностика (45 eur, 30 мин)
- Смяна на гуми (40 eur, 45 мин)
- Годишен технически преглед (70 eur, 90 мин)

## Функционалности

### За сервизи:
- Резервация на час за обслужване/ремонт
- Избор на тип услуга и специалист (provider)
- Качване на снимки/описание на проблема (`problem_image_url`)
- Управление на график и свободни часове
- История на обслужванията

### Допълнителни модули:
- **Favorites**: Добавяне на услуги в "Любими" за бърз достъп.
- **Notifications**: Система за известия при промяна на статус на резервация.
- **Reviews**: Оставяне на отзиви и оценка за изпълнени услуги.

## Тестове (по принцип към pygrader-a)

```bash
# Изпълнение на тестове
python -m pytest tests/ -v

# Coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Pylint
pylint models/ routes/
```

## Технологии

- Flask 3.0
- SQLAlchemy 2.0
- SQLite
- Python 3.13
