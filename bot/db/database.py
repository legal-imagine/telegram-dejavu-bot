import sqlite3
import os
import shutil

# Имя файла базы данных
LOCAL_DB_NAME = 'films.db'

# Настройки для Amvera
PERSISTENT_DIR = '/data'
PERSISTENT_DB_PATH = os.path.join(PERSISTENT_DIR, LOCAL_DB_NAME)

def get_db_path():
    """Возвращает путь к БД. Если мы на сервере — берет из /data"""
    if os.path.exists(PERSISTENT_DIR):
        if not os.path.exists(PERSISTENT_DB_PATH):
            if os.path.exists(LOCAL_DB_NAME):
                print(f"--- [MIGRATION] Копирую локальную базу в {PERSISTENT_DB_PATH} ---")
                shutil.copy2(LOCAL_DB_NAME, PERSISTENT_DB_PATH)
        return PERSISTENT_DB_PATH
    else:
        return LOCAL_DB_NAME

DB_NAME = get_db_path()

async def init_db():
    """
    Создает таблицу, если её нет.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS films (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        ''')
        
        cursor.execute("PRAGMA table_info(films)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Проверяем наличие обязательных колонок и создаем, если их нет
        if 'link' not in existing_columns:
            cursor.execute("ALTER TABLE films ADD COLUMN link TEXT")

        if 'title_normalized' not in existing_columns:
            cursor.execute("ALTER TABLE films ADD COLUMN title_normalized TEXT")

        if 'title_original' not in existing_columns:
            cursor.execute("ALTER TABLE films ADD COLUMN title_original TEXT")

        if 'user_id' not in existing_columns:
            cursor.execute("ALTER TABLE films ADD COLUMN user_id INTEGER")
            
        if 'timestamp' not in existing_columns:
             cursor.execute("ALTER TABLE films ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
            
        conn.commit()

async def add_film(title_normalized, title_original, link, user_id):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO films (title_normalized, title_original, link, user_id) VALUES (?, ?, ?, ?)", 
                (title_normalized, title_original, link, user_id)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

async def get_film_by_title(title_normalized):
    """
    Ищет фильм по названию. Использует LIKE для поиска частичных совпадений.
    """
    if not title_normalized or len(title_normalized) < 2:
        return None

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Ищем совпадение по началу строки
        search_pattern = f"{title_normalized}%"
        
        cursor.execute("SELECT * FROM films WHERE title_normalized = ? OR title_normalized LIKE ?", 
                      (title_normalized, search_pattern))
        result = cursor.fetchone()
        
        if result:
            col_names = [description[0] for description in cursor.description]
            row_dict = dict(zip(col_names, result))
            
            # Собираем красивый ответ. Приоритет - title_original
            display_title = (
                row_dict.get('title_original') or 
                row_dict.get('title_normalized') or 
                "Без названия"
            )
            
            return (
                row_dict.get('id'), 
                row_dict.get('link'), 
                display_title, 
                row_dict.get('timestamp'), 
                row_dict.get('user_id')
            )
        return None

async def get_film_by_link(link):
    """Ищет точное совпадение ссылки в базе."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # --- ИСПРАВЛЕНИЕ: Убрали OR source_url = ?, так как колонка удалена ---
        cursor.execute("SELECT * FROM films WHERE link = ?", (link,))
        result = cursor.fetchone()
        
        if result:
            col_names = [d[0] for d in cursor.description]
            row = dict(zip(col_names, result))
            
            title = row.get('title_original') or row.get('title_normalized') or "Без названия"
            user_id = row.get('user_id')
            
            return (row.get('id'), title, user_id)
        return None