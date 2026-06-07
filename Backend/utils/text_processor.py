import spacy
import nltk
from nltk.corpus import stopwords
from spellchecker import SpellChecker

class TextProcessor:
    def __init__(self):
        # Загрузка моделей для обработки текста
        self.nlp = spacy.load("en_core_web_sm")
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')

        self.spell = SpellChecker()
        self.stop_words = set(stopwords.words('english'))

    def process_text(self, text):
        """Обработка текста: исправление ошибок, нормализация, определение языка"""
        # Исправление орфографии
        words = text.split()
        corrected_words = []
        for word in words:
            corrected = self.spell.correction(word.lower())
            corrected_words.append(corrected if corrected else word)

        corrected_text = ' '.join(corrected_words)

        # Нормализация регистра и пунктуации
        doc = self.nlp(corrected_text)
        normalized_tokens = [token.text for token in doc if not token.is_punct]

        return ' '.join(normalized_tokens)

    def detect_language(self, text):
        """Определение языка текста"""
        # Простая эвристика: проверка распространённых слов
        words = text.lower().split()[:10]  # Первые 10 слов
        english_words = sum(1 for w in words if w in self.stop_words)
        if english_words > 5:
            return 'en'
        return 'unknown'