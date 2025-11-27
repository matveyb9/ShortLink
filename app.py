from flask import Flask, request, jsonify, render_template_string, redirect
from flask_cors import CORS
import psycopg2
import pymysql
import os
import string
import random
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Конфигурация из переменных среды
DB_TYPE = os.getenv('DB_TYPE', 'postgresql')  # postgresql или mysql
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432' if DB_TYPE == 'postgresql' else '3306')
DB_NAME = os.getenv('DB_NAME', 'urlshortener')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Подключение к базе данных
def get_db_connection():
    if DB_TYPE == 'postgresql':
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    else:  # mysql
        return pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursorclass=pymysql.cursors.DictCursor
        )

# Инициализация базы данных
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                shortcode VARCHAR(6) UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicks INTEGER DEFAULT 0
            )
        ''')
    else:  # mysql
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shortcode VARCHAR(6) UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicks INT DEFAULT 0
            )
        ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# Генерация уникального короткого кода
def generate_shortcode():
    characters = string.ascii_letters + string.digits
    while True:
        shortcode = ''.join(random.choices(characters, k=6))
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'postgresql':
            cursor.execute('SELECT shortcode FROM urls WHERE shortcode = %s', (shortcode,))
        else:
            cursor.execute('SELECT shortcode FROM urls WHERE shortcode = %s', (shortcode,))
        
        exists = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not exists:
            return shortcode

# Валидация URL
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# HTML шаблон главной страницы
HOME_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        input[type="url"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="url"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
            display: none;
        }
        
        .result.show {
            display: block;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .short-url {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 10px;
        }
        
        .short-url input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .copy-btn {
            padding: 10px 20px;
            width: auto;
            background: #667eea;
            font-size: 14px;
        }
        
        .error {
            color: #e74c3c;
            margin-top: 10px;
            font-size: 14px;
            display: none;
        }
        
        .error.show {
            display: block;
        }
        
        .success {
            color: #27ae60;
            margin-top: 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 URL Shortener</h1>
        <p class="subtitle">Сократите длинную ссылку в один клик</p>
        
        <form id="shortenForm">
            <div class="input-group">
                <input 
                    type="url" 
                    id="urlInput" 
                    placeholder="Вставьте вашу длинную ссылку здесь..." 
                    required
                >
            </div>
            <button type="submit" id="submitBtn">Сократить ссылку</button>
            <div class="error" id="error"></div>
        </form>
        
        <div class="result" id="result">
            <h3>✅ Ссылка успешно сокращена!</h3>
            <div class="short-url">
                <input type="text" id="shortUrl" readonly>
                <button class="copy-btn" onclick="copyToClipboard()">Копировать</button>
            </div>
            <p class="success" id="copySuccess" style="display:none;">Скопировано!</p>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('shortenForm');
        const urlInput = document.getElementById('urlInput');
        const submitBtn = document.getElementById('submitBtn');
        const result = document.getElementById('result');
        const shortUrlInput = document.getElementById('shortUrl');
        const error = document.getElementById('error');
        const copySuccess = document.getElementById('copySuccess');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = urlInput.value.trim();
            
            if (!url) {
                showError('Пожалуйста, введите URL');
                return;
            }
            
            error.classList.remove('show');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Сокращаем...';
            
            try {
                const response = await fetch('/api/shorten', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    shortUrlInput.value = data.short_url;
                    result.classList.add('show');
                    copySuccess.style.display = 'none';
                } else {
                    showError(data.error || 'Произошла ошибка');
                }
            } catch (err) {
                showError('Ошибка соединения с сервером');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Сократить ссылку';
            }
        });
        
        function showError(message) {
            error.textContent = message;
            error.classList.add('show');
            result.classList.remove('show');
        }
        
        function copyToClipboard() {
            shortUrlInput.select();
            document.execCommand('copy');
            copySuccess.style.display = 'block';
            setTimeout(() => {
                copySuccess.style.display = 'none';
            }, 2000);
        }
    </script>
</body>
</html>
'''

# HTML шаблон страницы редиректа
REDIRECT_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Переадресация...</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 28px;
        }
        
        .url-box {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            word-break: break-all;
        }
        
        .url {
            color: #667eea;
            font-weight: 600;
        }
        
        .redirect-info {
            color: #666;
            margin-top: 20px;
            font-size: 14px;
        }
        
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .button:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Переадресация</h1>
        <p>Эта короткая ссылка ведёт на:</p>
        <div class="url-box">
            <div class="url">{{ original_url }}</div>
        </div>
        <a href="{{ original_url }}" class="button">Перейти по ссылке</a>
        <p class="redirect-info">Вы будете перенаправлены автоматически через 3 секунды...</p>
    </div>
    
    <script>
        setTimeout(() => {
            window.location.href = '{{ original_url }}';
        }, 3000);
    </script>
</body>
</html>
'''

# HTML шаблон страницы 404
ERROR_404_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Ссылка не найдена</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        .error-code {
            font-size: 80px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 15px;
            font-size: 28px;
        }
        
        p {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        
        .button {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .button:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-code">404</div>
        <h1>Ссылка не найдена</h1>
        <p>К сожалению, такой короткой ссылки не существует.<br>Проверьте правильность адреса.</p>
        <a href="/" class="button">На главную</a>
    </div>
</body>
</html>
'''

# Маршруты
@app.route('/')
def home():
    return render_template_string(HOME_PAGE)

@app.route('/<shortcode>')
def redirect_url(shortcode):
    # Проверка формата shortcode
    if len(shortcode) != 6 or not all(c in string.ascii_letters + string.digits for c in shortcode):
        return render_template_string(ERROR_404_PAGE), 404
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        cursor.execute('SELECT original_url FROM urls WHERE shortcode = %s', (shortcode,))
        cursor.execute('UPDATE urls SET clicks = clicks + 1 WHERE shortcode = %s', (shortcode,))
    else:
        cursor.execute('SELECT original_url FROM urls WHERE shortcode = %s', (shortcode,))
        cursor.execute('UPDATE urls SET clicks = clicks + 1 WHERE shortcode = %s', (shortcode,))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    if result:
        original_url = result[0] if DB_TYPE == 'postgresql' else result['original_url']
        return render_template_string(REDIRECT_PAGE, original_url=original_url)
    else:
        return render_template_string(ERROR_404_PAGE), 404

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL не предоставлен'}), 400
    
    original_url = data['url'].strip()
    
    if not is_valid_url(original_url):
        return jsonify({'error': 'Некорректный URL'}), 400
    
    shortcode = generate_shortcode()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if DB_TYPE == 'postgresql':
            cursor.execute(
                'INSERT INTO urls (shortcode, original_url) VALUES (%s, %s)',
                (shortcode, original_url)
            )
        else:
            cursor.execute(
                'INSERT INTO urls (shortcode, original_url) VALUES (%s, %s)',
                (shortcode, original_url)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        short_url = f"{BASE_URL}/{shortcode}"
        
        return jsonify({
            'short_url': short_url,
            'shortcode': shortcode,
            'original_url': original_url
        }), 201
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'error': 'Ошибка при создании короткой ссылки'}), 500

@app.route('/api/info/<shortcode>', methods=['GET'])
def get_url_info(shortcode):
    if len(shortcode) != 6:
        return jsonify({'error': 'Некорректный shortcode'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'postgresql':
        cursor.execute(
            'SELECT original_url, created_at, clicks FROM urls WHERE shortcode = %s',
            (shortcode,)
        )
    else:
        cursor.execute(
            'SELECT original_url, created_at, clicks FROM urls WHERE shortcode = %s',
            (shortcode,)
        )
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        if DB_TYPE == 'postgresql':
            return jsonify({
                'shortcode': shortcode,
                'original_url': result[0],
                'created_at': result[1].isoformat(),
                'clicks': result[2]
            })
        else:
            return jsonify({
                'shortcode': shortcode,
                'original_url': result['original_url'],
                'created_at': result['created_at'].isoformat(),
                'clicks': result['clicks']
            })
    else:
        return jsonify({'error': 'Ссылка не найдена'}), 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
