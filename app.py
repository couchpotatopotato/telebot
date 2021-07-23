import os
import logging
from queue import Queue
from threading import Thread
from flask.templating import render_template
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher, dispatcher
from dotenv import load_dotenv
from telegram.update import Update

from flask import Flask, json, request
from telegram import Bot
from telebot.credentials import bot_token, bot_user_name, URL

from pprint import pprint

import mysql.connector

PORT = int(os.environ.get('PORT', '8443'))
TOKEN = bot_token
bot = Bot(token=TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)
SUBSCRIPTION_CHAT_ID_TO_USERNAME = {}   # create dictionary storing chat_id and group title/username key-value pairs

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    # bot.sendMessage(chat_id=chat_id, text="YOU ARE ASKING ME TO START", reply_to_message_id=msg_id)
    print('-----START FUNCTION-----')
    update.message.reply_text('Hi! I\'m created by THE CHONGSTERS. \n I will just repeat what you say OKAY')

def help(update, context):
    """Send a message when the command /help is issued."""
    print('-----HELP FUNCTION-----')
    update.message.reply_text('Help!')

    # bot.sendMessage(chat_id=chat_id, text="YOU ARE ASKING ME TO HELP", reply_to_message_id=msg_id)

def echo(update, context):
    """Echo the user message."""
    print('-----ECHO FUNCTION-----')
    update.message.reply_text(update.message.text)
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')

    cur.execute('INSERT INTO questions (question_text, question_answer) VALUES (%s, %s)', (update.message.text, 'no answer yet'))
    print('insert done')

    cur.execute('SELECT * FROM questions')
    for row in cur.fetchall():
        print(row)

    conn.commit()
    cur.close()
    conn.close()

def error(update, context):
    """Log Errors caused by Updates."""
    print('-----ERROR FUNCTION-----')
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def subscribe(update, context):
    """Add users to subscription list to allow sending of messages later"""
    if not SUBSCRIPTION_CHAT_ID_TO_USERNAME.get(update.message.chat.id, False):
        # store group title/username for groups/private chat respectively as the value
        SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] = update.message.chat.title if update.message.chat.type == 'group' else '@' + update.message.from_user.username
        update.message.reply_text(SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] + ' has been added to the subscription list!')

    else:
        update.message.reply_text(SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] + ' is already in the subscription list!')

def unsubscribe(update, context):
    """Remove user from subscription list"""
    # check if group / private chat, and thus store group name / username respectively
    if update.message.chat.type == 'group':
        username_or_group = update.message.chat.title
    else:
        username_or_group = '@' + update.message.from_user.username

    if not SUBSCRIPTION_CHAT_ID_TO_USERNAME.pop(update.message.chat.id, False):
        # return group name / username not in subscription list
        update.message.reply_text(username_or_group + ' is not in the subscription list!')
    else:
        update.message.reply_text(username_or_group + ' has been removed from the subscription list!')


# creates the flask app
app = Flask(__name__)

@app.before_first_request
def main():
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the thread
    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()

    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    # bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    # something to let us know things work
    print("---------------------------------------------webhook STARTED----------------------------------------------")

# processing requests made by user from telebot
@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond(): 
    update = Update.de_json(request.get_json(), bot)

    if update.message == None:
        return 'bad update'

    print(update.message.text + "--------------------------------------------------------")
    # Telegram understands UTF-8, so encode text for unicode compatibility
    # text = update.message.text.encode('utf-8').decode()

    update_queue.put(update)

    return 'good update'

@app.route('/sendmessage')
def sendmessage():
    message = request.args.get('message')
    
    # send the message to everyone in the subscription list
    if len(SUBSCRIPTION_CHAT_ID_TO_USERNAME) == 0 :
        return 'no one has subscribed to the bot yet'
    else:
        for chat_id in SUBSCRIPTION_CHAT_ID_TO_USERNAME:
            bot.sendMessage(chat_id=chat_id, text=message)
        
        # print the subscription list after sending messages
        subscriptionlist = '\n'.join(SUBSCRIPTION_CHAT_ID_TO_USERNAME.values())
        return 'sent to ' + str(len(SUBSCRIPTION_CHAT_ID_TO_USERNAME)) + ' persons/groups\n' + subscriptionlist
    

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
    return "<h1>Welcome to THE CHONGSTERS server!!</h1>"

def answer_question(update, context):
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    cur = conn.cursor()
    cur.execute('UPDATE questions SET question_answer= %s WHERE question_id= %s', (answer_question_text, question_id))
    print('update done')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/answerquestion', method=['GET', 'POST'])
def answerquestion():
    global answer_question_text
    answer_question_text = "testing_answering"
    global question_id 
    question_id = 245
  
if __name__ == '__main__':
    app.run(threaded=True)
