from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send, emit, disconnect
import pickle


pickle.dump({}, open("users.p", "wb"))
pickle.dump({}, open("channels.p", "wb"))

app = Flask(__name__)
socketio = SocketIO(app)

K = 16
L = 100
N = 16

@socketio.on("connect")
def connect():
    print("client wants to connect")
    emit("status", { "message": "Connected. Hello!" })

@socketio.on('join')
def on_join(data):
    channels = pickle.load(open("channels.p", "rb"))
    users = pickle.load(open("users.p", "rb"))

    if data['channel'] in channels.keys():
        if channels[data['channel']].num_users == 2:
            emit("status", { "message": "Channel is full, connect to other channel" })
            disconnect(request.sid)
        else:
            users[request.sid] = data['channel']
            join_room(data['channel'])
            channels[data['channel']].num_users += 1
            channels[data['channel']].BSid = request.sid
            pickle.dump(channels, open("channels.p", "wb"))
            pickle.dump(users, open("users.p", "wb"))
            print('sid of B is ' + request.sid)
            emit("status",
                {
                "message": "Connected to channel as Bob, room is full",
                'assign Bob': 'B',
                'channel': data['channel'],
                'start' : 'yes',
                'ASid': channels[data['channel']].ASid,
                'BSid': channels[data['channel']].BSid
                },
                room = data['channel'],
            )

    else:
        users[request.sid] = data['channel']
        join_room(data['channel'])
        channels[data['channel']] = TPMSync(L, K, N)
        channels[data['channel']].num_users += 1
        channels[data['channel']].ASid = request.sid
        print('sid of A is ' + request.sid)
        pickle.dump(channels, open("channels.p", "wb"))
        pickle.dump(users, open("users.p", "wb"))
        emit("status",
            {
            "message": "Connected to channel as Alice",
            'assign Alice': 'A'
            }
        )


@socketio.on("disconnect")
def disconnecting():
    channels = pickle.load(open("channels.p", "rb"))
    users = pickle.load(open("users.p", "rb"))

    if request.sid in users.keys():
        channel = channels[users[request.sid]]

        if users[request.sid] in channels.keys():
            channels.pop(users[request.sid])
            print("Closed channel")
        if channel.ASid in users.keys():
            disconnect(channel.ASid)
            users.pop(channel.ASid)
        if channel.BSid in users.keys():
            disconnect(channel.BSid)
            users.pop(channel.BSid)

        pickle.dump(channels, open("channels.p", "wb"))
        pickle.dump(users, open("users.p", "wb"))


@socketio.on('my message')
def handle_message(data):
    print("Message from client" + data)

@socketio.on('weights')
def handle_message(data):
    msg = {
        'vector': data['vector'],
        'output': data['output']
        }
    emit('get_weights', msg, room = data['sid'])
    print("Received weights")

@socketio.on('send_output')
def handle_message(data):
    emit('output_received', data, room = data['sid'])
    print("Received output: " + str(data['output']))


@socketio.on('send_chaos_output')
def handle_message(data):
    emit('receive_chaos_output', data, room = data['sid'])
    print(" First Chaotic Map output: " + str(data['output']))

@socketio.on('confirm_chaos_output')
def handle_message(data):
    emit('receive_chaos_output2', data, room = data['sid'])
    print("Second Chaotic Map output: " + str(data['output']))


class TPMSync:

    def __init__(self, l_, k_, n_):
        self.num_users = 0.0
        self.ASid = None
        self.BSid = None

        self.L = l_
        self.K = k_
        self.N = n_


if __name__ == '__main__':
    socketio.run(app, debug=True)
