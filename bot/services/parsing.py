import aiohttp
from bs4 import BeautifulSoup
import re

BLACKLIST_DOMAINS = ["instagram.com", "tiktok.com", "vm.tiktok.com", "instagr.am"]

async def get_page_title(url: str) -> str:
    """Переходит по ссылке и возвращает заголовок страницы."""
    # Проверка на черный список доменов
    for domain in BLACKLIST_DOMAINS:
        if domain in url.lower():
            return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    return None
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 1. Пробуем OpenGraph (обычно там самое чистое название)
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    return og_title["content"].strip()
                
                # 2. Если нет, берем обычный <title>
                if soup.title and soup.title.string:
                    return soup.title.string.strip()
                return None
    except Exception:
        return None

def normalize_title(title: str) -> str:
    """
    Нормализация названия для поиска дублей.
    Главная цель: превратить 'Ла-ла Лэнд (Ла-Ла Лэнд, 2016)' в 'ла ла лэнд'
    """
    if not title:
        return ""
    
    # 1. УБИВАЕМ ВСЁ ПОСЛЕ СКОБКИ
    # Это решает проблему дублирования названия внутри скобок
    if '(' in title:
        title = title.split('(')[0]
    
    # 2. Нижний регистр
    text = title.lower()
    
    # 3. Убираем хвосты платформ (до знаков препинания)
    text = re.sub(r'\s+[—–-]\s+на\s+(иви|ivi|kinopoisk|кинопоиск|okko|окко|premier|start).*', '', text)
    
    # 4. Отсекаем по разделителям (палка, тире окруженное пробелами, точка)
    # Пример: "Шпион | Spy" -> "Шпион"
    text = re.split(r'(\s+[|/—–-]\s+|\.\s+)', text)[0]

    # 5. Убираем "мусорные" слова
    stop_trigger_words = [
        "смотреть", "онлайн", "фильм", "трейлер", "online", "скачать", "бесплатно", 
        "в хорошем", "hd", "fhd", "4k", "720", "1080", "сезон", "серия"
    ]
    for word in stop_trigger_words:
        if word in text:
            text = text.split(word)[0]

    # 6. Заменяем ЛЮБЫЕ спецсимволы (включая дефис внутри слова) на пробел
    # Чтобы "Ла-Ла Лэнд" превратился в "ла ла лэнд"
    text = re.sub(r'[^\w\sа-яА-ЯёЁ]', ' ', text)
    
    # 7. Убираем лишние пробелы (схлопываем двойные пробелы в один)
    normalized = " ".join(text.split())

    return normalized