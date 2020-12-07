import time
from ssr import SsrDriver
from temp_reader import TempReader
from threading import Event
import sys
import queue
import json
import RPi.GPIO as GPIO

"""
    メインスクリプト
    以下のスレッドを起動してSSRを制御する。

    温度取得：TempReader
    SSR制御：SsrDriver
    温度データ受け渡しキュー：q_tc_temp


"""
def main():
 
    with open("./config.json", mode="r") as fr:
        config = json.load(fr)

    print(config)

    rate = 115200   # 通信レート

    # 温度用キュー（現在：全て同じキューを使用）
    q_maxsize = 200
    tc_queue_dict = {}
    tc_readers_dict = {}
    for str_port in config["Tc"].keys():
        print(str_port)
        tc_queue_dict[str_port] = {}
        for idx in config["Tc"][str_port]["index"]:
            tc_queue_dict[str_port][idx] = queue.Queue(maxsize=q_maxsize)
        
        save_file = f"output_{str_port[-4]}.txt"
        tc_readers_dict[str_port] = TempReader(str_port=str_port, rate=rate, save_file=save_file, tc_queue_dict=tc_queue_dict)
        tc_readers_dict[str_port].start() # スレッドを起動
        time.sleep(1)

    # SSR制御スレッド
    # スレッド起動
    ssr_group_dict = {}
    for i, group in enumerate(config["SSR"]):
        ssr_group_dict[i] = SsrDriver(group, tc_queue_dict=tc_queue_dict)
        ssr_group_dict[i].start()

    # ここから Ctrl-C が押されるまで無限ループ
    try:
        while True:
            # ここに処理を記載
            time.sleep(1)
            # 例
            ssr_group_dict[0].set_target_temp(200)
            ssr_group_dict[1].set_target_temp(200)
            # print(f"que_len: {q_tc_temp.qsize()}")
            pass
        
    except KeyboardInterrupt:
        # Ctrl-C
        print('interrupted!')

        # SSRスレッド終了処理 ※先に止める
        for i, ssr in enumerate(ssr_group_dict.keys()):
            # print (f"exiting at ssr.join({i})")
            ssr_group_dict[ssr].close()
            time.sleep(0.1)

        time.sleep(1)

        # 温度取得スレッド終了処理
        for i, str_port in enumerate(tc_readers_dict.keys()):
            # print (f"exiting at temp_reader.join({i})")
            tc_readers_dict[str_port].close()
            time.sleep(0.1)


        GPIO.cleanup()
        time.sleep(1)

        print("call exit!")
        exit()


if __name__ == "__main__":
    
    # setting.init()
    main()
