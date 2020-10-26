import serial, sys, queue
import re
import time
#from pylab import *
from threading import Event, Thread
import RPi.GPIO as GPIO


class TempReader(Thread):
    def __init__(self, str_port, rate, save_file=None):
        Thread.__init__(self)

        self.running = True
        self.str_port = str_port
        self.rate = rate

        self.ser = serial.Serial(str_port, rate, timeout = 0) #20200627 115200->19200
        self.ser.send_break()
        self.ser.reset_input_buffer
        self.ser.reset_input_buffer
        self.ser.reset_input_buffer
        self.ser.reset_input_buffer
        line_byte = self.ser.readline()  #一回、読み飛ばしをかける
        #一回バッファークリアしないといけない？？？
        self.ser.reset_input_buffer

        
        regex = re.compile('\d+')  # for extracting number from strings
        self.fw = open(save_file, "w+")
        y = [0]*100
        data = []
        itime = 0

        time.sleep(0.2)

    def run(self):

        event = Event()
        event.set()

        time.sleep(3)

        while self.running:
            try:
                buff_waiting = self.ser.in_waiting
                if buff_waiting > 0:
                    line_byte = self.ser.readline()
                    line_byte = line_byte.decode(encoding='utf-8')
                    temperatures=line_byte.split(',')
                    self.fw.write(",".join(temperatures))
                    print(f"{self.running}, line_s = {temperatures}") 
                    """
                    T_measは、Tc-1なので、これをPIDの計測値としてPID制御をする。
                    tempertures[2]
                    """
                    # q.put(line_byte)
                    # if False :
                    #     print(buff_waiting, q.qsize(), line_byte)
                    event.wait()
            except KeyboardInterrupt:
                print ('exiting thread-1 in port_read')
                self.ser.close()
                self.fw.close()
                sys.exit()
        
        self.ser.close()
        self.fw.close()
    
    def close(self):
        self.running = False

