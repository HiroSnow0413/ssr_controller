
import sys, queue
import re
import time

from threading import Thread
import RPi.GPIO as GPIO

"""
    SSR制御クラス

    設定温度：target_temp
    出力ピン：pin_num
    温度取得キュー：q_tc_temp

"""

MAX_PWM_WIDTH = 10

class SsrController(Thread):
    def __init__(self, pin_num, q_tc_temp, target_temp=200):
        Thread.__init__(self)
        print(f"init SSR PIN({pin_num})")

        # 設定
        self.target_temp = target_temp
        self.q_tc_temp = q_tc_temp
        self.pin_num = pin_num

        self.running = True     # 外部からスレッドを止める用フラグ

        self.d_temp = None      # 温度差（将来PID制御用）

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(self.pin_num, False)

    def run(self):

        time.sleep(0.2)
        print(f"start SSR PIN({self.pin_num})")
  
        while self.running:

            try:
                list_tc_temp = []
                # キューが空になるまで取得
                while not self.q_tc_temp.empty():
                    list_tc_temp.append(float(self.q_tc_temp.get()))
                # キューから温度を取得
                if len(list_tc_temp) > 0:
                    
                    # キューに入っている温度の平均
                    tc_temp = sum(list_tc_temp) / len(list_tc_temp)

                    print(f"SSR({self.pin_num}) Tc: {tc_temp:.2f}")
                    pwm_width = self.get_pwm_width(self.target_temp, tc_temp)
                    self.set_pwm_width(pwm_width)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

  
    def get_pwm_width(self, target_temp, tc_temp):
        """
            PWM幅の計算
            設定温度との温度差 * 0.1

        """

        if self.d_temp is None:
            self.d_temp = target_temp - tc_temp
        
        pwm_width = round( (target_temp - tc_temp) / 10 )

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
        GPIO.output(self.pin_num, True)
        time.sleep(on_time)
        GPIO.output(self.pin_num, False)
        time.sleep(off_time)

        print(f"SSR({self.pin_num}) pwm_width = {pwm_width}")


    def close(self):
        """
        外部からSSR制御のスレッド停止用
        """

        print(f"close SSR: {self.pin_num}")
        self.running = False

