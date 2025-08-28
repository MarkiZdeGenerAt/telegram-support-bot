from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
