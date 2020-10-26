
import sys, queue
import re
import time

from threading import Thread
import RPi.GPIO as GPIO


class SsrController(Thread):
    def __init__(self, pin_num, q_tc_temp):
        Thread.__init__(self)
        print(f"init SSR PIN({pin_num})")

        self.q_tc_temp = q_tc_temp
        self.running = True
        self.pin_num = pin_num
        self.d_temp = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
        time.sleep(0.1)
        GPIO.output(self.pin_num, False)

    def run(self):

        time.sleep(0.2)
        print(f"start SSR PIN({self.pin_num})")
   
        target_temp = 200
  
        while self.running:
            try:
                list_tc_temp = []
                while not self.q_tc_temp.empty():
                    list_tc_temp.append(float(self.q_tc_temp.get()))
                if len(list_tc_temp) > 0:
                    tc_temp = sum(list_tc_temp) / len(list_tc_temp)
                    print(f"SSR({self.pin_num}) Tc: {tc_temp:.2f}")
                    pwm_width = self.get_pwm_width(target_temp, tc_temp)
                    self.set_pwm_width(pwm_width)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

  
    def get_pwm_width(self, target_temp, tc_temp):

        if self.d_temp is None:
            self.d_temp = target_temp - tc_temp
        
        pwm_width = round( (target_temp - tc_temp) / 10 )

        # print(f"pwm_width = {pwm_width} befor limit")
        if pwm_width > 10:
            pwm_width = 10

        self.d_temp = target_temp - tc_temp

        return pwm_width

    def set_pwm_width(self, pwm_width):
        
        pwm_total_time = 1.0
        on_time = pwm_total_time * pwm_width / 10
        off_time = pwm_total_time * (10 - pwm_width) / 10
        # print(f"on: {on_time}, off: {off_time}")
        GPIO.output(self.pin_num, True)
        time.sleep(on_time)
        GPIO.output(self.pin_num, False)
        time.sleep(off_time)

        print(f"SSR({self.pin_num}) pwm_width = {pwm_width}")


    def close(self):
        print(f"close SSR: {self.pin_num}")
        self.running = False

