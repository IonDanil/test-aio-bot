from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove,KeyboardButton
from aiogram import executor
from logging import basicConfig, INFO

from handlers import admin_menu, user_menu
from loader import dp, bot, db
from data.config import ADMINS
import handlers

user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(user_message, admin_message)

    await message.answer('''Привет! 👋 

🤖 Я бот-магазин по продаже товаров любой категории. 

🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся  
товары воспользуйтесь командой /menu. 

❓ Возникли вопросы? Не проблема! Команда /sos поможет  
связаться с админами, которые постараются как можно быстрее откликнуться. 
    ''', reply_markup=markup)


@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):
    cid = message.chat.id
    if cid not in ADMINS:
        ADMINS.append(cid)

    await message.answer('Включен админский режим.', reply_markup=ReplyKeyboardRemove())

    await admin_menu(message)


@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):
    cid = message.chat.id
    if cid in ADMINS:
        ADMINS.remove(cid)

    await message.answer('Включен пользовательский режим.', reply_markup=ReplyKeyboardRemove())

    await user_menu(message)


async def on_startup(dp):
    basicConfig(level=INFO)
    db.create_tables()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
