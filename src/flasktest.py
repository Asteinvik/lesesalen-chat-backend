import os
import math
import random as rnd
from datetime import datetime
from flask import Flask, render_template, request, json, Response
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt

DATABASE_URL = os.environ['DATABASE_URL']

rooms = [0]*1000

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password = db.Column(db.String(128))
    registered_on = db.Column('registered_on' , db.DateTime)

    def __init__(self, username, password, email):
        self.username = username
        bvalue = bytes(password, 'utf-8')
        self._password = bcrypt.generate_password_hash(bvalue).decode('utf-8')
        self.email = email
        self.registered_on = datetime.utcnow()
 
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return str(self.id)
 
    def __repr__(self):
        return '<User %r, pass: %s>' % (self.username, self.password)

    @hybrid_property
    def password(self):
        return self._password

    def is_correct_password(self, plaintext):
        if bcrypt.check_password_hash(self._password.encode('utf-8'), plaintext.encode('utf-8')):
            return True
        return False

class Message():
	
    def __init__(self,id,message,system=False):
        self.id = id
        self.createdAt = datetime.utcnow()
        self.text = message
        self.system = system

    def json(self):
    	return json.dumps({
    		'_id': str(self.id),
        	'text': str(self.text),
        	'createdAt': self.createdAt,
        	'system': str(self.system),
    		})
    

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
        user = User(username=username, password=password, email=email)
        try:
            db.session.add(user)
            db.session.commit()
            js = json.dumps({
                'status': 200,
                'message': 'Registered user %s' % username
            })
            return Response(js, status = 200, mimetype='application/json')
        except:
            js = json.dumps({
                'status': 409,
                'message': 'Username or email already exist'
            })
            return Response(js, status = 409, mimetype='application/json')


@app.route('/login',methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username).first_or_404()
    if registered_user.is_correct_password(password):
        login_user(registered_user)
        js = json.dumps({
            'status': 200,
            'message': 'Login success',
            'username': registered_user.username,
            'id': registered_user.id
        })
        return Response(js, status = 200, mimetype='application/json')
    else:
        js = json.dumps({
            'status': 403,
            'message': 'Invalid username or password'
        })
        return Response(js, status = 403, mimetype='application/json')


@app.route('/logout')
def logout():
    logout_user()
    js = json.dumps({
        'status': 200,
        'message': 'Logged out'
    })
    return Response(js, status = 200, mimetype='application/json')

@app.route('/secure')
@login_required
def secure():
    js = json.dumps({
        'status': 200,
        'message': 'Here is some very secure data!'
    })
    return Response(js, status = 200, mimetype='application/json')

@socketio.on('message')
def handle_message(message):
    emit('message', message, broadcast = True, include_self=False)

@socketio.on('connect')
def connect():
    msg= Message(-1,'You are now connected',True)
    emit('system', msg.json())


@socketio.on('join')
def on_join(data):
    username = data['username']
    user=db.session.query(User).filter_by(username=username).first()
    room = rooms[user.id]
    join_room(room)
    msg= Message(-2,username+' has entered the room.',True)
    emit('system', msg.json(), room=room)


#  @socketio.on('room_message')
#  def handle_room_message(data):
    #  username = data['username']
    #  user=db.session.query(User).filter_by(username=username).first()
    #  room = rooms[user.id]
    #  join_room(room)
    #  message_json = json.dumps({
        #  '_id': '-1',
        #  'text': username + ' has entered the room.',
        #  'createdAt': datetime.utcnow(),
        #  'system': 'true',
    #  })
    #  emit('system', message_json, room=room)


def giveRoom():
    nUsers=db.session.query(User).order_by(User.id).count()
    nRooms=math.ceil(nUsers/2)
    roomspace=(list(range(1,nRooms+1))+list(range(1,nRooms+1)))
    for user in db.session.query(User).order_by(User.id):
        rooms[user.id]=rnd.choice(roomspace)
        print(user.id,rooms[user.id])
