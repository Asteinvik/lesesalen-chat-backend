import os
from flask import Flask, render_template, request, json, Response
from flask_socketio import SocketIO, send, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime


DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.String(120))
    registered_on = db.Column('registered_on' , db.DateTime)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.utcnow()
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.id)
 
    def __repr__(self):
        return '<User %r>' % (self.username)



if __name__ == '__main__':
    socketio.run(app)

@app.route('/')
def index():
    return ('hello world!')

@login_manager.user_loader
def load_user(id):
    '''
    Loads a User object based on id
    '''
    return User.query.get(int(id))

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        # TODO: Validate input
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User(username, password, email)
        try:
            db.session.add(user)
            db.session.commit()
            js = json.dumps({
                'message': 'Registered user %s' % username,
                'testField': 420
            })
            return Response(js, status = 200, mimetype='application/json')
        except:
            js = json.dumps({
                'message': 'Username or email already exist',
                'testField': 420
            })
            return Response(js, status = 409, mimetype='application/json')

@app.route('/login', methods=['GET','POST'])
def login():
    return 'login route'

@socketio.on('message')
def handle_message(message):
    emit('message', {'data': message}, broadcast=True, include_self=False)

@socketio.on('connect')
def connect():
    id = 1
    emit('on_connect', {'data': 'You are connected. ID: %d' % id})



