import requests
from bs4 import BeautifulSoup
import time

class WebScraper:
    def search_and_scrape(self, query, max_results=5):
        """Поиск в интернете и скрапинг результатов"""
        results = []

        # Имитация поиска через Google (в реальности нужно использовать API)
        search_url = f"https://www.google.com/search?q={query}&num={max_results}"

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлечение ссылок из результатов поиска
            links = soup.find_all('a', href=True)
            for link in links[:max_results]:
                url = link['href']
                if url.startswith('/url?q='):
                    actual_url = url.split('/url?q=')[1].split('&')[0]
                    content = self._scrape_page(actual_url)
                    if content:
                        results.append(content)
                    time.sleep(1)  # Задержка между запросами
        except Exception as e:
            print(f"Web scraping error: {e}")

        return results

    def _scrape_page(self, url):
        """Скрапинг содержимого страницы"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Удаление скриптов и стилей
            for script in soup(["script", "style"]):
                script.decompose()

            # Извлечение текста
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:2000]  # Ограничение длины
        except:
            return None