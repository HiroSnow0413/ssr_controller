import keyboard
import time
from ssr import SsrController
from temp_reader import TempReader
from threading import Event
import sys
import queue

import RPi.GPIO as GPIO

"""
    メインスクリプト
    以下のスレッドを起動してSSRを制御する。

    温度取得：TempReader
    SSR制御：SsrController
    温度データ受け渡しキュー：q_tc_temp


"""
def main():
 
    # 温度用キュー（現在：全て同じキューを使用）
    q_tc_temp = queue.Queue()

    # 温度取得　起動処理
    str_port_list = ["/dev/ttyUSB0",  "/dev/ttyUSB1",  "/dev/ttyUSB2"]  # USBデバイス ポート
    rate = 115200   # 通信レート

    # スレッド起動
    list_temp_reader_threads = []
    for i, str_port in enumerate(str_port_list):
        save_file = f"output_{i}.txt"
        temp_reader = TempReader(str_port=str_port, rate=rate, save_file=save_file, q_tc_temp=q_tc_temp)
        temp_reader.start() # スレッドを起動
        list_temp_reader_threads.append(temp_reader)
    time.sleep(1)

    # SSR制御スレッド
    ssr_pins = [2, 3, 4, 9, 10, 11]     # SSR PWM output pins

    # スレッド起動
    list_ssr_threads = []
    for i, pin_num in enumerate(ssr_pins):
        ssr = SsrController(pin_num, q_tc_temp=q_tc_temp)
        ssr.start()
        list_ssr_threads.append(ssr)

    # ここから Ctrl-C が押されるまで無限ループ
    try:
        while True:
            time.sleep(1)

            # print(f"que_len: {q_tc_temp.qsize()}")
            pass
        
    except KeyboardInterrupt:
        # Ctrl-C
        print('interrupted!')

        # SSRスレッド終了処理 ※先に止める
        for i, ssr in enumerate(list_ssr_threads):
            # print (f"exiting at ssr.join({i})")
            ssr.close()
            time.sleep(0.1)

        time.sleep(1)

        # 温度取得スレッド終了処理
        for i, temp_reader in enumerate(list_temp_reader_threads):
            # print (f"exiting at temp_reader.join({i})")
            temp_reader.close()
            time.sleep(0.1)


        GPIO.cleanup()
        time.sleep(1)

        print("call exit!")
        exit()


if __name__ == "__main__":
    
    # setting.init()
    main()