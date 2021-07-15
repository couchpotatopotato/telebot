# using python-telegram-bot
import os
from telegram import *
from telegram.ext import *

PORT = int(os.environ.get('PORT', 5000))
TOKEN = os.getenv('TOKEN') 
bot = Bot(TOKEN)
updater = Updater(TOKEN, use_context=True)

dispatcher = updater.dispatcher


def test_function(update: Update, context: CallbackContext):
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="hi"
    )


start_value = CommandHandler("bye", test_function)
dispatcher.add_handler(start_value)
updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
updater.bot.setWebhook('https://chong-testbot.herokuapp.com/' + TOKEN)
