from flask import *

# creates the flask app
app = Flask(__name__)

@app.route('/')
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