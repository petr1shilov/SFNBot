from dotenv import load_dotenv
import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import  CommandStart, Command, StateFilter
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile
)
import time

from base_model import BaseModel
from rag_engine import get_bot_answer

from bot.states import UserStates
from bot.keyboards import get_keyboard
from bot.texts import *

load_dotenv() 

auth_key = os.getenv("AUTH_KEY")
TOKEN = os.getenv("TELEGRAM_KEY")


base_model = BaseModel(auth_key)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(TOKEN)

bot_logger = logging.getLogger('bot_logger')

if bot_logger.hasHandlers():
    bot_logger.handlers.clear()

handler = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s:%(name)s - %(message)s')
handler.setFormatter(formatter)
bot_logger.addHandler(handler)
bot_logger.setLevel(logging.INFO)


async def safe_delete_messages(chat_id: int, message_ids: list):
    """Функция безопасного удаления сообщений с обработкой ошибок."""
    if not message_ids:
        return

    try:
        await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
    except TelegramBadRequest:
        bot_logger.warning(f"Сообщения {message_ids} уже удалены или не существуют.")
    except TelegramForbiddenError:
        bot_logger.warning(f"Нет прав на удаление сообщений в чате {chat_id}.")
    except TelegramRetryAfter as e:
        bot_logger.warning(f"Превышен лимит запросов. Ожидание {e.retry_after} секунд...")
        await asyncio.sleep(e.retry_after)
        await safe_delete_messages(chat_id, message_ids)


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    curr_time = time.strftime("%H:%M:%S", time.localtime())
    bot_logger.info(f'Начало итерации: {curr_time}\nПользователь: {message.from_user.id}')
    await state.update_data(faq_threshold=base_model.faq_threshold, top_k=base_model.top_k)
    await message.answer(hello_message_text)


<<<<<<< HEAD
# @dp.message(Command('bot_settings'))
# async def change_settings(message: Message, state: FSMContext):
#     await message.answer('Меню настроек бота', reply_markup=get_keyboard('settings_kb'))
=======
@dp.message(Command('bot_settings'))
async def change_settings(message: Message, state: FSMContext):
    await message.answer('Меню настроек бота', reply_markup=get_keyboard('settings_kb'))
>>>>>>> 0df95b76a3a0a30f0a5f2c72e110bb6cc0e9b907


@dp.callback_query(F.data == button_faq_threshold)
async def chage_faq_threshold(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(UserStates.get_faq)
    await callback.message.answer('Введите число от 0.0 до 1.0')
    

@dp.message(StateFilter(UserStates.get_faq), F.content_type == "text")
async def get_agent_text(message: Message, state: FSMContext):
    try:
        faq_threshold = float(message.text)
        await state.update_data(faq_threshold=faq_threshold) 
        await message.answer('faq_threshold успешно обновлен', reply_markup=get_keyboard('settings_kb'))
    except:
        await message.answer('faq_threshold был введен с ошибкой', reply_markup=get_keyboard('settings_kb'))


@dp.callback_query(F.data == button_top_k)
async def chage_faq_threshold(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(UserStates.get_top_k)
    await callback.message.answer('Введите целое число, например 1')
    

@dp.message(StateFilter(UserStates.get_top_k), F.content_type == "text")
async def get_agent_text(message: Message, state: FSMContext):
    try:
        top_k = int(message.text)
        await state.update_data(top_k=top_k) 
        await message.answer('top_k успешно обновлен', reply_markup=get_keyboard('settings_kb'))
    except:
        await message.answer('top_k был введен с ошибкой', reply_markup=get_keyboard('settings_kb'))


@dp.callback_query(F.data == button_info)
async def get_update(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(base_model.show_params())
    await state.set_state(UserStates.get_all)


@dp.callback_query(F.data == button_update)
async def get_update(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    user_data = await state.get_data() 
    faq_threshold = user_data.get('faq_threshold', base_model.faq_threshold)
    top_k = user_data.get('top_k', base_model.top_k)
    base_model.update(faq_threshold=faq_threshold, top_k=top_k)
    await callback.message.answer(base_model.show_params())
    await state.set_state(UserStates.get_all)


@dp.message(F.content_type == "text")
async def conversation(message: Message):
    print(message.text)
    answer = get_bot_answer(base_model, message.text)
    await message.answer(answer)


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))