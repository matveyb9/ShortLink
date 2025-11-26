# URL Shortener

Сервис для сокращения ссылок с минималистичным интерфейсом.

## 🚀 Быстрый старт (Cloud Apps)

### Шаг 1: Настройка переменных окружения

В панели Cloud Apps настройте следующие переменные:
```
DB_NAME=urlshortener
DB_USER=postgres
DB_PASSWORD=your_secure_password
DOMAIN=your-app.cloud-provider.com
```

### Шаг 2: Подключение базы данных

**Вариант A: Встроенная база данных Cloud Apps**
- Создайте PostgreSQL базу в панели управления
- Сервис автоматически создаст переменную DATABASE_URL
- Дополнительные переменные не нужны

**Вариант B: Внешняя база данных**
- Используйте переменные DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

### Шаг 3: Деплой

1. Подключите GitHub репозиторий
2. Выберите ветку (main/master)
3. Укажите Dockerfile
4. Нажмите "Deploy"

Cloud Apps автоматически:
- Соберет Docker образ
- Настроит CI/CD
- Выделит домен
- Настроит SSL

## 📡 API Endpoints

### Сократить ссылку
```bash
POST /api/shorten
Content-Type: application/json

{
  "url": "https://example.com/very/long/url"
}
```

### Получить информацию
```bash
GET /api/info/{short_code}
```

### Health Check
```bash
GET /health
```

## 🔧 Локальная разработка
```bash
# Клонирование
git clone <repo>
cd url-shortener

# Настройка окружения
cp .env.example .env
nano .env

# Запуск
docker-compose up -d

# Проверка
curl http://localhost:5000/health
```

## 🛠 Технологии

- Python 3.11
- Flask
- PostgreSQL 15
- Docker
- Gunicorn

## 📝 Лицензия

MIT
```

**6. .dockerignore**
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.git
.gitignore
*.md
*.log
.vscode
.idea
*.swp
docker-compose.yml
Dockerfile
.dockerignore
```

**7. .gitignore**
```
# Environment
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Logs
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## 🎯 ИНСТРУКЦИЯ ПО ДЕПЛОЮ НА CLOUD APPS

### Вариант 1: Timeweb Cloud Apps

1. **Создайте приложение:**
   - Перейдите в раздел "Cloud Apps"
   - Нажмите "Создать приложение"
   - Выберите "Docker"

2. **Настройте репозиторий:**
   - Подключите GitHub/GitLab
   - Выберите репозиторий и ветку
   - Путь к Dockerfile: `./Dockerfile`

3. **Настройте переменные окружения:**
```
   DB_NAME=urlshortener
   DB_USER=postgres
   DB_PASSWORD=your_password
   DOMAIN=your-app.timeweb.cloud
```

4. **Подключите базу данных:**
   - Создайте PostgreSQL в разделе "Базы данных"
   - Скопируйте данные подключения
   - Или используйте автоматическую переменную DATABASE_URL

5. **Деплой:**
   - Нажмите "Создать"
   - Дождитесь сборки (3-5 минут)
   - Приложение будет доступно по выданному домену

### Вариант 2: VK Cloud (ML Platform)

1. **Создайте проект:**
   - Зайдите в ML Platform
   - Создайте новый проект
   - Выберите "Docker контейнер"

2. **Настройте образ:**
   - Укажите Dockerfile
   - Или используйте готовый образ из registry

3. **База данных:**
   - Создайте Cloud Databases PostgreSQL
   - Получите строку подключения
   - Добавьте как DATABASE_URL

4. **Переменные окружения:**
```
   DATABASE_URL=postgresql://user:pass@host:5432/db
   DOMAIN=your-app.mcs.mail.ru
   PORT=8080
```

### Вариант 3: DigitalOcean App Platform

1. **Создайте App:**
   - Apps → Create App
   - Выберите GitHub repository
   - Detect Dockerfile автоматически

2. **Настройте компоненты:**
   - Web Service (из Dockerfile)
   - PostgreSQL Database (managed)

3. **Environment Variables:**
```
   DATABASE_URL=${db.DATABASE_URL}
   DOMAIN=${APP_DOMAIN}
```

4. **Deploy:**
   - Настройки применяются автоматически
   - SSL настраивается автоматически

### Вариант 4: Render

1. **New Web Service:**
   - Подключите GitHub
   - Docker выбирается автоматически

2. **Environment:**
```
   DOMAIN=${RENDER_EXTERNAL_HOSTNAME}
   DB_HOST=<postgres-hostname>
   DB_NAME=urlshortener
   DB_USER=<user>
   DB_PASSWORD=<password>
```

3. **Database:**
   - Создайте PostgreSQL в Render
   - Или используйте внешнюю БД

### Вариант 5: Railway

1. **New Project:**
   - Deploy from GitHub
   - Railway автоматически определит Dockerfile

2. **PostgreSQL:**
   - Add Plugin → PostgreSQL
   - DATABASE_URL создается автоматически

3. **Variables:**
```
   DOMAIN=${RAILWAY_PUBLIC_DOMAIN}