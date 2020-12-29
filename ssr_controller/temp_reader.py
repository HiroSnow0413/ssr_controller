import serial, sys, queue
from collections import deque
import re
import time
from threading import Event, Thread
import RPi.GPIO as GPIO
# import setting

"""
    USBから温度取得用スレッド
"""

class TempReader(Thread):
    def __init__(self, str_port, rate, tc_index, q_maxlen, save_file=None):
        Thread.__init__(self)

        # 温度用のキュー
        self.tc_index = tc_index
        self.q_maxlen = q_maxlen
        self.tc_queue_dict = {}
        self.tc_now = {}
        for idx in tc_index:
            self.tc_queue_dict[idx] = deque(maxlen=q_maxlen)
            self.tc_now[idx] = None

        # 外部からスレッド停止用
        self.running = True

        # シリアルポート設定
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
        # self.tc_queue_dict.put(temperatures[2])
        # print(f"{self.str_port}, {tc_queue_dict.qsize()}")
        #一回バッファークリアしないといけない？？？
        self.ser.reset_input_buffer
        
        # ログファイル
        self.fw = open(save_file, "w+")

        time.sleep(0.2)

    def run(self):

        event = Event()
        event.set()

        time.sleep(3)
        while self.running:
            buff_waiting = self.ser.in_waiting

            # print(f"buff_waiting: {buff_waiting}")
            # バッファーにデータ有
            if buff_waiting > 0:
                line_byte = self.ser.readline()
                line_byte = line_byte.decode(encoding='utf-8')
                temperatures=line_byte.split(',')
                self.fw.write(",".join(temperatures))   # ファイルへ保存
                # print(f"line_s = {temperatures}")

                # キューに温度をいれる（SSR制御で使用）
                print(f"{self.str_port}: {temperatures}")
                for idx in self.tc_index:
                    # if idx == 1:
                    #     print(temperatures[idx])
                    self.tc_queue_dict[idx].append(temperatures[idx])
                    self.tc_now = temperatures[idx]
                # print(f"{self.str_port}, {self.tc_queue_dict.qsize()}")
                """
                T_measは、Tc-1なので、これをPIDの計測値としてPID制御をする。
                tempertures[2]
                """
                # q.put(line_byte)
                # if False :
                # print(buff_waiting, q.qsize(), line_byte)
            event.wait()
        # 終了処理
        self.ser.close()
        self.fw.close()
        print(f"exit usb: {self.str_port}")

    def close(self):
        """
        外部からスレッド停止用メソッド
        """
        print(f"close usb: {self.str_port}")
        self.running = False

    def get_tc_now(self, idx):

        return self.tc_now[idx]

    def get_tc_average(self, idx):

        total = 0
        for tc_hist in self.tc_queue_dict[idx]:
            total += tc_hist

        return total / self.q_maxlen