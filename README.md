# Система за резервации - Автосервизи

REST API за резервация на часове в автосервизи (смяна на масло, ремонт, диагностика).

## Функционалности

### За автосервизи:
- Резервация на час за обслужване/ремонт
- Избор на тип услуга и специалист (provider)
- Качване на снимки/описание на проблема (`problem_image_url`)
- Управление на график и свободни часове
- История на обслужванията

### Допълнителни:
- Favorites (любими услуги)
- Notifications (известия за резервации)
- Reviews (ревюта)

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

## API Endpoints

### Резервации
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /api/reservations/available-slots?service_id=1&date=2026-02-10 | Свободни часове |
| GET | /api/reservations/history | История на обслужвания |
| POST | /api/reservations | Нова резервация (с `problem_image_url`) |

### Favorites
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /api/favorites | Списък любими услуги |
| POST | /api/favorites | Добави любима |
| DELETE | /api/favorites/:service_id | Премахни любима |

### Notifications
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /api/notifications | Списък известия |
| PUT | /api/notifications/:id/read | Маркирай прочетено |
| PUT | /api/notifications/read-all | Маркирай всички прочетени |

## Примерни акаунти

| Роля | Email | Парола |
|------|-------|--------|
| Admin | admin@reservations.com | admin123 |
| Provider | service@autoservice.bg | provider123 |

## Начални услуги

При стартиране автоматично се създават 5 демо услуги:
- Смяна на масло (89.99 лв, 30 мин)
- Смяна на накладки (120 лв, 60 мин)
- Компютърна диагностика (45 лв, 30 мин)
- Смяна на гуми (40 лв, 45 мин)
- Годишен технически преглед (70 лв, 90 мин)

## Тестове

```bash
# Изпълнение на тестове
python -m pytest tests/ -v

# Coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Pylint
pylint models/ routes/
```

## Структура

```
├── models/           # Модели: Guest → RegisteredUser → Provider → Admin
│   ├── user.py       # Наследяване на потребители
│   ├── service.py    # Услуги
│   ├── reservation.py # Резервации (с problem_image_url)
│   ├── favorite.py   # Любими услуги
│   └── notification.py # Известия
├── routes/           # API endpoints
│   ├── reservations.py # available-slots, history
│   ├── favorites.py  # Favorites CRUD
│   └── notifications.py # Notifications CRUD
├── tests/            # 219 теста, 92% coverage
├── pyproject.toml    # Конфигурация
└── main.py           # Entry point
```

## Технологии

- Flask 3.0
- SQLAlchemy 2.0
- SQLite
- Python 3.13