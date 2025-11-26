from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
import random
import string
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import re

# Настройка логирования
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Конфигурация из переменных окружения
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'urlshortener')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DOMAIN = os.getenv('DOMAIN', 'localhost')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Connection pool
connection_pool = None

def init_connection_pool():
    """Инициализация пула соединений"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        app.logger.info("Connection pool created successfully")
    except Exception as e:
        app.logger.error(f"Error creating connection pool: {e}")
        raise

def get_db_connection():
    """Получение соединения из пула"""
    try:
        return connection_pool.getconn()
    except Exception as e:
        app.logger.error(f"Error getting connection from pool: {e}")
        raise

def return_db_connection(conn):
    """Возврат соединения в пул"""
    try:
        connection_pool.putconn(conn)
    except Exception as e:
        app.logger.error(f"Error returning connection to pool: {e}")

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                original_url TEXT NOT NULL,
                short_code VARCHAR(6) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicks INTEGER DEFAULT 0,
                last_clicked TIMESTAMP
            )
        ''')
        
        # Индексы для оптимизации
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON urls(created_at)
        ''')
        
        conn.commit()
        cur.close()
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Error initializing database: {e}")
        raise
    finally:
        return_db_connection(conn)

def is_valid_url(url):
    """Валидация URL"""
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url) is not None

def is_safe_url(url):
    """Проверка URL на безопасность (блокировка вредоносных доменов)"""
    # Здесь можно добавить проверку через API или базу данных вредоносных сайтов
    blocked_domains = ['malware.com', 'phishing.com']
    for domain in blocked_domains:
        if domain in url.lower():
            return False
    return True

def generate_short_code():
    """Генерация уникального 6-значного кода"""
    characters = string.ascii_letters + string.digits
    max_attempts = 10
    
    for _ in range(max_attempts):
        code = ''.join(random.choices(characters, k=6))
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute('SELECT short_code FROM urls WHERE short_code = %s', (code,))
            exists = cur.fetchone()
            cur.close()
            
            if not exists:
                return code
        finally:
            return_db_connection(conn)
    
    # Если не удалось сгенерировать уникальный код
    raise Exception("Unable to generate unique short code")

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', domain=DOMAIN)

@app.route('/<short_code>')
@limiter.limit("30 per minute")
def redirect_to_url(short_code):
    """Редирект по короткой ссылке"""
    # Валидация short_code
    if not re.match(r'^[a-zA-Z0-9]{6}$', short_code):
        app.logger.warning(f"Invalid short code format: {short_code}")
        return render_template('404.html'), 404
    
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('SELECT original_url FROM urls WHERE short_code = %s', (short_code,))
        result = cur.fetchone()
        
        if result:
            # Обновляем статистику
            cur.execute(
                'UPDATE urls SET clicks = clicks + 1, last_clicked = CURRENT_TIMESTAMP WHERE short_code = %s',
                (short_code,)
            )
            conn.commit()
            
            original_url = result['original_url']
            cur.close()
            
            app.logger.info(f"Redirect: {short_code} -> {original_url}")
            return render_template('redirect.html', url=original_url, domain=DOMAIN)
        else:
            app.logger.warning(f"Short code not found: {short_code}")
            cur.close()
            return render_template('404.html'), 404
    except Exception as e:
        app.logger.error(f"Error in redirect: {e}")
        return render_template('404.html'), 404
    finally:
        return_db_connection(conn)

@app.route('/api/shorten', methods=['POST'])
@limiter.limit("10 per minute")
def shorten_url():
    """API для сокращения ссылки"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        original_url = data['url'].strip()
        
        # Валидация URL
        if not is_valid_url(original_url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Проверка безопасности
        if not is_safe_url(original_url):
            app.logger.warning(f"Blocked unsafe URL: {original_url}")
            return jsonify({'error': 'URL blocked for security reasons'}), 403
        
        # Ограничение длины URL
        if len(original_url) > 2048:
            return jsonify({'error': 'URL too long'}), 400
        
        conn = get_db_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Проверяем, существует ли уже такой URL
            cur.execute('SELECT short_code FROM urls WHERE original_url = %s', (original_url,))
            existing = cur.fetchone()
            
            if existing:
                short_code = existing['short_code']
                app.logger.info(f"URL already exists: {original_url} -> {short_code}")
            else:
                # Генерируем новый код
                short_code = generate_short_code()
                
                cur.execute(
                    'INSERT INTO urls (original_url, short_code) VALUES (%s, %s)',
                    (original_url, short_code)
                )
                conn.commit()
                app.logger.info(f"Created new short URL: {original_url} -> {short_code}")
            
            cur.close()
            
            protocol = 'https' if FLASK_ENV == 'production' else 'http'
            short_url = f"{protocol}://{DOMAIN}/{short_code}"
            
            return jsonify({
                'original_url': original_url,
                'short_url': short_url,
                'short_code': short_code
            }), 201
        finally:
            return_db_connection(conn)
            
    except Exception as e:
        app.logger.error(f"Error in shorten_url: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/info/<short_code>', methods=['GET'])
@limiter.limit("30 per minute")
def get_url_info(short_code):
    """API для получения информации о ссылке"""
    if not re.match(r'^[a-zA-Z0-9]{6}$', short_code):
        return jsonify({'error': 'Invalid short code format'}), 400
    
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('SELECT * FROM urls WHERE short_code = %s', (short_code,))
        result = cur.fetchone()
        
        cur.close()
        
        if result:
            return jsonify({
                'original_url': result['original_url'],
                'short_code': result['short_code'],
                'created_at': result['created_at'].isoformat(),
                'clicks': result['clicks'],
                'last_clicked': result['last_clicked'].isoformat() if result['last_clicked'] else None
            }), 200
        else:
            return jsonify({'error': 'URL not found'}), 404
    except Exception as e:
        app.logger.error(f"Error in get_url_info: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        return_db_connection(conn)

@app.route('/health')
def health_check():
    """Health check endpoint для мониторинга"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        return_db_connection(conn)
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy'}), 503

@app.errorhandler(429)
def ratelimit_handler(e):
    """Обработчик rate limit"""
    app.logger.warning(f"Rate limit exceeded: {get_remote_address()}")
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    """Обработчик внутренних ошибок"""
    app.logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_connection_pool()
    init_db()
    
    # В production используется gunicorn, а не встроенный сервер Flask
    if FLASK_ENV == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(host='0.0.0.0', port=5000, debug=False)