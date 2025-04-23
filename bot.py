# -*- coding: utf-8 -*-
# Импорты стандартных библиотек
import logging
import os
import psutil
import asyncio

# Импорт aiohttp для асинхронных запросов
import aiohttp

# Импорты Aiogram 3.x
from aiogram import Bot, Dispatcher, types, F # F - Magic Filter для удобной фильтрации
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart # Специальный фильтр для команды /start
from aiogram.enums import ParseMode # Enum для режимов парсинга
from aiogram.client.default import DefaultBotProperties


# --- Конфигурация ---
API_TOKEN = '7567198692:AAGOKQK7n-2fagZeSk1eXM2aBQTKtkAA_h0'  # <-- ВАШ ТОКЕН СЮДА!
DATA_STATUS_URL = 'http://10.1.10.144:5000/data-status' # URL для проверки данных

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация Dispatcher (Aiogram 3.x)
dp = Dispatcher()
# Инициализация Bot с токеном и режимом парсинга по умолчанию (Aiogram 3.x)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

# --- Вспомогательная функция ---
def bytes_to_gb(bytes_val):
    """Конвертирует байты в гигабайты."""
    gb = bytes_val / (1024**3)
    return round(gb, 2)

# --- Функции для получения статистики ---
# Эти функции не зависят от версии Aiogram
def get_cpu_stats():
    """Gets CPU usage percentage."""
    return psutil.cpu_percent(interval=1)

def get_ram_stats():
    """Gets RAM statistics."""
    memory = psutil.virtual_memory()
    return {
        'total': bytes_to_gb(memory.total),
        'available': bytes_to_gb(memory.available),
        'used': bytes_to_gb(memory.used),
        'percent': memory.percent
    }

def get_disk_stats(path='/'):
    """Gets disk statistics (defaults to root partition)."""
    disk = psutil.disk_usage(path)
    return {
        'total': bytes_to_gb(disk.total),
        'used': bytes_to_gb(disk.used),
        'free': bytes_to_gb(disk.free),
        'percent': disk.percent
    }

# --- Обработчики сообщений и колбэков (Aiogram 3.x style) ---

# Используем фильтр CommandStart для команды /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    """
    Handler for the /start command. Uses Aiogram 3.x filters.
    """
    # Синтаксис создания клавиатуры в Aiogram 3.x
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Get System Stats", callback_data='get_system_stats')],
        [InlineKeyboardButton(text="Check Data Status", callback_data='check_data_status')]
    ])

    # Используем message.reply или message.answer
    await message.reply(
        "Hello!\n"
        "I am a bot that can show system statistics or check external data status.\n"
        "Choose an option below:",
        reply_markup=keyboard
    )

# Используем Magic Filter F.data для обработки callback_query
@dp.callback_query(F.data == 'get_system_stats')
async def process_callback_stats(callback_query: types.CallbackQuery):
    """
    Handler for the 'Get System Stats' button. Uses Aiogram 3.x filters.
    """
    # Ответ на колбэк (убирает часики на кнопке)
    await callback_query.answer(text="Collecting system statistics...", show_alert=False)

    loop = asyncio.get_event_loop()
    try:
        # Запуск синхронных функций в executor'е - хороший тон в async коде
        cpu_load = await loop.run_in_executor(None, get_cpu_stats)
        ram_stats = await loop.run_in_executor(None, get_ram_stats)
        disk_stats = await loop.run_in_executor(None, get_disk_stats, '/')

        stats_message = (
            f"*System Statistics:*\n\n"
            f"*CPU:*\n"
            f"   - Load: {cpu_load}%\n\n"
            f"*RAM (Memory):*\n"
            f"   - Total: {ram_stats['total']} GB\n"
            f"   - Used: {ram_stats['used']} GB ({ram_stats['percent']}%)\n"
            f"   - Available: {ram_stats['available']} GB\n\n"
            f"*Disk (/):*\n"
            f"   - Total: {disk_stats['total']} GB\n"
            f"   - Used: {disk_stats['used']} GB ({disk_stats['percent']}%)\n"
            f"   - Free: {disk_stats['free']} GB\n"
        )
        # Отправка сообщения через объект CallbackQuery (Aiogram 3.x)
        await callback_query.message.answer(stats_message)
    except Exception as e:
        logging.error(f"Error getting system stats: {e}")
        await callback_query.message.answer("Sorry, failed to retrieve system statistics.")


# Используем Magic Filter F.data для обработки callback_query
@dp.callback_query(F.data == 'check_data_status')
async def process_callback_check_data(callback_query: types.CallbackQuery):
    """
    Handler for the 'Check Data Status' button. Uses Aiogram 3.x filters
    and makes an async HTTP request with aiohttp.
    """
    await callback_query.answer(text="Checking data status...", show_alert=False)

    # Используем aiohttp для асинхронных запросов
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(DATA_STATUS_URL, timeout=10) as response:
                response_text = await response.text()
                status_code = response.status

                logging.info(f"Data status check: URL={DATA_STATUS_URL}, Status={status_code}")

                if response.status == 200:
                    # Отправляем ответ как блок кода Markdown
                    await callback_query.message.answer(
                        f"*Data Status Response (from {DATA_STATUS_URL}):*\n\n"
                        f"```\n{response_text[:4000]}\n```" # Обрезка на всякий случай
                    )
                else:
                    await callback_query.message.answer(
                        f"Failed to check data status.\n"
                        f"URL: {DATA_STATUS_URL}\n"
                        f"Status Code: {status_code}\n"
                        f"Response: ```\n{response_text[:500]}\n```"
                    )

        except asyncio.TimeoutError:
            logging.warning(f"Data status check timeout: URL={DATA_STATUS_URL}")
            await callback_query.message.answer(
                f"Failed to check data status: Request timed out (10 seconds).\n"
                f"URL: {DATA_STATUS_URL}"
            )
        except aiohttp.ClientError as e:
            logging.error(f"Data status check error: URL={DATA_STATUS_URL}, Error: {e}")
            await callback_query.message.answer(
                f"Failed to check data status: Could not connect or other client error.\n"
                f"URL: {DATA_STATUS_URL}\n"
                f"Error: `{e}`" # Экранируем ошибку в Markdown
            )
        except Exception as e:
            logging.exception(f"Unexpected error during data status check: URL={DATA_STATUS_URL}")
            await callback_query.message.answer(
                f"An unexpected error occurred while checking data status.\n"
                f"URL: {DATA_STATUS_URL}"
            )

# --- Запуск бота (Aiogram 3.x style) ---
async def main():
    """Основная асинхронная функция для запуска бота."""
    # Можно добавить удаление вебхука и пропуск старых апдейтов перед запуском
    # await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting bot polling...")
    # Запуск polling в Aiogram 3.x
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Запуск асинхронной функции main
    asyncio.run(main())