from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

if __name__ == '__main__':
    socketio.run(app)

@app.route('/')
def index():
    return ('hello world!')

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
