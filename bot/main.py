import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, F
from bot import config 
from bot.handlers import links

async def on_startup(bot: Bot):
    """Срабатывает при успешном запуске бота"""
    print("-----------------------------------------")
    print(f"🚀 Бот @{(await bot.get_me()).username} успешно запущен!")
    print("   Режим: Polling")
    print("   База данных: Подключена")
    print("-----------------------------------------")

async def on_shutdown(bot: Bot):
    """Срабатывает при остановке бота (Ctrl+C)"""
    print("-----------------------------------------")
    print("🛑 Бот остановлен. До встречи!")
    print("-----------------------------------------")

async def main():
    # Настройка логирования (чтобы видеть ошибки в консоли)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # --- ЗАЩИТА (WHITELIST) ---
    # Если в конфиге есть список разрешенных чатов, включаем фильтр
    if hasattr(config, "ALLOWED_CHATS") and config.ALLOWED_CHATS:
        dp.message.filter(F.chat.id.in_(config.ALLOWED_CHATS))
        logging.info(f"🔒 Включен фильтр чатов: {config.ALLOWED_CHATS}")

    # Регистрируем роутеры (логику)
    dp.include_router(links.router)

    # Регистрируем функции старта и стопа
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Удаляем вебхуки и старые апдейты перед запуском
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск поллинга
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Критическая ошибка при запуске: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nЗавершение работы (KeyboardInterrupt).")