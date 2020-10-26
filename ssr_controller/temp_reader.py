import serial, sys, queue
import re
import time
#from pylab import *
from threading import Event, Thread
import RPi.GPIO as GPIO

# import setting


class TempReader(Thread):
    def __init__(self, str_port, rate, q_tc_temp, save_file=None):
        Thread.__init__(self)
        self.q_tc_temp = q_tc_temp
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
        # line_byte = line_byte.decode(encoding='utf-8')
        # temperatures = line_byte.split(',')
        # print(f"[Debug] line_s = {temperatures}")
        # self.q_tc_temp.put(temperatures[2])
        # print(f"{self.str_port}, {q_tc_temp.qsize()}")
        #一回バッファークリアしないといけない？？？
        self.ser.reset_input_buffer
        
        # regex = re.compile('\d+')
        self.fw = open(save_file, "w+")

        time.sleep(0.2)

    def run(self):

        event = Event()
        event.set()

        time.sleep(3)
        while self.running:
            try:
                buff_waiting = self.ser.in_waiting

                # print(f"buff_waiting: {buff_waiting}")
                if buff_waiting > 0:
                    line_byte = self.ser.readline()
                    line_byte = line_byte.decode(encoding='utf-8')
                    temperatures=line_byte.split(',')
                    self.fw.write(",".join(temperatures))
                    # print(f"line_s = {temperatures}")
                    self.q_tc_temp.put(temperatures[2])
                    # print(f"{self.str_port}, {self.q_tc_temp.qsize()}")
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
        print(f"close usb: {self.str_port}")
        self.running = False

