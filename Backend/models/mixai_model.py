import torch
import torch.nn as nn
from torch.optim import Adam
import numpy as np
from transformers import AutoTokenizer, AutoModel
import pickle
import os
from datetime import datetime

class MixAIModel:
    def __init__(self, model_name='distilbert-base-uncased'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.vocab_size = self.tokenizer.vocab_size

        # Простая генеративная модель
        self.generator = nn.Linear(self.model.config.hidden_size, self.vocab_size)

        self.optimizer = Adam(self.generator.parameters(), lr=1e-4)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

        # Загрузка сохранённой модели, если есть
        self.load_model()

    def generate_response(self, input_text, history, max_length=150):
        # Объединение истории и текущего сообщения
        context = self._build_context(input_text, history)

        # Токенизация
        inputs = self.tokenizer(
            context,
            return_tensors='pt',
            truncation=True,
            max_length=4096
        ).to(self.device)

        # Генерация текста
        with torch.no_grad():
            outputs = self.model(**inputs)
            hidden_states = outputs.last_hidden_state

            # Простая генерация следующего токена
            generated_tokens = []
            for _ in range(max_length):
                logits = self.generator(hidden_states[:, -1, :])
                next_token = torch.argmax(logits, dim=-1)
                generated_tokens.append(next_token.item())

                # Обновление входных данных для следующего шага
                new_input = torch.cat([
                    inputs['input_ids'],
                    next_token.unsqueeze(0)
                ], dim=1)
                inputs['input_ids'] = new_input
                outputs = self.model(inputs['input_ids'])
                hidden_states = outputs.last_hidden_state

        # Декодирование
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return response

    def _build_context(self, current_message, history):
        context_parts = []
        for msg in history[-5:]:  # Последние 5 сообщений для контекста
            context_parts.append(f"User: {msg['user']}")
            context_parts.append(f"AI: {msg['ai']}")
        context_parts.append(f"User: {current_message}")
        context_parts.append("AI:")
        return " ".join(context_parts)

    def train_on_feedback(self, chat_id, message_id, rating, comment):
        # Обучение на основе отзывов пользователей
        if rating < 3:  # Плохие отзывы — корректировка
            self._adjust_model_based_on_feedback(comment)

    def _adjust_model_based_on_feedback(self, feedback_text):
        # Простая корректировка на основе текстового отзыва
        pass
        def manual_train(self, input_text, output_text):
            """Ручное обучение модели на паре «запрос‑ответ»"""
        # Токенизация данных
        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=512
        ).to(self.device)

        targets = self.tokenizer(
            output_text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=512
        ).input_ids.to(self.device)

        # Обучение
        self.model.train()
        self.optimizer.zero_grad()

        outputs = self.model(**inputs)
        hidden_states = outputs.last_hidden_state

        logits = self.generator(hidden_states)
        loss = nn.CrossEntropyLoss()(
            logits.view(-1, self.vocab_size),
            targets.view(-1)
        )

        loss.backward()
        self.optimizer.step()

        print(f"Manual training completed. Loss: {loss.item():.4f}")

    def learn_from_web(self, query, max_results=5):
        """Обучение на основе информации из интернета"""
        from utils.data_loader import WebScraper
        scraper = WebScraper()
        web_content = scraper.search_and_scrape(query, max_results)

        for content in web_content:
            self.manual_train(query, content)

    def save_model(self, path="models/saved_mixai"):
        """Сохранение модели и токенизатора"""
        os.makedirs(path, exist_ok=True)
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

        # Сохранение весов генератора
        torch.save(self.generator.state_dict(), f"{path}/generator.pth")
        torch.save(self.optimizer.state_dict(), f"{path}/optimizer.pth")

    def load_model(self, path="models/saved_mixai"):
        """Загрузка модели и токенизатора"""
        if os.path.exists(path):
            try:
                self.model = AutoModel.from_pretrained(path)
                self.tokenizer = AutoTokenizer.from_pretrained(path)
                self.generator.load_state_dict(
                    torch.load(f"{path}/generator.pth", map_location=self.device)
                )
                self.optimizer.load_state_dict(
                    torch.load(f"{path}/optimizer.pth", map_location=self.device)
                )
                print("Model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {e}")