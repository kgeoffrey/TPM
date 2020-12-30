import time
import numpy as np
import math
import sys
import requests


class tpm_test:

    def __init__(self):
        self.user = None
        self.url = 'https://tpmserver.herokuapp.com' #"http://127.0.0.1:5000"
        self.secret = None
        self.tpm = TPM(16, 16, 100)
        self.n = 200
        self.IsSync = False

    def synchronize(self):

        for i in range(self.n):
            time.sleep(0.2)
            self.update_weights()
            time.sleep(0.2)
            self.send_output()
            time.sleep(0.2)
            self.get_output()
            time.sleep(0.2)
            self.check_sync()

            if self.IsSync:
                print('Machines synced!')

    def pair(self, keyword):
        obj = {"keyword" : keyword}

        response = self.checkResponse(requests.post, self.url + "/pair", obj, 100)
        response = response.json()

        self.secret = response["url"]
        self.user = response["user"]
        #return response

    def update_weights(self):

        #response = requests.get(self.url + '/weights/' + self.secret)

        response = self.checkResponse(requests.get, self.url + '/weights/' + self.secret, None, 100)
        json = response.json()

        vec = [np.array(x) for x in json['random_vector']]
        self.tpm.get_output(vec)

        return response


    def send_output(self):
        obj = {
            'output': self.tpm.out,
            'user': self.user
            }

        response = self.checkResponse(requests.post, self.url + '/receive_output/' + self.secret, obj, 100)


    def get_output(self):
        #url = "http://127.0.0.1:5000/show_output/" + secret
        response = self.checkResponse(requests.get, self.url + '/show_output/' + self.secret, None, 500)
        #response = requests.get(self.url + '/show_output/' + self.secret)
        json_ = response.json()
        print(json_)
        if json_['output']['A'] == json_['output']['B']:
            print('updating weights!')
            self.tpm.update_weigths(json_['output']['A'])

        return response# .json()

    def check_sync(self):
        obj = {
            'output' : self.tpm.chaosmap(),
            'user' : self.user
        }

        response = self.checkResponse(requests.post, self.url + '/check_sync/' + self.secret, obj, 200)
        response = self.checkResponse(requests.get, self.url + '/check_sync/' + self.secret, None, 200)

        json_ = response.json()
        if json_['output']['A'] == json_['output']['B']:
            print('comparing weights')
            print(json_)
            self.IsSync = True


    def checkResponse(self, request_, url_, obj_, time_):
        timer = 0
        status = None # request_(url_, json =  obj_)

        while status != 200:
            time.sleep(0.1)
            timer += 1
            response = request_(url_, json = obj_)
            status = response.status_code
            if timer > time_:
                print('request timed out')
                break
            if response.status_code == 200:
                print('request reached')
                #break
                return response



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

    def update_weigths(self, outputB):
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
        rr = sum(abs(x) for x in (list(np.hstack(self.weights))))
        t = abs(r) / rr
        x = t
        for i in range(rr):
            x = (3.6 + t/2)* x *(1 - x)
        return x



if __name__ == "__main__":
    instance = tpm_test()
    instance.pair(sys.argv[1])
    instance.synchronize()
