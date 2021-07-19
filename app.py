import os
import logging
from queue import Queue
from threading import Thread
from flask.templating import render_template
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher
from dotenv import load_dotenv
from telegram.update import Update

from flask import Flask, json, request
from telegram import Bot
from telebot.credentials import bot_token, bot_user_name,URL

PORT = int(os.environ.get('PORT', '8443'))
TOKEN = bot_token
bot = Bot(token=TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! I\'m created by the WANKSTERS. \n I will just repeat what you say OKAY')

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)



# creates the flask app
app = Flask(__name__)

@app.route('/setwebhook', methods=['GET', 'POST'])
def start_telebot():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    global update_queue
    update_queue = Queue()

    dp = Dispatcher(bot, update_queue)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    print("webhook STARTED")

     # Start the thread
    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()
    
    return 'webhook started'
    # you might want to return dispatcher as well, 
    # to stop it at server shutdown, or to register more handlers:
    # return (update_queue, dispatcher)


# def set_webhook():
#     # we use the bot object to link the bot to our app which live
#     # in the link provided by URL
#     s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
#     # something to let us know things work
#     if s:
#         return "webhook setup ok"
#     else:
#         return "webhook setup failed"

@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond(): 
    update = Update.de_json(request.get_json(force=True), bot)
    print("tele message recieved")
    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()

    webhook(text)

    return 'ok'

def webhook(update):
    update_queue.put(update)

@app.route('/hello/', methods=['GET', 'POST'])
def index():
    message = 'Test'
    # message = request.args.get('message')

    # if there is no message submitted via HTML form yet, return None
    if message is None:
        return render_template('index.html')

    # else return acknowledgement that message is received
    else:
        print(message)
        return 'Sent to telebot!'
        
@app.route('/')
def welcome():
    return "<h1>Welcome to THE CHONGSTERS server !!</h1>"


if __name__ == '__main__':
   app.run(threaded=True)