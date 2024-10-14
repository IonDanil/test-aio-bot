from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, ContentType
from aiogram.types.chat import ChatActions
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from hashlib import md5

from loader import dp, db, bot
from filters import IsAdmin
from handlers.user.menu import settings
from states import CategoryState, ProductState
from keyboards.default.markups import *


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Добавить товар'
delete_category = '🗑️ Удалить категорию'


@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):

        markup.add(
            InlineKeyboardButton(title, callback_data=category_cb.new(id=idx, action='view'))
        )

    markup.add(
        InlineKeyboardButton('+ Добавить категорию', callback_data='add_category')
    )

    await message.answer('Настройка категорий:', reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Название категории?')
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))

    await state.finish()
    await process_settings(message)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict,
                                    state: FSMContext):
    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Все добавленные товары в эту категорию.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products, category_idx)


async def show_products(m, products, category_idx):
    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, tag in products:
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Удалить',
            callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)

    await m.answer('Хотите что-нибудь добавить или удалить?',
                   reply_markup=markup)


@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if 'category_index' in data.keys():
            idx = data['category_index']

            db.query(
                'DELETE FROM products WHERE tag IN (SELECT '
                'title FROM categories WHERE idx=?)',
                (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
            await process_settings(message)


# Обработчик нажатия кнопки добавления товара
@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):
    # Устанавливаем объект состояния для названия товара. Теперь админ сможет ввести название товара
    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)  # Запускает обработчик process_cancel

    await message.answer('Название?', reply_markup=markup)


# Обработчик отмены добавления.
@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
# Благодаря state=ProductState.title Обработчик срабатывает при включении состояния для параметра Название категории
async def process_cancel(message: Message, state: FSMContext):
    # При отмене выводим соответствующее сообщение и выключаем состояние.
    await message.answer('Ок, отменено!', reply_markup=ReplyKeyboardRemove())   # reply_markup=ReplyKeyboardRemove() - удаляет всю разметку
    await state.finish()    # завершает наше состояние

    await process_settings(message)     # Переходим обратно к списку категорий


# Обработчик добавления описания товара после ввода названия
@dp.message_handler(IsAdmin(), state=ProductState.title)
# Сам обработчик будет запускаться после изменения состояния title, т.е. когда мы введем название товара
async def process_title(message: Message, state: FSMContext):
    # Передаем в словарь контекста название товара
    async with state.proxy() as data:
        data['title'] = message.text

    await ProductState.next()   # Переходим к следующему состоянию, где нам будет предложено ввести описание товара
    await message.answer('Описание?', reply_markup=back_markup())
    # Если нам необходимо вернуться на предыдущий шаг, то мы прописываем reply_markup=back_markup()


# Обработчик возврата к добавлению товара, который будет отрабатывать только после указания названия товара.
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)  # По сути происходит повторное создание товара при нажатии кнопки возврата.


# Обработчик, который возвращает нас на этап ввода описания.
@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):
    # Устанавливаем объект состояния для названия товара. Теперь админ сможет ввести название товара.
    await ProductState.title.set()

    async with state.proxy() as data:
        await message.answer(f"Изменить название с <b>{data['title']}</b>?",
                             reply_markup=back_markup())


# Обработчик добавления фото товара после описания
@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['body'] = message.text     # Дополняем словарь контекста описанием товара

    await ProductState.next()   # Переходим к следующему атрибуту-состоянию класса ProductState. Это атрибут image.
    await message.answer('Фото?', reply_markup=back_markup())   # Запрашиваем фото.


# Обработчик непосредственно добавления фото и перехода к указанию цены после добавления фото.
@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):
    fileID = message.photo[-1].file_id  # В Telegram есть стандартная опция прикрепления сообщению фото.
    file_info = await bot.get_file(fileID)  # Получаем идентификатор этого фото.
    downloaded_file = (await bot.download_file(file_info.file_path)).read()  # Получаем объект фото по идентификатору.

    # Выполняем загрузку фото в атрибут-состояние класса ProductState.
    async with state.proxy() as data:
        data['image'] = downloaded_file

    # Переходим к следующему состоянию и выводим соответствующее сообщение.
    await ProductState.next()
    await message.answer('Цена?', reply_markup=back_markup())


# Обработчик формирования карточки товара после ввода цены.
@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

        title = data['title']
        body = data['body']
        price = data['price']

        await ProductState.next()
        text = f'<b>{title}</b>\n\n{body}\n\nЦена: {price} рублей.'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                   caption=text,
                                   reply_markup=markup)


# Обработчик подтверждения регистрации товара.
@dp.message_handler(IsAdmin(), text=all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        # Здесь данные, которыми мы наполняли словарь контекста. Теперь мы сможем сделать запись в базу данных.
        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']

        # Получаем название категории по ее идентификатору и записываем в переменную tag.
        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?',
            (data['category_index'],))[0]
        # Формируем и хэшируем строку с параметрами товара, что не хранить их в явном виде.
        # Формируем id товара для этого мы берем название, описание, цену и категорию и хэшируем(шифруем) их
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()

        # Выполняем вставку в базу данных.
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag))

    # Выключаем состояние и выводим соответствующую надпись.
    await state.finish()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())  # Убирает кнопки из клавиатуры Телеграмма
    await process_settings(message)


# Обработчик удаления. Срабатывает когда на карточке товара(show_products) нажимают кнопку "Удалить"
@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):
    product_idx = callback_data['id']  # Из словаря callback_data в show_products мы получаем id товара
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))  # Удаляем товар из базы данных по id
    await query.answer('Удалено!')  # Отправляем сообщение
    await query.message.delete()  # Убираем карточку товара


# Обработчик для изменения цены
@dp.message_handler(IsAdmin(), text=back_message,  # Данный обработчик срабатывает
                    state=ProductState.confirm)  # при состоянии подтверждения добавления товара (confirm).
async def process_confirm_back(message: Message, state: FSMContext):
    await ProductState.price.set()  # Включаем состояние изменения цены.

    # Т.к. мы меняем цену, нам нужно знать текущее ее значение,
    # поэтому обращаемся к словарю контекста за текущим значением цены.
    async with state.proxy() as data:
        await message.answer(f"Изменить цену с <b>{data['price']}</b>?",
                             reply_markup=back_markup())


# Обработчик, когда мы хотим изменить описание товара или, когда вместо фото, добавили текст
@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT,  # С указанным обработчиком работаем,
                    state=ProductState.image)  # Когда добавляем фото, т.е. включено соответствующее состояние.
async def process_image_url(message: Message, state: FSMContext):
    # Если нажимаем кнопку «Назад», включаем состояние изменения описания (body).
    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:
            # Предлагаем подтвердить изменение описания.
            await message.answer(f"Изменить описание с <b>{data['body']}</b>?",
                                 reply_markup=back_markup())
    # Если вместо фото вводим текст.
    else:
        await message.answer('Вам нужно прислать фото товара.')


# Обработчик на случай указания цены/фото в неверном формате
@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.price)
# lambda message: not message.text.isdigit()
# Обработчик будет реагировать если в качестве цены мы введем не число.
async def process_price_invalid(message: Message, state: FSMContext):
    # Если мы возвращаемся
    if message.text == back_message:

        # То включается состояние изменения фото
        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Другое изображение?",
                                 reply_markup=back_markup())
    # Если же мы ввели не число - выдает ошибку
    else:

        await message.answer('Укажите цену в виде числа!')


@dp.message_handler(IsAdmin(),  # Данный обработчик срабатывает
                    # Когда мы вместо подтверждения добавления товара или отмены добавления пишем текст
                    lambda message: message.text not in [back_message, all_right_message],
                    state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варианта не было.')
