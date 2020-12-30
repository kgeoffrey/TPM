from flask import Flask, jsonify, request, abort
import numpy as np
import random
import string

app = Flask(__name__)

K = 16
L = 100
N = 16


def get_random_url():
    # Random string with the combination of lower and upper case
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(32))
    return result_str

keywords = {}
channels = {}


@app.route('/pair', methods=['POST'])
def create_channel():
    if not request.json or not 'keyword' in request.json:
        abort(400)

    if request.json['keyword'] in keywords.keys():
        if keywords[request.json['keyword']]["users"] == 2:
            # abort(400)
            return 500 #"channel is already full"
        else:
            keywords[request.json['keyword']]["users"] += 1
            return jsonify({
                'user': 'B',
                'url': keywords[request.json['keyword']]["url"]
                })

    else:
        keywords[request.json['keyword']] = {
            "users" : 1,
            "url" : get_random_url()
        }

        channels[keywords[request.json['keyword']]["url"]] = TPMSync(L, K, N)

        return jsonify({
            'user': 'A',
            'url': keywords[request.json['keyword']]["url"]
            })


@app.route("/weights/<url>", methods=['GET'])
def get_weights(url):
    channels[url].ready = False
    te = [x.tolist() for x in channels[url].vec]
    return jsonify({'random_vector': te}) #, 201


@app.route("/receive_output/<url>", methods=['POST'])
def receive_output(url):
    if not request.json or not 'output' in request.json:
        return 400

    if request.json['user'] == "A":
        channels[url].OutA = request.json['output']
        channels[url].UserAReady = True
        print("received")
    else:
        channels[url].OutB = request.json['output']
        channels[url].UserBReady = True
        print("received")

    if channels[url].UserAReady and channels[url].UserBReady:
        channels[url].ready = True

    if channels[url].ready:
        channels[url].UserAReady = False
        channels[url].UserBReady = False
        channels[url].update_vec()

    return "OK"


@app.route("/show_output/<url>", methods=['GET'])
def show_output(url):
    if channels[url].ready:
        return jsonify({
            'output' : {
                'A': channels[url].OutA,
                'B': channels[url].OutB
                }
            })
    else:
        return abort(400, 'My custom message') #'300'


@app.route("/check_sync/<url>", methods=['POST'])
def get_sync(url):
    if not request.json or not 'output' in request.json:
        return abort(400, 'My custom message')

    if request.json['user'] == "A":
        channels[url].chaosA = request.json['output']
    else:
        channels[url].chaosB = request.json['output']

    return 'received'


@app.route("/check_sync/<url>", methods=['GET'])
def show_sync(url):
    if channels[url].ready:
        return jsonify({
            'output' : {
                'A': channels[url].chaosA,
                'B': channels[url].chaosB
                }
            })
    else:
        return abort(400, 'My custom message')


if __name__ == '__main__':
    app.run(debug=True)





class TPMSync:

    def __init__(self, l_, k_, n_):
        self.num_users = 1
        self.OutA = None
        self.OutB = None
        self.UserAReady = False
        self.UserBReady = False
        self.url = "sdkafjhasdkfnv"
        self.ready = False

        self.chaosA = 0.0
        self.chaosB = 0.0

        self.L = l_
        self.K = k_
        self.N = n_

        self.vec = self.rand_vec()

    def rand_vec(self):
        p = []
        for i in range(self.K):
            p.append(np.random.randint(-self.L, self.L, size=self.N))
        return p

    def update_vec(self):
        p = []
        for i in range(self.K):
            p.append(np.random.randint(-self.L, self.L, size=self.N))
        self.vec = p
