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

global bot
global TOKEN
TOKEN = bot_token
bot = Bot(token=TOKEN)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
update_queue = Queue()
dp = Dispatcher(bot, update_queue)


#COMMAND HANDLERS
def start_cmd(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! I\'m created by the WANKSTERS. \n I will just repeat what you say OKAY')
def help_cmd(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')
def echo_cmd(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    
    
#FLASK APP
app = Flask(__name__)

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

    
def get_response(update):
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(MessageHandler(Filters.text, echo_cmd))
    dp.add_error_handler(error)

 
@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), bot)
    update_queue.put(update)
    response = get_response(update)
    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()
    return 'ok'
    #chat_id = update.message.chat.id
    #msg_id = update.message.message_id
    #text = update.message.text.encode('utf-8').decode()


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
