import threading

class Ssr(threading.Thread):
    def __init__(pin_num):
        threading.Thread.__init__(self)


        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
