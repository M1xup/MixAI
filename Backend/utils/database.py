import mysql.connector
import gzip
import base64
from cryptography.fernet import Fernet
import hashlib
import os
from datetime import datetime
from mysql.connector import Error

class SecureMySQLDatabase:
    def __init__(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                # Зелёный цвет для успеха
                print("\033[92m✓ Успешное подключение к MySQL\033[0m")
        except Error as e:
            # Красный цвет для ошибки
            print(f"\033[91m✗ Ошибка подключения к MySQL: {e}\033[0m")
            raise
        
        self.cursor = self.connection.cursor()
        # Генерация мастер‑ключа (в продакшене храните его в безопасном месте)
        self.master_key = os.environ.get('DB_ENCRYPTION_KEY')
        if not self.master_key:
            self.master_key = Fernet.generate_key()
            os.environ['DB_ENCRYPTION_KEY'] = self.master_key.decode()
        self.fernet = Fernet(self.master_key)

    def _encrypt_and_compress(self, data):
        """Шифрование и сжатие данных"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        # Сжатие
        compressed_data = gzip.compress(data)
        # Шифрование
        encrypted_data = self.fernet.encrypt(compressed_data)
        return encrypted_data

    def _decrypt_and_decompress(self, encrypted_data):
        """Расшифровка и распаковка данных"""
        # Расшифровка
        decrypted_data = self.fernet.decrypt(encrypted_data)
        # Распаковка
        decompressed_data = gzip.decompress(decrypted_data)
        return decompressed_data.decode('utf-8')

    def _get_key_hash(self):
        """Получить хеш текущего ключа шифрования"""
        # Кодируем строку в байты с использованием UTF-8
        key_bytes = self.master_key.encode('utf-8')
        return hashlib.sha256(key_bytes).hexdigest()

    def save_chat_message(self, chat_id, user_msg, ai_response):
        """Сохранить сообщение чата в базу данных"""
        user_msg_encrypted = self._encrypt_and_compress(user_msg)
        ai_response_encrypted = self._encrypt_and_compress(ai_response)
        key_hash = self._get_key_hash()

        query = """
                INSERT INTO chat_history
                (chat_id, user_message_encrypted, ai_response_encrypted, encryption_key_hash)
                VALUES (%s, %s, %s, %s) \
                """
        self.cursor.execute(query, (chat_id, user_msg_encrypted,
                                    ai_response_encrypted, key_hash))
        self.connection.commit()

    def load_chat_history(self, chat_id):
        """Загрузить историю чата из базы данных"""
        query = """
                SELECT user_message_encrypted, ai_response_encrypted, timestamp
                FROM chat_history
                WHERE chat_id = %s
                ORDER BY timestamp \
                """
        self.cursor.execute(query, (chat_id,))
        results = self.cursor.fetchall()
        history = []
        for user_enc, ai_enc, timestamp in results:
            try:
                user_msg = self._decrypt_and_decompress(user_enc)
                ai_response = self._decrypt_and_decompress(ai_enc)
                history.append({
                    'user': user_msg,
                    'ai': ai_response,
                    'timestamp': timestamp
                })
            except Exception as e:
                print(f"Ошибка расшифровки: {e}")
        return history

    def save_feedback(self, chat_id, message_id, rating, comment):
        """Сохранить отзыв пользователя"""
        comment_encrypted = None
        if comment:
            comment_encrypted = self._encrypt_and_compress(comment)
        key_hash = self._get_key_hash()

        query = """
                INSERT INTO user_feedback
                    (chat_id, message_id, rating, comment_encrypted, encryption_key_hash)
                VALUES (%s, %s, %s, %s, %s) \
                """
        self.cursor.execute(query, (chat_id, message_id, rating,
                                    comment_encrypted, key_hash))
        self.connection.commit()

    def close(self):
        """Закрыть соединение с базой данных"""
        self.cursor.close()
        self.connection.close()