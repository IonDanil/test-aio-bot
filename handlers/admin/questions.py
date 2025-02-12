from handlers.user.menu import questions
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import all_right_message, cancel_message, \
    submit_markup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.types.chat import ChatActions

from states import AnswerState
from loader import dp, db, bot
from filters import IsAdmin

# Формируем шаблон с возвращаемыми данными.
# В нем обязательно должен быть идентификатор пользователя, поскольку нам нужно знать, кому слать ответ
question_cb = CallbackData('question', 'cid', 'action')


@dp.message_handler(IsAdmin(), text=questions)
async def process_questions(message: Message):
    # Имитируем набор сообщения человеком
    await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
    # Получаем список вопросов из базы данных
    questions = db.fetchall('SELECT * FROM questions')

    # Если их нет, выводим соответствующее сообщение
    if len(questions) == 0:

        await message.answer('Нет вопросов.')

    # Если вопросы имеются, для каждого формируем кнопку
    else:

        for cid, question in questions:
            markup = InlineKeyboardMarkup()
            # И добавляем в разметку.
            # К каждой кнопке привязываем обработчик. При его нажатии будет передаваться идентификатор пользователя
            markup.add(InlineKeyboardButton(
                'Ответить',
                callback_data=question_cb.new(cid=cid, action='answer')))

            await message.answer(question, reply_markup=markup)


# Обработчик, обеспечивающий переход к вводу ответа
@dp.callback_query_handler(IsAdmin(), question_cb.filter(action='answer'))
async def process_answer(query: CallbackQuery, callback_data: dict,
                         state: FSMContext):
    # Пополняем словарь контекста идентификатором пользователя.
    # Идентификатор получаем из «коллбека» с данными
    async with state.proxy() as data:
        data['cid'] = callback_data['cid']
    # Предлагаем админу ввести ответ на вопрос пользовтаеля
    await query.message.answer('Напиши ответ.',
                               reply_markup=ReplyKeyboardRemove())
    # Устанавливаем состояние ожидания ответа на вопрос
    await AnswerState.answer.set()


# Обработчик подтверждения правильности ответа
@dp.message_handler(IsAdmin(), state=AnswerState.answer)
async def process_submit(message: Message, state: FSMContext):
    # Пополняем словарь контекста текстом сообщения – ответом на вопрос
    async with state.proxy() as data:
        data['answer'] = message.text
    # Переключаемся в состояние подтверждения ответа.
    await AnswerState.next()
    await message.answer('Убедитесь, что не ошиблись в ответе.',
                         reply_markup=submit_markup())


# обработчик отмены ответа
@dp.message_handler(IsAdmin(), text=cancel_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):
    await message.answer('Отменено!', reply_markup=ReplyKeyboardRemove())
    # Выключаем состояние. Это означает откат к исходному положению.
    await state.finish()


# Обработчик отправки ответа пользователю
@dp.message_handler(IsAdmin(), text=all_right_message, state=AnswerState.submit)
async def process_send_answer(message: Message, state: FSMContext):

    # Получаем ответ пользователя и его идентификатор
    async with state.proxy() as data:

        answer = data['answer']
        cid = data['cid']

        # Получаем вопрос пользователя
        question = db.fetchone(
            'SELECT question FROM questions WHERE cid=?', (cid,))[0]
        # Удаляем вопрос пользователя
        db.query('DELETE FROM questions WHERE cid=?', (cid,))
        # Формируем текст вопроса и ответа
        text = f'Вопрос: <b>{question}</b>\n\nОтвет: <b>{answer}</b>'

        # Извещаем админа об отправке ответа
        await message.answer('Отправлено!', reply_markup=ReplyKeyboardRemove())
        # Отправляем ответ автору вопроса
        await bot.send_message(cid, text)
    # Выключаем состояние
    await state.finish()


