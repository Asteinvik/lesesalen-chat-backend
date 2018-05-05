import os
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy

DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password=db.Column(db.String(120))



if __name__ == '__main__':
    socketio.run(app)

@app.route('/')
def index():
    return ('hello world!')

@socketio.on('message')
def handle_message(message):
    emit('message', {'data': message}, broadcast=True, include_self=False)

@socketio.on('connect')
def connect():
    id = 1
    emit('on_connect', {'data': 'You are connected. ID: %d' % id})



