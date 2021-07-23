import os
import logging
from queue import Queue
from threading import Thread
from flask.templating import render_template
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters, Dispatcher, dispatcher, messagehandler
from dotenv import load_dotenv
from telegram.message import Message
from telegram.update import Update
from flask_cors import CORS, cross_origin

from flask import Flask, json, request
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.credentials import bot_token, bot_user_name, URL

import mysql.connector
import time

# define variables
PORT = int(os.environ.get('PORT', '8443'))
TOKEN = bot_token
bot = Bot(token=TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)
STORING_QUESTION, SUBSCRIBE_QUESTIONID, UNSUBSCRIBE_QUESTIONID, STARTED = range(4)
# create dictionary storing chat_id and group title/username key-value pairs
SUBSCRIPTION_CHAT_ID_TO_USERNAME = {}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
load_dotenv()
                               
# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message and show the main menu when the command /start is issued."""
    print('-----START FUNCTION-----')
    update.message.reply_text('Welcome to the chongsters bot!')
    time.sleep(0.5)
    update.message.reply_text('What is your meeting id?')
    return STARTED

def store_meetingid(update,context):
    meetingid = update.message.text
    # check if meeting id is inside the database
    update.message.reply_text(f'Meeting ID {meetingid} stored!')
    help(update, context)
    return ConversationHandler.END


def help(update, context):
    """Send the main menu when the command /help is issued."""
    print('-----HELP FUNCTION-----')
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
    update.message.reply_text('What is your question?')
    return STORING_QUESTION

def ask_storequestion(update, context):
    print('-----storing the question-------')

    # process through NLP
    # if repetitive, prompt the user and suggest that they subscribe to the other question

    # options_yesno = {'inline_keyboard':
    #             [[{'text': 'Yes', 'callback_data': update.message.text}], [{'text': 'No', 'callback_data': '0'}]]}
    # bot.sendMessage(chat_id=update.message.chat.id, text='Your question is "' + update.message.text + '". Send this to the presenter?', reply_markup=reply_markup)
    
    # update the question into the database
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')
    cur.execute('INSERT INTO questions (question_text) VALUES (%s)',(update.message.text))
    conn.commit()

    update.message.reply_text(f'Your question "{update.message.text}" has been added!')
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    print('-----ERROR FUNCTION-----')
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def subscribe(update, context):
    """Get question id from user to subscribe"""
    update.message.reply_text('What is the question id that you want to subscribe to?')
    return SUBSCRIBE_QUESTIONID

def subscribe_questionid(update, context):
    # check if the user is already in the subscription list
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')
    cur.execute('SELECT chat_id FROM subscriptions WHERE question_id = %s', update.message.text)
    for chat_id in cur:
        if chat_id[0] == update.message.chat.id:
            update.message.reply_text('Already in subscription list!')
            cur.close()
            conn.close()
            return ConversationHandler.END
    
    cur.execute('INSERT INTO subscriptions (chat_id, question_id) VALUES(%s, %s)', update.message.chat.id, update.message.text)
    conn.commit()
    cur.close()
    conn.close()

    update.message.reply_text(f"Added {update.message.from_user.username} to question {update.message.text}'s subscription list!")
    return ConversationHandler.END

def unsubscribe(update, context):
    """Get question id from user to unsubscribe"""
    update.message.reply_text('What is the question id that you want to unsubscribe from?')
    return UNSUBSCRIBE_QUESTIONID

    """Remove user from subscription list"""
    # check if group / private chat, and thus store group name / username respectively
    if update.message.chat.type == 'group':
        username_or_group = update.message.chat.title
    else:
        username_or_group = '@' + update.message.from_user.username

    if not SUBSCRIPTION_CHAT_ID_TO_USERNAME.pop(update.message.chat.id, False):
        # return group name / username not in subscription list
        update.message.reply_text(
            username_or_group + ' is not in the subscription list!')
    else:
        update.message.reply_text(
            username_or_group + ' has been removed from the subscription list!')

def unsubscribe_questionid(update, context):
    # check if the user is already in the subscription list
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')
    cur.execute('SELECT chat_id FROM subscriptions WHERE question_id = %s', update.message.text)
    

    for chat_id in cur:
        if chat_id[0] == update.message.chat.id:
            cur.execute('DELETE FROM subscriptions WHERE chat_id = %s AND question_id = %s', (update.message.chat.id, update.message.text))
            conn.commit()
            cur.close()
            conn.close()
            update.message.reply_text(f"Deleted {update.message.from_user.username} from question {update.message.text}'s subscription list!")
            return ConversationHandler.END
    
    update.message.reply_text(f"{update.message.from_user.username} is not in question {update.message.text}'s subscription list!")
    cur.close()
    conn.close()
    return ConversationHandler.END
            
# creates the flask app
app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

@app.before_first_request
def main():
    # on different commands - answer in Telegram
    dp.add_handler(ConversationHandler(
                    entry_points=[CommandHandler("start", start)],
                    states={STARTED: [MessageHandler(Filters.text, store_meetingid)]},
                    fallbacks=[]
    ))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(ConversationHandler(
                    entry_points=[CommandHandler("ask", ask)],
                    states={STORING_QUESTION: [MessageHandler(Filters.text, ask_storequestion)]},
                    fallbacks=[]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("subscribe", subscribe)],
        states={SUBSCRIBE_QUESTIONID: [MessageHandler(Filters.text, subscribe_questionid)]},
        fallbacks=[]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("unsubscribe", unsubscribe)],
        states={UNSUBSCRIBE_QUESTIONID: [MessageHandler(Filters.text, unsubscribe_questionid)]},
        fallbacks=[]
    ))

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

    print(update.message.text +
          "--------------------------------------------------------")
    # Telegram understands UTF-8, so encode text for unicode compatibility
    # text = update.message.text.encode('utf-8').decode()

    update_queue.put(update)

    return 'good update'


@app.route('/sendmessage')
def sendmessage():
    message = request.args.get('message')

    # send the message to everyone in the subscription list
    if len(SUBSCRIPTION_CHAT_ID_TO_USERNAME) == 0:
        return 'no one has subscribed to the bot yet'
    else:
        for chat_id in SUBSCRIPTION_CHAT_ID_TO_USERNAME:
            bot.sendMessage(chat_id=chat_id, text=message)

        # print the subscription list after sending messages
        subscriptionlist = '\n'.join(SUBSCRIPTION_CHAT_ID_TO_USERNAME.values())
        return 'sent to ' + str(len(SUBSCRIPTION_CHAT_ID_TO_USERNAME)) + ' persons/groups\n' + subscriptionlist


@app.route('/')
def welcome():
    return "<h1>Welcome to THE CHONGSTERS server!!</h1>"


@app.route('/answer', methods=['GET','POST'])
@cross_origin()
def answer():
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')
    input_json = request.get_json(force=True)
    answer_question_text = input_json["answer"]
    question_id = input_json["id"]
    cur.execute('UPDATE questions SET question_answer= %s WHERE question_id= %s',(answer_question_text, question_id))
    conn.commit()
    cur.close()
    conn.close()
    return "ok"

@app.route('/retrieve', methods=['GET', 'POST'])
@cross_origin()
def retrieve():
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    print('conn done')
    cur = conn.cursor()
    print('cur done')
    retrieved_data = []
    cur.execute("""SELECT questions.question_id, questions.question_text, questions.question_answer, 
    count(subscriptions.question_id) AS subscription_count 
    FROM subscriptions
    RIGHT JOIN questions on questions.question_id=subscriptions.question_id
    GROUP BY question_id""")
    for row in cur.fetchall():
        dict = {}
        dict["question_id"] = row[0]
        dict["question_text"] = row[1]
        dict["question_answer"] = row[2]
        dict["subscription_count"] = row[3]
        retrieved_data.append(dict)
    json_data = json.dumps(retrieved_data)
    cur.close()
    conn.close()
    return json_data


if __name__ == '__main__':
    app.run(threaded=True)
