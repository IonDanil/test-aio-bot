from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

# создаем класс-шаблон с данными, отправляемыми в запросе обратного вызова.
category_cb = CallbackData('category', 'id', 'action')


# Функция формирования разметки
def categories_markup():
    global category_cb

    # Создаем разметку клавиатуры.
    markup = InlineKeyboardMarkup()

    # Получаем список категорий из базы данных и для каждой создаем кнопку.
    # При нажатии на кнопку будет создаваться новый объект класса с отправляемыми в запросе обратного вызова.
    # В эти данные будет попадать идентификатор категории.
    for idx, title in db.fetchall('SELECT * FROM categories'):
        markup.add(InlineKeyboardButton(title,
                                        callback_data=category_cb.new(id=idx,
                                                                      action='view'))) # Привяжем к каждой кнопке обработчик вывода списка товаров категории.

    return markup
