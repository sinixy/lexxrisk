from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


risk_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Текущие условия")],
    [KeyboardButton(text="Изменить стоп")],
    [KeyboardButton(text="Изменить кавер")],
    [KeyboardButton(text="Изменить фиксер")]
], resize_keyboard=True)

yes_no_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да", callback_data='yes'), InlineKeyboardButton(text="Нет", callback_data='no')]
])

cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data='cancel')]
])