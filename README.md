# Custom Authentication & Authorization System (FastAPI)

Backend-приложение с собственной системой аутентификации и авторизации, реализованной **без полного использования готовых framework-based решений "из коробки"**.

Проект демонстрирует кастомный подход к:

* хранению JWT токенов в Cookie;
* разграничению прав доступа через таблицу правил `AccessRule`;
* управлению ролями пользователей;
* blacklist/logout механизму;
* refresh-token flow;
* централизованной системе доступа к бизнес-ресурсам.

---

# Технологии

* **Python 3.12+**
* **FastAPI**
* **SQLAlchemy Async**
* **PostgreSQL**
* **JWT (PyJWT)**
* **bcrypt**
* **Pydantic**

---

# Архитектура проекта

Проект построен по многослойной архитектуре:

```text
apps/
│
├── user/
│   ├── models.py
│   ├── schemas.py
│   ├── repository.py
│   ├── services.py
│   ├── controllers.py
│   └── routers.py
│
├── auth/
│   ├── models.py
│   ├── schemas.py
│   ├── repository.py
│   ├── services.py
│   ├── controllers.py
│   └── routers.py
│
├── admin/
│   └── ...
│
routers/
│   └── api_v1_router.py
│
settings/
│   └── settings.py
│
utils/
│   └── ...
│
main.py
```

---

# Архитектурные слои

## Controllers

Обрабатывают HTTP-запросы и формируют HTTP-ответы.

## Services

Содержат бизнес-логику приложения.

## Repository

Инкапсулируют взаимодействие с БД.

## Models

SQLAlchemy ORM модели.

## Schemas

Pydantic DTO / валидация запросов и ответов.

---

# Аутентификация

## Основа решения

В проекте используется **JWT-based authentication**.

### Почему JWT хранится в Cookie?

Поскольку предполагаемый клиент — **браузер**, JWT хранится в:

* **HttpOnly Cookie**
* **Secure Cookie** (при HTTPS)
* **SameSite Cookie**

Это позволяет:

* защититься от XSS-доступа к токену;
* автоматически отправлять токен браузером;
* реализовать browser-friendly authentication flow.

---

## JWT Payload

JWT содержит:

```json
{
  "user_id": 123,
  "role_id": 2,
  "exp": 9999999999
}
```

---

# Refresh Token

При логине создаются:

* **Access Token**
* **Refresh Token**

Refresh Token используется для:

* продления access token без повторного ввода логина/пароля;
* реализации долгоживущих сессий.

---

# Logout / Blacklist

При logout:

1. JWT токен заносится в таблицу **BlacklistedToken**
2. Cookie удаляется у клиента

Таким образом:

> Даже если злоумышленник сохранил токен до logout, использовать его повторно невозможно.

---

# Основные Flow

## Регистрация пользователя

```http
POST /reg
```

### Назначение:

Создание нового пользователя.

### Особенности:

* email должен быть уникален;
* пароль хэшируется через bcrypt;
* пользователь сохраняется в БД.

---

## Авторизация

```http
POST /login
```

### Назначение:

Вход пользователя в систему.

### Flow:

1. Проверка email/password
2. Генерация access token
3. Генерация refresh token
4. Сохранение JWT в Cookie

---

## Logout

```http
GET /log_out
```

### Flow:

1. Текущий JWT добавляется в Blacklist
2. Cookie удаляется у клиента

---

## Заполнение БД тестовыми данными

```http
POST /fill_db
```

### Назначение:

Заполняет таблицы:

* `roles`
* `business_elements`
* `access_role_rules`

из JSON файла в корне проекта.

### Важно:

Таблица `users` **не заполняется автоматически**, чтобы:

* можно было вручную создавать пользователей;
* тестировать разные роли через `/reg`.

---

# Авторизация / Система разграничения прав доступа

## Основная идея

В проекте реализована кастомная система **RBAC-like Authorization**.

---

# Таблица AccessRule

Основой управления доступом является таблица:

```text
access_role_rules
```

---

## Структура AccessRule

| Поле                  | Назначение                 |
| --------------------- | -------------------------- |
| role_id               | Роль пользователя          |
| element_id            | Бизнес-элемент             |
| read_permission       | Может читать свои объекты  |
| read_all_permission   | Может читать любые объекты |
| create_permission     | Может создавать            |
| update_permission     | Может обновлять свои       |
| update_all_permission | Может обновлять любые      |
| delete_permission     | Может удалять свои         |
| delete_all_permission | Может удалять любые        |

---

# Логика авторизации

## 1. Идентификация пользователя

Производится через:

```text
JWT -> role_id
```

---

## 2. Идентификация бизнес-элемента

Производится **непосредственно в endpoint-е**, который работает с этим элементом.

### Пример:

```http
PATCH /users/1
```

Эндпоинт обновляет пользователя → значит бизнес-элемент = `users`.

---

## 3. Проверка AccessRule

По:

```text
role_id + element_id
```

---

## 4. Разрешение / Запрет

Если правило разрешает действие:

```text
-> Выполняем endpoint
```

Иначе:

```text
403 Forbidden
```

---

# Пример работы AccessRule

## Обновление пользователя

Допустим:

* Обновлять пользователя могут:

  * **role_id = 1** → Admin
  * **role_id = 3** → Сам пользователь

### Flow Endpoint

1. Из JWT получаем `role_id`
2. Проверяем AccessRule:

   * есть ли право update/update_all для `users`
3. Если есть:

   * выполняем обновление
4. Иначе:

   * 403 Forbidden

---

# Почему AccessRule не редактируется через API?

В рамках проекта CRUD для AccessRule **не реализован намеренно**.

### Причина:

Редактирование правил доступа:

* является обычным CRUD;
* требует лишь проверки:

```python
if role_id != 1:
    raise 403
```

Реализация не представляет архитектурной сложности и не влияет на основную цель задания.

---

# Концепция Системы Доступа

## Идентификация пользователя

```text
JWT (role_id)
```

## Идентификация ресурса

```text
Endpoint = Business Element
```

## Управление доступом

```text
AccessRule
```

---

# Таким образом:

```text
User Identity -> JWT(role_id)
Resource Identity -> Endpoint / Business Element
Permission Rules -> AccessRule
```

---

# Коды Ответов

## 401 Unauthorized

Возвращается если:

* JWT отсутствует;
* JWT невалиден;
* JWT в blacklist;
* пользователь не найден.

---

## 403 Forbidden

Возвращается если:

* пользователь идентифицирован;
* но не имеет прав на данный бизнес-элемент.

---

# Запуск проекта

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск

```bash
В корневой директории:
python main.py
```


# Swagger

После запуска:

```text
http://localhost:8000/docs
```
## Заполняем БД тестовыми данными

```bash
POST /fill_db
```

---

# Итог

Проект реализует полноценную кастомную backend-систему:

* JWT Authentication
* Cookie-based Session Strategy
* Refresh Tokens
* Blacklist Logout
* RBAC-like Authorization
* Fine-grained Access Rules
* Layered Architecture
* JSON Seed Data Loader

---

# Автор

Проект выполнен в рамках тестового/учебного задания на разработку backend-системы аутентификации и авторизации.
