from flask import *
import os

# creates the flask app
app = Flask(__name__)

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
    return "<h1>Welcome to our server !!</h1>"
