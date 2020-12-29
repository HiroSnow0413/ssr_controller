
import sys, queue
import re
import time

from threading import Thread
import RPi.GPIO as GPIO

"""
    SSR制御クラス

    設定温度：target_temp
    出力ピン：pin_num
    温度取得キュー：tc_readers_dict

"""

MAX_PWM_WIDTH = 10

class SsrDriver(Thread):
    def __init__(self, target_pin, tc_readers_dict, target_temp=20):
        Thread.__init__(self)
        self.pin_num = target_pin["pin_num"]
        print(f"init SSR PIN({self.pin_num})")

        # 設定
        self.tc_index = target_pin["tc_index"]
        self.target_temp = target_temp
        self.kp = 0.1
        self.tc_readers_dict = tc_readers_dict

        self.running = True     # 外部からスレッドを止める用フラグ

        self.d_temp = None      # 温度差（将来PID制御用）

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_num, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(self.pin_num, False)
        time.sleep(0.1)


    def run(self):

        time.sleep(0.2)
        print(f"start SSR PIN({self.ssr_pin})")
  
        while self.running:

            try:
                list_tc_temp = []
                # キューから温度を取得
                for input_port in self.tc_index:
                    if self.tc_readers_dict[input_port[0]].get_tc_now(input_port[1]) is not None:
                        list_tc_temp.append(float(self.tc_readers_dict[input_port[0]].get_tc_now(input_port[1])))
                
                # キューに入っている温度の平均
                if len(list_tc_temp) > 0:
                    tc_temp_avg = sum(list_tc_temp) / len(list_tc_temp)
                else:
                    tc_temp_avg = 0

                print(f"SSR({self.pin_num}) Tc: {tc_temp:.2f}")
                pwm_width = self.get_pwm_width(self.target_temp, tc_temp_avg)
                self.set_pwm_width(pwm_width)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

            
        print(f"exit SSR: {self.ssr_pin}")

  
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
        # print(f"on: {on_time}, off: {off_time}"
        GPIO.output(self.ssr_pin, True)
        time.sleep(on_time)
        GPIO.output(self.pin_num, False)
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
        print(f"close SSR: {self.pin_num}")
        self.running = False

