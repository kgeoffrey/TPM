import threading

class loading_animation:
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

    def start_animation(self):
        self.timer = threading.Timer(0.1, self.update)
        self.timer.start()

if __name__ == "__main__":
    animation = loading_animation()
    animation.start_animation()
    #sio.connect('http://localhost:5000')
