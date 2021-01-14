import sys, queue
import os
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
#target temperature ==> look at main.py, set_target_temp
room_temp= 0.0       #degree_C temperature
kp = 0.1
pwm_total_time = 0.1  # Is is very fast time-constant at NiCr wire heating 
MAX_PWM_WIDTH  = pwm_total_time

Debug1=True
Debug2=False
Debug3=True

class SsrDriver(Thread):
    def __init__(self, target_pin, tc_readers_dict, target_temp=20): #target_temp=20 for default
        Thread.__init__(self)
        self.pin_num = target_pin["pin_num"]  # config.jsonでの SSR pin番号
        print(f"init SSR PIN({self.pin_num})")

        # 設定
        self.tc_index = target_pin["tc_index"]   # config.jsonでのSSRと組になっている熱電対の番号
        self.target_temp = target_temp
        self.kp = kp
        """
        Kメモ{210103}
        ここ（def __init__ ）はあくまで、デフォルトのパラメータを決めていると言う位置づけで
        本当に制限をやっているのは、あるいはやるべきなのは、現場に1番近いところ。
        したがって、デフォルトのパラメータを、現場のプログラムに渡してあげると言う立ち位置になる。
        現場が無茶をやっても、ここで安全性を見てあげると言うような立場なのかもしれない。
        （試行錯誤でプログラムの構造を考えてみる。）
        """
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
        print(f"start SSR PIN({self.pin_num})")  
  
        while self.running:

            try:
                """
                このプログラム1が1番、コントロールの現場に近いところで、本来あらゆる温度の情報とSSRの操作ができる
                作業フィールドになっているべき。今そうなっているかどうか、よくわからないけど。。。。。
                self.tc_readers_dict[input_port[0]].get_tc_now(input_port[1])　
                """
                list_tc_temp = []
                # キューから温度を取得
                """
                K210104, ジェイソンの使い方、ジェイソンからデータとってくるところをきれいにわかるようにしないといけない
                （変数の説明）：
                 input_port= config.json の終端 
                            ['/dev/ttyUSB0', 2]　＝［Tc収録機のUARTの番号、「熱電対Tcの番号（文字列の位置）」］
                            input_port[1]は「熱電対Tcの番号」
                 get_tc_now = temperatures[idx] 最新値、吉澤さんのTc収録機から読み込んだcsv形式をばらしたもの
                 tc_readers_dict
                            この名前でスレッド（TempReaderを呼び出してTc収録機のデー打を受け取る）を立ち上げたもの。
                """
                
                if Debug1: print("debug in ssr, self.tc_index=",self.tc_index)
                for input_port in self.tc_index:
                    #print("___debug_input_port=",input_port) ###################
                    if self.tc_readers_dict[input_port[0]].get_tc_now(input_port[1]) is not None:
                        #print("debug_input_port=",input_port) ###################
                        list_tc_temp.append(
                          self.tc_readers_dict[input_port[0]].get_tc_now(input_port[1])
                          ) 
                # （config.jsonで書いてあるグループ化してある熱電対の）温度の平均
                # ここで Group化を図っている
                if Debug1: print("debug in ssr, list_tc_temp",list_tc_temp)
                if len(list_tc_temp) > 0:
                    tc_temp_avg = sum(list_tc_temp) / len(list_tc_temp)
                else:
                    tc_temp_avg = room_temp #default for safety
                
                """
                
                """
                if Debug1: print(f"@@@ debug in ssr, SSR({self.pin_num}) Tc: {tc_temp_avg:.2f}")
                pwm_width_s = self.get_pwm_width(self.target_temp, tc_temp_avg)
                self.set_pwm_width(pwm_width_s)
                # time.sleep(1)
            except KeyboardInterrupt:
                print (f'exiting thread-1 in temp_read({self.pin_num})')
                self.close()

            
        print(f"exit SSR: {self.pin_num}")

  
    def get_pwm_width(self, target_temp, tc_temp):
        """
            PWM幅の計算
            P制御：設定温度との温度差 * 0.1
            I制御：未実装
            D制御：未実装
        """
        
        """
        時刻の増加のシーケンスで、dt を計算するときは
        59.8, 59.9, 60.0,  0.1, 数字が下がったら、60を加えて、
                          60.1 として引き算する,
                          
        """
        if self.d_temp is None:
            self.d_temp = target_temp - tc_temp
            
        if Debug3: print("ccccccccccc  SSR, self.pin_num=",self.pin_num)
        
        dtemp_t=dtemp_total=target_temp-room_temp
        target_temp_s=target_temp_scaled =(
                      target_temp-room_temp)/dtemp_t
        tc_temp_s    =tc_temp_scaled     =(
                      tc_temp-room_temp)/dtemp_t
        ########
        if Debug1: print("~~~ debug in ssr, tc_temp_s=",tc_temp_s)
        if Debug1: print("                  tc_temp, target_temp, room_temp=",tc_temp, target_temp, room_temp)
       

        # BEGIN　 SSR(n)の制御ロジック
        """
        {210111}
        さあ、考えよう。
        JSON（上流側の概要としての指示）に書ききれない、現場での、こまかいロジックを、ここで実装する。
        あたらしい、ロジックが、ここで発見される、
        あたらしい、アイディアが、ここで生まれる。
        """ 
        self.d_temp_s=self.d_temp_scaled =(
                      self.d_temp)/dtemp_t
        
        pwm_width_s = pwm_width_scaled = (
                      target_temp_s-tc_temp_s)*self.kp
        # END SSR(n)の制御ロジック



        # PWM幅を制限
        if pwm_width_s > 1.0:
            pwm_width_s = 1.0
            pwm_width_s = pwm_width_s_min = 0.1 #OBS OBS maximum pwm_width to be safe {210109}


        # 温度差（将来のPID制御用）
        self.d_temp = target_temp - tc_temp

        return pwm_width_s

    def set_pwm_width(self, pwm_width_s):
        """
            PWMの出力
            on_time: ON時間
            off_time: OFF時間
        """
#        pwm_width_s=pwm_width_scaled=pwm_width / MAX_PWM_WIDTH
        pwm_width_s=pwm_width_scaled=pwm_width_s
        
        on_time  = pwm_total_time * pwm_width_s
        off_time = pwm_total_time * (1-pwm_width_s)
        if Debug1: print("+++ debug in ssr of set_pwm_width",f"on: {on_time/pwm_total_time}, off: {off_time/pwm_total_time}")
        GPIO.output(self.pin_num, True)
        time.sleep(on_time)
        GPIO.output(self.pin_num, False)
        time.sleep(off_time)

        if Debug1: print("debug in ssr,", f"SSR({self.pin_num}) pwm_width_s = {pwm_width_s}")

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

