# Диагностический центр - Веб-приложение и Telegram-бот

Комплексное решение для диагностического центра, включающее веб-приложение на Flask и Telegram-бота для взаимодействия с клиентами.

## 📋 Описание

Проект представляет собой гибридную систему, состоящую из:
- **Веб-приложение** на Flask с панелью администратора и личным кабинетом пользователя
- **Telegram-бот** для уведомлений и взаимодействия с клиентами
- **База данных** SQLite с миграциями через Alembic

## 🚀 Возможности

### Веб-приложение
- Личный кабинет пользователя с персональными данными
- Панель администратора с управлением пользователями и контентом
- Загрузка и управление файлами (до 50 МБ)
- Адаптивный дизайн

### Telegram-бот
- Уведомления о статусах заявок
- Взаимодействие с клиентами в реальном времени
- Фоновый запуск вместе с веб-приложением

## 🛠️ Технологии

- **Backend**: Python 3.x, Flask 2.3.3
- **База данных**: SQLite + SQLAlchemy 2.0
- **Миграции**: Flask-Migrate + Alembic
- **Telegram Bot**: python-telegram-bot 22.7
- **Асинхронность**: AnyIO 4.13.0
- **HTTP клиент**: HTTPX 0.28.1

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/majormguarde/diag_4.git
cd diag_4
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
```

### 3. Активация виртуального окружения

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

Создайте файл `.env` в корне проекта (можно скопировать с `.env.example` если есть) и настройте:

```env
SECRET_KEY=ваш_секретный_ключ
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

Или отредактируйте [`config.py`](config.py) напрямую.

### 6. Инициализация базы данных

```bash
flask db upgrade
```

Или через Python:
```python
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
```

## 🏃‍♂️ Запуск приложения

### Основной способ (рекомендуется)

```bash
python run.py
```

Приложение будет доступно по адресу: `http://localhost:5000`

### Отдельный запуск Flask

```bash
flask run
```

### Для разработки с автоперезагрузкой

```bash
python run.py
# или
set DEBUG=True && python run.py  # Windows
export DEBUG=True && python run.py  # Linux/Mac
```

## 📁 Структура проекта

```
diag_4/
├── app/                      # Основное приложение
│   ├── __init__.py          # Фабрика приложения
│   ├── models.py            # Модели базы данных
│   ├── routes.py            # Основные маршруты
│   ├── admin_routes.py      # Маршруты админ-панели
│   ├── bot.py              # Telegram-бот
│   ├── router.py           # Дополнительная маршрутизация
│   ├── static/             # Статические files
│   │   ├── css/           # Стили
│   │   └── js/            # JavaScript
│   └── templates/          # HTML шаблоны
│       └── admin/         # Шаблоны админки
├── migrations/             # Миграции базы данных
├── config.py              # Конфигурация
├── run.py                 # Точка входа
├── requirements.txt       # Зависимости
└── .env                   # Переменные окружения
```

## 🔧 Конфигурация

Основные настройки в [`config.py`](config.py):

- `SECRET_KEY` - секретный ключ для сессий
- `SQLALCHEMY_DATABASE_URI` - строка подключения к БД (по умолчанию SQLite)
- `TELEGRAM_BOT_TOKEN` - токен Telegram-бота
- `UPLOAD_FOLDER` - папка для загрузок
- `MAX_CONTENT_LENGTH` - максимальный размер загружаемых файлов (50 МБ)

## 🗄️ Миграции базы данных

### Создание новой миграции

```bash
flask db migrate -m "Описание изменений"
```

### Применение миграций

```bash
flask db upgrade
```

### Откат миграций

```bash
flask db downgrade
```

## 👥 Администрирование

### Доступ к админ-панели

1. Перейдите по адресу `/admin`
2. Используйте учетные данные администратора

### Создание первого администратора

Через Python консоль:
```python
from app import create_app, db
from app.models import Admin
app = create_app()
with app.app_context():
    admin = Admin(username='admin', email='admin@example.com')
    admin.set_password('ваш_пароль')
    db.session.add(admin)
    db.session.commit()
```

## 🤖 Telegram-бот

Бот запускается автоматически вместе с приложением в фоновом потоке.

### Команды бота

- `/start` - начало работы
- `/help` - справка
- `/status` - проверка статуса

### Настройка бота

1. Получите токен у [@BotFather](https://t.me/botfather)
2. Установите токен в `.env` или `config.py`
3. Запустите приложение

## 📝 Лицензия

Проект создан для диагностического центра. Все права защищены.

## 🤝 Вклад в проект

1. Создайте ветку для новой фичи (`git checkout -b feature/amazing-feature`)
2. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
3. Отправьте в удаленный репозиторий (`git push origin feature/amazing-feature`)
4. Создайте Pull Request

## 📞 Контакты

- GitHub: [@majormguarde](https://github.com/majormguarde)
- Репозиторий: [diag_4](https://github.com/majormguarde/diag_4)

---

*Проект находится в разработке. Некоторые функции могут быть изменены.*