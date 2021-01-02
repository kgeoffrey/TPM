# from socketIO_client import SocketIO, LoggingNamespace
import sys
import socketio
import numpy as np
import math
from random import randrange


sio = socketio.Client()


@sio.on('receive_chaos_output2')
def on_message(msg):
    if msg['output'] == tpmclient.tpm.chaosmap():
        tpmclient.IsSync = True
        print('SUCCESSFULLY synched with Bob')
        sio.disconnect()
        tpmclient.save_key()

        # save key to KEYS

@sio.on('receive_chaos_output')
def on_message(msg):
    sio.emit('confirm_chaos_output',
        {
            'msg':'sending chaos output',
            'output': tpmclient.tpm.chaosmap(),
            'sid': tpmclient.partner_sid
        }
    )

    if msg['output'] == tpmclient.tpm.chaosmap():
        tpmclient.IsSync = True
        print('SUCCESSFULLY synched with Alice')
        sio.disconnect()
        tpmclient.save_key()

        # save key to KEYS


@sio.on('output_received')
def on_message(msg):
    if tpmclient.tpm.out == msg['output']:
        tpmclient.tpm.update_weights(msg['output'])

    if tpmclient.n >= 200:
        if tpmclient.n  % 10 == 0:
            tpmclient.send_chaos_output()

    if not tpmclient.IsSync:
        tpmclient.send_vector_and_output()
        # print("output received", + msg['output'])
        animation.update()

@sio.on('get_weights')
def on_message(msg):
    try:
        vector = msg['vector']
        list_vec = [np.array(vector[x:x+16]) for x in range(0, len(vector), 16)]
        tpmclient.receive_vector(list_vec)
        tpmclient.send_output()
        if tpmclient.tpm.out == msg['output']:
            tpmclient.tpm.update_weights(msg['output'])
        # print("output received", + msg['output'])
        animation.update()
    except socketio.exceptions.BadNamespaceError:
        pass

@sio.on('status')
def on_message(msg):
    if 'assign Alice' in msg:
        tpmclient.user = msg['assign Alice']
    if 'assign Bob' in msg and not tpmclient.user:
        tpmclient.user = msg['assign Bob']
    if 'start' in msg:
        if tpmclient.user == 'A':
            tpmclient.partner_sid = msg["BSid"]
            print(' B sid is ' + tpmclient.partner_sid)
            tpmclient.send_vector_and_output()
        else:
            tpmclient.partner_sid = msg["ASid"]
            print(' A sid is ' + tpmclient.partner_sid)

        print('My partners sid is: ' + tpmclient.partner_sid)

    print('message from server: ' + msg['message'])

@sio.event
def connect():
    sio.emit('my message', " FU", namespace='/')
    sio.emit('join', {'channel': CHANNEL}, namespace='/')
    print("connected to server!")


class TPMClient:
    def __init__(self):
        self.user = None
        self.tpm = TPM(16, 16, 100)
        self.n = 0
        self.IsSync = False

    def send_vector_and_output(self):
        vector = self.rand_vec()
        list_vec = [np.array(vector[x:x+16]) for x in range(0, len(vector), 16)]
        self.tpm.get_output(list_vec)

        sio.emit('weights',
            {
                'msg':'sending random vector and output',
                'vector': vector,
                'output': self.tpm.out,
                'sid': tpmclient.partner_sid
            }
        )
        self.n += 1

    def receive_vector(self, vector_):
        vec = [np.array(x) for x in vector_]
        self.tpm.get_output(vec)

    def rand_vec(self):
        l = []
        for i in range(256):
            l.append(randrange(-100, 100))
        return l

    def send_output(self):
        sio.emit('send_output',
            {
                'msg':'sending output',
                'output': self.tpm.out,
                'sid': tpmclient.partner_sid
            }
        )

    def send_chaos_output(self):
        sio.emit('send_chaos_output',
            {
                'msg':'sending chaos output',
                'output': self.tpm.chaosmap(),
                'sid': tpmclient.partner_sid
            }
        )

    def save_key(self):
        re = [abs(item+155) for sublist in self.tpm.weights for item in sublist]
        key = bytes(abs(x) for x in re).decode('cp437')
        with open("KEYS/{}.txt".format(CHANNEL), "w") as text_file:
            print(key, file=text_file)


class TPM:
    def __init__(self, k_, n_, l_):
        self.k = k_
        self.n = n_
        self.l = l_
        self.weights = self.initialize_w()
        self.inputs = None
        self.H = np.zeros(self.k)
        self.out = None
        self.X = None

    def get_output(self, input_):
        self.X = input_
        self.out = 1

        for i in range(self.k):
            self.H[i] = self.signum(np.dot(input_[i], self.weights[i]))
            self.out *= self.signum(np.dot(input_[i], self.weights[i]))

    def initialize_w(self):
        p = []
        for i in range(self.k):
            p.append(np.random.randint(-self.l, self.l, size=self.n))
        return p

    def signum(self, x):
        return math.copysign(1, x)

    def update_weights(self, outputB):
        for i in range(self.k):
            for j in range(self.n):
                self.weights[i][j] += self.X[i][j] * self.out * self.isequal(self.out, self.H[i]) * self.isequal(self.out, outputB)
                self.weights[i][j] = self.g(self.weights[i][j])

    def isequal(self, A, B):
        if A==B:
            return 1.0
        else:
            return 0.0

    def g(self, w):
        if w > self.l:
            return self.l
        if w < -self.l:
            return -self.l
        else:
            return w

    def chaosmap(self):
        r = sum(list(np.hstack(self.weights)))

        rr = sum([abs(x) for x in (list(np.hstack(self.weights)))])

        t = float(abs(r)) / float(rr)
        x = t
        for i in range(rr):
            x = (3.6 + t/2)* x *(1 - x)
        return x


class Animation:
    def __init__(self):
        self.animation = [
                        "[        ]",
                        "[=       ]",
                        "[===     ]",
                        "[====    ]",
                        "[=====   ]",
                        "[======  ]",
                        "[======= ]",
                        "[========]",
                        "[ =======]",
                        "[  ======]",
                        "[   =====]",
                        "[    ====]",
                        "[     ===]",
                        "[      ==]",
                        "[       =]",
                        "[        ]",
                        "[        ]"]
        self.i = 0
        self.timer = None

    def update(self):
        print(self.animation[self.i % len(self.animation)], end='\r')
        self.i += 1

if __name__ == "__main__":
    CHANNEL = sys.argv[1]
    tpmclient = TPMClient()
    animation = Animation()
    sio.connect('https://tpmserver.herokuapp.com/')
    # sio.connect('http://localhost:5000')
