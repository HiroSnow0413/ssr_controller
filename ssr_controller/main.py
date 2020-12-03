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
    for str_port in config["Tc"].keys():
        print(str_port)
        tc_queue_dict[str_port] = {}
        for idx in config["Tc"][str_port]["index"]:
            tc_queue_dict[str_port][idx] = queue.Queue(maxsize=q_maxsize)
        
        save_file = f"output_{str_port[-4]}.txt"
        conig["Tc"][str_port]["reader"] = TempReader(str_port=str_port, rate=rate, save_file=save_file, tc_queue_dict=tc_queue_dict)
        conig["Tc"][str_port]["reader"].start() # スレッドを起動
        time.sleep(1)

    # SSR制御スレッド
    # スレッド起動
    for i, group in enumerate(config["SSR"]):
        config["SSR"][i]["driver"] = SsrDriver(group, tc_queue_dict=tc_queue_dict)
        config["SSR"][i]["driver"].start()

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
        for i, ssr in enumerate(config["SSR"]):
            # print (f"exiting at ssr.join({i})")
            config["SSR"][i]["driver"].close()
            time.sleep(0.1)

        time.sleep(1)

        # 温度取得スレッド終了処理
        for i, str_port in enumerate(config["Tc"].keys()):
            # print (f"exiting at temp_reader.join({i})")
            config["Tc"][str_port]["reader"].close()
            time.sleep(0.1)


        GPIO.cleanup()
        time.sleep(1)

        print("call exit!")
        exit()


if __name__ == "__main__":
    
    # setting.init()
    main()
