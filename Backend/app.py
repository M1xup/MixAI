from flask import Flask, request, jsonify
from models.mixai_model import MixAIModel
from utils.text_processor import TextProcessor
from utils.database import SecureMySQLDatabase
import os
import json

app = Flask(__name__)

# Инициализация модели и процессора текста
mixai_model = MixAIModel()
text_processor = TextProcessor()

# Папки для хранения данных
CHAT_HISTORY_DIR = "data/chat_history"
FEEDBACK_DIR = "data/user_feedback"

os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    chat_id = data.get('chat_id', 'default')

    # Обработка текста (исправление ошибок, нормализация)
    processed_message = text_processor.process_text(user_message)

    # Загрузка истории чата
    history = load_chat_history(chat_id)

    # Генерация ответа
    response = mixai_model.generate_response(
        processed_message,
        history
    )

    # Сохранение в историю
    save_chat_message(chat_id, user_message, response)

    return jsonify({
        'response': response,
        'chat_id': chat_id
    })

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    chat_id = data.get('chat_id')
    message_id = data.get('message_id')
    rating = data.get('rating')  # 1-5
    comment = data.get('comment', '')

    # Сохранение отзыва
    save_feedback(chat_id, message_id, rating, comment)

    # Обучение на основе отзыва
    mixai_model.train_on_feedback(chat_id, message_id, rating, comment)

    return jsonify({'status': 'success'})

@app.route('/manual_train', methods=['POST'])
def manual_train():
    data = request.json
    text_input = data.get('input')
    text_output = data.get('output')

    # Ручное обучение
    mixai_model.manual_train(text_input, text_output)

    return jsonify({'status': 'trained'})

@app.route('/')
def home():
    return jsonify({'status': 'MixAI Backend is running!', 'endpoints': ['/chat', '/feedback', '/manual_train']})

# Инициализация базы данных
db = SecureMySQLDatabase(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', 'root'),
    database=os.environ.get('DB_NAME', 'mixai')
)

def load_chat_history(chat_id):
    return db.load_chat_history(chat_id)

def save_chat_message(chat_id, user_msg, ai_response):
    db.save_chat_message(chat_id, user_msg, ai_response)

def save_feedback(chat_id, message_id, rating, comment):
    db.save_feedback(chat_id, message_id, rating, comment)

if __name__ == '__main__':
    app.run(debug=True, port=5000)