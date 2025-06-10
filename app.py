# app.py - Наше новое веб-приложение
from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess # Для вызова нашего старого скрипта

# --- Конфигурация ---
app = Flask(__name__, static_folder='.', static_url_path='')
DOCS_DIR = 'docs'

# --- API эндпоинты ---

@app.route('/api/get-content')
def get_file_content():
    """Возвращает содержимое md-файла."""
    file_path_rel = request.args.get('path') # Получаем путь из запроса ?path=...
    if not file_path_rel:
        return jsonify({"error": "Путь к файлу не указан"}), 400

    # Безопасность: проверяем, что путь находится внутри папки docs
    full_path = os.path.abspath(os.path.join(DOCS_DIR, file_path_rel))
    if not full_path.startswith(os.path.abspath(DOCS_DIR)):
        return jsonify({"error": "Доступ запрещен"}), 403

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content})
    except FileNotFoundError:
        return jsonify({"error": "Файл не найден"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/save-content', methods=['POST'])
def save_file_content():
    """Сохраняет содержимое в md-файл и пересобирает сайт."""
    data = request.json
    file_path_rel = data.get('path')
    content = data.get('content')

    if not file_path_rel or content is None:
        return jsonify({"error": "Неверные данные"}), 400

    full_path = os.path.abspath(os.path.join(DOCS_DIR, file_path_rel))
    if not full_path.startswith(os.path.abspath(DOCS_DIR)):
        return jsonify({"error": "Доступ запрещен"}), 403

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Запускаем наш старый скрипт для пересборки notes.html
        print("Пересборка сайта...")
        subprocess.run(['python', 'generate_site.py'], check=True)
        print("✓ Сайт пересобран.")
        
        return jsonify({"success": True, "message": "Файл сохранен"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Роут для отдачи главной страницы ---

@app.route('/')
def index():
    # Просто отдаем уже сгенерированный файл
    return send_from_directory('.', 'notes.html')


if __name__ == '__main__':
    # Сначала один раз генерируем сайт при запуске
    print("Первичная сборка сайта при запуске...")
    subprocess.run(['python', 'generate_site.py'], check=True)
    
    # Запускаем веб-сервер
    print("\nСервер запущен. Откройте http://127.0.0.1:5000 в вашем браузере.")
    app.run(debug=True, port=5000)