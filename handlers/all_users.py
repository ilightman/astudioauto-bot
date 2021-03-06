import logging

from aiogram import types, filters

from main import dp, bot
from misc import inline_kb_constructor, retail_info_by_phone_number, TrackNumber


@dp.callback_query_handler(filters.Text(startswith='tracking'))
async def process_callback_button_tracking(callback_query: types.CallbackQuery):
    track = TrackNumber(callback_query.message.text.split()[-1])
    await bot.send_message(callback_query.message.chat.id, await track.track_down(), reply_markup=None)
    logging.info(f'{track.type}:{track.number}:{callback_query.message.from_user.id}:'
                 f'{callback_query.message.from_user.full_name}')


@dp.message_handler(regexp=r'(^\d{14}$)|(^[A-Z]{2}\d{9}[A-Z]{2}$)|(^[^9]\d{9}$)')
async def tracking(message: types.Message):
    track = TrackNumber(message.text)
    await message.answer(await track.track_down())
    logging.info(f'{track.type}:{track.number}:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(content_types='contact')
@dp.message_handler(regexp=r'(^[+][7]\d{10}$)|(^[7-8]\d{10}$)|(^[9]\d{9}$)')
async def contact(message: types.Message):
    phone_num = message.contact.phone_number if message.content_type == 'contact' else message.text
    msg, track = await retail_info_by_phone_number(phone_num)
    if track:
        kb_inl = await inline_kb_constructor({'Отследить тут': 'tracking',
                                              track.type: track.ext_tracking_link()}, 2)
        await message.answer(msg, reply_markup=kb_inl)
    else:
        await message.answer(msg, reply_markup=types.ReplyKeyboardRemove())
    logging.info(f'{track if track else None}:'
                 f'{phone_num}:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler(commands=['start', 'help'])
async def start_help(message: types.Message):
    """
        This handler will be called when user sends `/start` or `/help` command
    """
    message_text = 'Вот, что я умею:\n' \
                   '/start , /help - отображает список моих команд\n' \
                   'Умею отслеживать информацию по номеру телефона или по трек номеру, просто отправь мне свой номер'
    kb1 = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb1.add(types.KeyboardButton('Этот номер', request_contact=True))
    await message.answer(message_text, reply_markup=kb1)
    logging.info(f'{message.text}:{message.from_user.id}:{message.from_user.full_name}')


@dp.message_handler()
async def echo(message: types.Message):
    """echo"""
    await message.answer(str(message))
    logging.info(f'{message.from_user.id}:{message.from_user.full_name}')
