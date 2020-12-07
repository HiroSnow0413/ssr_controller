
import sys, queue
import re
import time

from threading import Thread
import RPi.GPIO as GPIO

"""
    SSR制御クラス

    設定温度：target_temp
    出力ピン：pin_num
    温度取得キュー：tc_queue_dict

"""

MAX_PWM_WIDTH = 10

class SsrDriver(Thread):
    def __init__(self, group, tc_queue_dict, target_temp=20):
        Thread.__init__(self)
        self.ssr_pins = group["ssr_pins"]
        print(f"init SSR PIN({self.ssr_pins})")

        # 設定
        self.group = group
        self.target_temp = target_temp
        self.kp = 0.1
        self.tc_queue_dict = tc_queue_dict

        self.running = True     # 外部からスレッドを止める用フラグ

        self.d_temp = None      # 温度差（将来PID制御用）

        GPIO.setmode(GPIO.BCM)
        for pin_num in self.ssr_pins:
            GPIO.setup(pin_num, GPIO.OUT)
            time.sleep(0.1)
            GPIO.output(pin_num, False)
            time.sleep(0.1)


    def run(self):

        time.sleep(0.2)
        print(f"start SSR PIN({self.ssr_pins})")
  
        while self.running:

            try:
                list_tc_temp = []
                # キューが空になるまで取得
                while len(list_tc_temp) < 1:
                    # キューから温度を取得
                    for input_port in self.group["tc_index"]:
                        # print(self.tc_queue_dict[input_port[0]])
                        while not self.tc_queue_dict[input_port[0]][input_port[1]].empty():
                            list_tc_temp.append(float(self.tc_queue_dict[input_port[0]][input_port[1]].get()))
                    
                # キューに入っている温度の平均
                tc_temp_avg = sum(list_tc_temp) / len(list_tc_temp)

                print(f"SSR({self.pin_num}) Tc: {tc_temp:.2f}")
                pwm_width = self.get_pwm_width(self.target_temp, tc_temp_avg)
                self.set_pwm_width(pwm_width)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

            
        print(f"exit SSR: {self.ssr_pins}")

  
    def get_pwm_width(self, target_temp, tc_temp):
        """
            PWM幅の計算
            P制御：設定温度との温度差 * 0.1
            I制御：未実装
            D制御：未実装
        """

        if self.d_temp is None:
            self.d_temp = target_temp - tc_temp
        
        pwm_width = round( (target_temp - tc_temp) * self.kp )

        # print(f"pwm_width = {pwm_width} befor limit")
        # PWM幅を制限 MAX 10
        if pwm_width > MAX_PWM_WIDTH:
            pwm_width = MAX_PWM_WIDTH

        # 温度差（将来のPID制御用）
        self.d_temp = target_temp - tc_temp

        return pwm_width

    def set_pwm_width(self, pwm_width):
        """
            PWMの出力
            on_time: ON時間
            off_time: OFF時間
        """
        pwm_total_time = 1.0
        on_time = pwm_total_time * pwm_width / MAX_PWM_WIDTH
        off_time = pwm_total_time * (MAX_PWM_WIDTH - pwm_width) / MAX_PWM_WIDTH
        # print(f"on: {on_time}, off: {off_time}")
        for pin_num in self.ssr_pins:
            GPIO.output(pin_num, True)
        time.sleep(on_time)
        for pin_num in self.ssr_pins:
            GPIO.output(pin_num, False)
        time.sleep(off_time)

        print(f"SSR({self.pin_num}) pwm_width = {pwm_width}")

    def set_target_temp(self, target_temp):
        self.target_temp = target_temp

    def set_kp(self, kp):
        self.kp = kp

    def close(self):
        """
        外部からSSR制御のスレッド停止用
        """
        print(f"close SSR: {self.ssr_pins}")
        self.running = False

