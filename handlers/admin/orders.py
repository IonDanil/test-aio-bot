from aiogram.types import Message
from loader import dp, db
from handlers.user.menu import orders
from filters import IsAdmin


# обработчик – для отображения списка заказов
@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):

    list_orders = db.fetchall('SELECT * FROM orders')

    if len(list_orders) == 0:
        await message.answer('У вас нет заказов.')
    else:
        await order_answer(message, list_orders)


# обработчик – для отображения содержимого заказа
async def order_answer(message, list_orders):

    res = ''

    for order in list_orders:
        res += f'Заказ <b>№{order[3]}</b>\n\n'

    await message.answer(res)

