# secDB Portal

Полноценный веб-сайт на FastAPI с PostgreSQL (secDB).

## Что реализовано

- Регистрация и авторизация пользователей
- Роли:
  - EXECUTOR (Исполнитель): создает/редактирует только свои заявки и изделия, меняет рабочие статусы
  - SERVICE_MANAGER (Руководитель службы): видит и редактирует все записи, принимает первое решение
  - CENTER_MANAGER (Руководитель центра): просматривает записи, принимает второе обязательное решение
  - ADMIN (Администратор): создает пользователей, назначает роли, управляет справочниками и настройками
- Веб-интерфейс и API
- Автосоздание таблиц приложения при старте

В проект добавлен отдельный backend на FastAPI в папке `fastapi_app/`.

1. Установить Python зависимости:

   pip install -r requirements-fastapi.txt

2. Убедиться, что PostgreSQL поднят:

   docker compose up -d

3. (Опционально) задать секрет JWT:

   JWT_SECRET="your_secret_key"

4. Запустить FastAPI сервер:

   uvicorn fastapi_app.main:app --reload --port 8011

5. Swagger/OpenAPI:

   http://localhost:8000/docs

6. Веб-интерфейс (FastAPI + Jinja2):

   http://localhost:8011/web/login

Примечание: API использует существующий `DATABASE_URL` из `.env` и автоматически создает таблицы `*_py` при старте.
Если в базе еще нет админа, при старте автоматически создается:

- Email: admin@sec.local
- Пароль: Admin123!

Переопределить можно переменными `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`, `DEFAULT_ADMIN_NAME`.

### Разделы веб-сайта

- `/web/register` и `/web/login` - регистрация и вход
- `/web/dashboard` - сводная панель
- `/web/requests` - заявки (с ролевыми действиями)
- `/web/products` - изделия (с ролевыми действиями)
- `/web/users` - управление пользователями и ролями (только ADMIN)
- `/web/admin` - справочники и настройки (только ADMIN)

## Данные администратора по умолчанию

- Email: admin@sec.local
- Пароль: Admin123!
