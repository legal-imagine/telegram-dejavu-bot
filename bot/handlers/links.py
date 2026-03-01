import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.chat_action import ChatActionSender  # <--- 1. НОВЫЙ ИМПОРТ

# Импорты
from bot.db import database
from bot.services import parsing

router = Router()

class LinkState(StatesGroup):
    waiting_for_title = State()

@router.message(F.text.regexp(r'(?i)смотрим\s+https?://\S+'))
async def process_link(message: Message, state: FSMContext, bot: Bot):
    """
    Ловит сообщения с ссылками.
    """
    # <--- 2. ОБЕРТКА ДЛЯ СТАТУСА "ПЕЧАТАЕТ"
    async with ChatActionSender(bot=bot, chat_id=message.chat.id, action="typing"):
        
        # --- ДАЛЬШЕ ВАШ СТАРЫЙ КОД (просто с отступом) ---
        import re
        match = re.search(r'https?://\S+', message.text)
        if not match:
            return

        link = match.group(0)
        user_id = message.from_user.id
        
        # 1. Сначала проверяем точное совпадение ссылки
        existing_film = await database.get_film_by_link(link)
        
        if existing_film:
            try:
                film_title = existing_film[1] 
                await message.delete()
                await message.answer(f"✋ Уже смотрели {film_title}")
            except Exception as e:
                logging.error(f"Не удалось удалить сообщение: {e}")
            return

        # 2. Пробуем найти название фильма по ссылке
        page_title = await parsing.get_page_title(link)
        
        if page_title:
            # Автоматический режим
            normalized_title = parsing.normalize_title(page_title)
            
            # Проверяем дубликат по названию
            existing_by_title = await database.get_film_by_title(normalized_title)
            
            if existing_by_title:
                try:
                    await message.delete()
                    await message.answer(f"✋ Уже смотрели {normalized_title}!")
                except:
                    pass
                return

            await database.add_film(normalized_title, page_title, link, user_id)
            await message.answer(f"✅ Еще не смотрели. Сохранил в базу: {normalized_title}")
            
        else:
            # 3. Ручной режим
            bot_msg = await message.answer(
                "🤔 Не смог узнать название фильма по ссылке.\n"
                "Пожалуйста, напишите название в следующем сообщении:"
            )
            
            await state.set_state(LinkState.waiting_for_title)
            
            await state.update_data(
                link=link,
                original_msg_id=message.message_id,
                bot_msg_id=bot_msg.message_id
            )

@router.message(LinkState.waiting_for_title)
async def process_manual_title(message: Message, state: FSMContext, bot: Bot):
    """
    Обработка введенного вручную названия
    """
    # <--- 2. ОБЕРТКА ДЛЯ СТАТУСА "ПЕЧАТАЕТ"
    async with ChatActionSender(bot=bot, chat_id=message.chat.id, action="typing"):
        
        # --- ДАЛЬШЕ ВАШ СТАРЫЙ КОД (просто с отступом) ---
        data = await state.get_data()
        link = data.get("link")
        original_msg_id = data.get("original_msg_id")
        bot_msg_id = data.get("bot_msg_id")
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Нормализуем то, что ввел пользователь
        manual_title_original = message.text
        manual_title_normalized = parsing.normalize_title(manual_title_original)
        
        # Проверка на дубликат
        existing_film = await database.get_film_by_title(manual_title_normalized)
        
        if existing_film:
            # --- ВАРИАНТ 1: ДУБЛИКАТ ---
            await message.answer(f"✋ Уже смотрели {manual_title_normalized}!")
            
            try:
                await message.delete()
                if bot_msg_id: await bot.delete_message(chat_id, bot_msg_id)
                if original_msg_id: await bot.delete_message(chat_id, original_msg_id)
            except Exception as e:
                logging.error(f"Ошибка при очистке дубликата: {e}")

        else:
            # --- ВАРИАНТ 2: УСПЕХ ---
            await database.add_film(manual_title_normalized, manual_title_original, link, user_id)
            
            await message.answer(f"✅ Еще не смотрели. Сохранил в базу: {manual_title_normalized}")
            
            try:
                await message.delete()
                if bot_msg_id: await bot.delete_message(chat_id, bot_msg_id)
            except Exception as e:
                logging.error(f"Ошибка при очистке диалога: {e}")

        # Сбрасываем состояние
        await state.clear()