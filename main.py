# using python-telegram-bot

from telegram import *
from telegram.ext import *

bot = Bot("1888950275:AAFX1jKq1kxhYhg2yfYW30k1WszssJijSIs")
updater = Updater(
    "1888950275:AAFX1jKq1kxhYhg2yfYW30k1WszssJijSIs", use_context=True)

dispatcher = updater.dispatcher


def test_function(update: Update, context: CallbackContext):
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="hi"
    )


start_value = CommandHandler("bye", test_function)
dispatcher.add_handler(start_value)
updater.start_polling()
