from aiogram.types import ReplyKeyboardMarkup

back_message = '👈 Назад'
all_right_message = '✅ Все верно'
cancel_message = '🚫 Отменить'


# Функция добавления в меню кнопки возврата при редактировании
def back_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(back_message)

    return markup


# Функция размещения клавиатуры с кнопками подтверждения и перехода на предыдущий шаг.
def check_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(back_message, all_right_message)

    return markup


confirm_message = '✅ Подтвердить заказ'


def confirm_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(confirm_message)
    markup.add(back_message)

    return markup

# Функция для формирования разметки клавиатуры для подтверждения вопроса пользователя
def submit_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row(cancel_message, all_right_message)

    return markup






