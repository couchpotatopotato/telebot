import os
import logging
from queue import Queue
from threading import Thread
from flask.templating import render_template
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, Dispatcher, callbackqueryhandler, dispatcher
from dotenv import load_dotenv
from telegram.update import Update

from flask import Flask, json, request
from telegram import Bot
from telebot.credentials import bot_token, bot_user_name, URL

import mysql.connector
import time

# define variables
PORT = int(os.environ.get('PORT', '8443'))
TOKEN = bot_token
bot = Bot(token=TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)

# create dictionary storing chat_id and group title/username key-value pairs
SUBSCRIPTION_CHAT_ID_TO_USERNAME = {} 

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()

# connect to the database
conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
print('conn done')
cur = conn.cursor()
print('cur done')

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message and show the main menu when the command /start is issued."""
    print('-----START FUNCTION-----')
    remove_unneeded_handlers()
    update.message.reply_text('Welcome to the chongsters bot!')
    help(update, context)  # to show the main menu

def help(update, context):
    """Send the main menu when the command /help is issued."""
    print('-----HELP FUNCTION-----')
    remove_unneeded_handlers()
    mainmenu = '''
    /ask - ask a question
    /subscribe - get notifications for any of the question

    See all the questions here: 
    https://chong-testbot.herokuapp.com/
    '''
    update.message.reply_text(mainmenu)

# def echo(update, context):
#     """Echo the user message."""
#     print('-----ECHO FUNCTION-----')
#     update.message.reply_text(update.message.text)
  
#     cur.execute('INSERT INTO questions (question_text, question_answer) VALUES (%s, %s)', (update.message.text, 'no answer yet'))
#     print('insert done')

#     cur.execute('SELECT * FROM questions')
#     for row in cur.fetchall():
#         print(row)

def ask(update, context):
    print('----------ASK FUNCTION-------------')
    remove_unneeded_handlers()
    update.message.reply_text('What is your question?')
    dp.add_handler(MessageHandler(Filters.text, ask_getquestion))

def ask_getquestion(update, context):
    print('-----getting the question-------')
    remove_unneeded_handlers()

    # ensure that there is a question
    question = update.message.text
    if question == '':
        update.message.reply_text('Enter a question!')
        help(update, context)
    else:
        # process through NLP
        # if repetitive, prompt the user and suggest that they subscribe to the other question

        options_yesno = {'inline_keyboard':[[{'text': 'yes', 'callback_data': update.message.text}], [{'text': 'no', 'callback_data': '0'}]]}
        bot.sendMessage(chat_id=update.message.chat.id, text='Your question is "' + update.message.text + '". Send this to the presenter?', reply_markup=options_yesno)

        dp.add_handler(CallbackQueryHandler(callback=ask_sendquestion))

def ask_sendquestion(update, context):
    print('----------sending the question-----------')
    remove_unneeded_handlers()

    if update.callback_query.data != '0':
        cur.execute('INSERT INTO questions (question_text) VALUES (%s)', (update.callback_query.data))
        # check for errors
        update.message.reply_text('Your message has been added!')
    else:
        ask(update)

def error(update, context):
    """Log Errors caused by Updates."""
    print('-----ERROR FUNCTION-----')
    remove_unneeded_handlers()
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def subscribe(update, context):
    """Add users to subscription list to allow sending of messages later"""
    remove_unneeded_handlers()
    if not SUBSCRIPTION_CHAT_ID_TO_USERNAME.get(update.message.chat.id, False):
        # store group title/username for groups/private chat respectively as the value
        SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] = update.message.chat.title if update.message.chat.type == 'group' else '@' + update.message.from_user.username
        update.message.reply_text(SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] + ' has been added to the subscription list!')

    else:
        update.message.reply_text(SUBSCRIPTION_CHAT_ID_TO_USERNAME[update.message.chat.id] + ' is already in the subscription list!')

def unsubscribe(update, context):
    """Remove user from subscription list"""
    remove_unneeded_handlers()
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

def remove_unneeded_handlers():
    dp.remove_handler(MessageHandler(Filters.text, ask_getquestion))
    dp.remove_handler(CallbackQueryHandler(callback=ask_sendquestion))

# creates the flask app
app = Flask(__name__)

@app.before_first_request
def main():
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("ask", ask))

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
    
@app.route('/answer')
def answer():
    answer = request.args.get('answer')


        
@app.route('/')
def welcome():
    return "<h1>Welcome to THE CHONGSTERS server!!</h1>"

def answer_question():
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    cur = conn.cursor()
    print("cur done!")
    answer_question_text = "testing_answer"
    question_id = 235
    cur.execute('UPDATE questions SET question_answer= %s WHERE question_id= %s', (answer_question_text, question_id))
    print('update done')
    conn.commit()
    cur.close()
    conn.close()
  
if __name__ == '__main__':
    app.run(threaded=True)
