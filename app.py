import os
import logging
from queue import Queue
from threading import Thread
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, Filters, Dispatcher
from telegram.update import Update
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv

from flask import Flask, json, request
from telegram import Bot, ParseMode
from telebot.credentials import bot_token

import mysql.connector
import time

# define variables
PORT = int(os.environ.get('PORT', '8443'))
TOKEN = bot_token
bot = Bot(token=TOKEN)
update_queue = Queue()
dp = Dispatcher(bot, update_queue)
STORING_QUESTION, SUBSCRIBE_QUESTIONID, UNSUBSCRIBE_QUESTIONID, STARTED = range(4)

# define function for connecting / closing database
def connectdb():
    global conn, cur
    conn = mysql.connector.connect(user='bb75a740c4787a', password='6ae814c8', host='us-cdbr-east-04.cleardb.com', database='heroku_aff68423aab93c1')
    cur = conn.cursor()

def closedb(commit):
    conn.commit() if commit is True else None
    cur.close()
    conn.close()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
                               


# functions for handlers
# function for error handler
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# functions for /start
def start(update, context):
    """Send a message and show the main menu when the command /start is issued."""
    update.message.reply_text('Welcome to the TeleAsk bot!')
    time.sleep(0.5)
    update.message.reply_text('What is your meeting id?')
    return STARTED

def start_meetingid(update,context):        # for more than 1 meetings
    meetingid = update.message.text
    update.message.reply_text(f'Meeting ID {meetingid} stored!')
    help(update, context)
    return ConversationHandler.END



# function for /help
def help(update, context):
    """Send the main menu when the command /help is issued."""
    mainmenu = '''/ask - ask a question
/subscribe - get notifications for any of the question
/unsubscribe - remove any previous subscriptions
/help - show this menu again

See all the questions here: 
https://chongsters-web.herokuapp.com/
'''
    update.message.reply_text(mainmenu)



# functions for /ask
def ask(update, context):
    update.message.reply_text('What is your question?')
    return STORING_QUESTION

def ask_storequestion(update, context):
    # process through NLP
    # if repetitive, prompt the user and suggest that they subscribe to the other question

    # use inline keyboard
    # options_yesno = {'inline_keyboard':
    #             [[{'text': 'Yes', 'callback_data': update.message.text}], [{'text': 'No', 'callback_data': '0'}]]}
    # bot.sendMessage(chat_id=update.message.chat.id, text='Your question is "' + update.message.text + '". Send this to the presenter?', reply_markup=reply_markup)
    
    # update the question into the database
    connectdb()
    cur.execute('SET @@auto_increment_increment=1')
    cur.execute('INSERT INTO questions (question_text) VALUES (%s)',(update.message.text,))
    closedb(commit=True)

    update.message.reply_text(f'Your question "{update.message.text}" has been added!')
    return ConversationHandler.END



# functions for /subscribe
def subscribe(update, context):
    """Get question id from user to subscribe"""
    bot.sendMessage(chat_id=update.message.chat.id, text='What is the question id that you want to *subscribe* to?', parse_mode=ParseMode.MARKDOWN_V2)
    return SUBSCRIBE_QUESTIONID

def subscribe_questionid(update, context):
    connectdb()    
    # check if there is such a question id
    cur.execute('SELECT * FROM questions WHERE question_id = %s', (update.message.text,))
    if len(cur.fetchall()) == 0:
        update.message.reply_text('No such question!')
        closedb(commit=False)
        return ConversationHandler.END
    else:
        # check if user is already in the subscription list
        cur.execute('SELECT chat_id FROM subscriptions WHERE question_id = %s', (update.message.text,))
        for chat_id in cur:
            if chat_id[0] == update.message.chat.id:
                update.message.reply_text('Already in subscription list!')
                closedb(commit=False)
                return ConversationHandler.END
    
    cur.execute('SET @@auto_increment_increment=1')
    cur.execute('INSERT INTO subscriptions (chat_id, question_id) VALUES(%s, %s)', (update.message.chat.id, update.message.text))
    closedb(commit=True)

    update.message.reply_text(f"Added {update.message.from_user.username} to question {update.message.text}'s subscription list!")
    return ConversationHandler.END



# functions for /unsubscribe
def unsubscribe(update, context):
    """Get question id from user to unsubscribe"""
    bot.sendMessage(chat_id=update.message.chat.id, text='What is the question id that you want to *unsubscribe* from?', parse_mode=ParseMode.MARKDOWN_V2)
    return UNSUBSCRIBE_QUESTIONID

def unsubscribe_questionid(update, context):
    connectdb()    
    # check if there is such a question id
    cur.execute('SELECT * FROM questions WHERE question_id = %s', (update.message.text,))
    if len(cur.fetchall()) == 0:
        update.message.reply_text('No such question!')
        closedb(commit=False)
        return ConversationHandler.END

    else:
        # delete only if chat_id is in the subscription list
        cur.execute('SELECT chat_id FROM subscriptions WHERE question_id = %s', (update.message.text,))
        for chat_id in cur:
            if chat_id[0] == update.message.chat.id:
                cur.execute('DELETE FROM subscriptions WHERE chat_id = %s AND question_id = %s', (update.message.chat.id, update.message.text))
                closedb(commit=True)
                update.message.reply_text(f"Deleted {update.message.from_user.username} from question {update.message.text}'s subscription list!")
                return ConversationHandler.END
    
    update.message.reply_text(f"{update.message.from_user.username} is not in question {update.message.text}'s subscription list!")
    closedb(commit=False)
    return ConversationHandler.END



# Flask application and routes
app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

@app.before_first_request
def main():
    # on different commands - answer in Telegram
    dp.add_handler(ConversationHandler(
                    entry_points=[CommandHandler("start", start)],
                    states={STARTED: [MessageHandler(Filters.text, start_meetingid)]},
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

# processing requests made by user from telebot
@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(), bot)

    if update.message == None:
        return 'bad update'

    update_queue.put(update)
    return 'good update'

@app.route('/answer', methods=['GET','POST'])
@cross_origin()
def answer():
    connectdb()
    input_json = request.get_json(force=True)
    answer_question_text = input_json["answer"]
    question_id = input_json["id"]

    # update the answer to the database
    cur.execute('UPDATE questions SET question_answer= %s WHERE question_id= %s',(answer_question_text, question_id))

    # get list of subscriptions and the text of the question from DB
    cur.execute('SELECT question_text FROM questions WHERE question_id = %s', (question_id,))
    question = cur.fetchone()[0]
    cur.execute('SELECT chat_id FROM subscriptions WHERE question_id = %s', (question_id,))
    records = cur.fetchall()

    # notify each subscriber of the answer to the question
    if len(records) != 0:
        for (chat_id,) in records:
            chat_id = str(chat_id)
            bot.sendMessage(chat_id=chat_id, text=f'The question "{question}" has been answered! Here is the answer:')
            time.sleep(1)
            bot.sendMessage(chat_id=chat_id, text=answer_question_text)

    closedb(commit=True)
    return "ok"

@app.route('/retrieve', methods=['GET', 'POST'])
@cross_origin()
def retrieve():
    connectdb()
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
    closedb(commit=False)
    return json_data


if __name__ == '__main__':
    app.run(threaded=True)
