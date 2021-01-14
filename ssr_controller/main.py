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
    """
    （以下、変数の中身の例）
    str.port= /dev/ttyUSB0
    tc_readers_dictというスレッドの立ち上がり:
    tc_readers_dict （スレッド）==  {'/dev/ttyUSB0': <TempReader(Thread-1, started 1985582176)>}
    """
    q_maxlen = 20
    tc_readers_dict = {}
    for str_port in config["Tc"].keys():
        print("tc_reader USB port=", str_port)
        tc_index = config["Tc"][str_port]["index"]	# ジェイソン使って順番を指定してもらう。Kメモ{210103}
        
        save_file = f"output_{str_port[-1]}.txt"
        tc_readers_dict[str_port] = TempReader(
            str_port=str_port, 
            rate=rate, 
            tc_index=tc_index, 
            q_maxlen=q_maxlen, 
            save_file=save_file
        )									# とにかく、順番に、温度を読んでくる。Kメモ{210103}
        tc_readers_dict[str_port].start() # スレッドを起動
        time.sleep(1)
    print("tc_readers_dictというスレッドの立ち上がり")   #Kinoshita{210102}
    print("str.port=", str_port)   #Kinoshita{210102}
    print("jsonからの情報の持ち込み方を見たい：")   #Kinoshita{210102}
    print("tc_readers_dict （スレッド）== ",tc_readers_dict)  #Kinoshita{210102}

    # SSR制御スレッド
    # スレッド起動
    """
    SSR のスレッドは以下のように立ち上がる：
    ssr_group_dict= {
    0: <SsrDriver(Thread-2, started 1975514208)>, 
    1: <SsrDriver(Thread-3, started 1965028448)>, 
    2: <SsrDriver(Thread-4, started 1954542688)>, 
    3: <SsrDriver(Thread-5, started 1944056928)>}
    """
    ssr_group_dict = {}
    # SSRの各々で現時点では、{210104} ループしている
    # confis.jsonで指定した、Groupでの ループにする方向ではないかとおもう。
    for i, target_pin in enumerate(config["SSR"]):   #ここでGroup別にイテレーションLoopに。{201212}
        ssr_group_dict[i] = SsrDriver(
            target_pin,
            tc_readers_dict=tc_readers_dict
        )
        ssr_group_dict[i].start()    #ここで起動１

    print("SsrDriverへの情報伝達を見たい：")   #Kinoshita{210103}
    print("ssr_group_dict （スレッド）==",ssr_group_dict)  #Kinoshita{210103}
    print()
    print("ssr_group_dict.keys()=",ssr_group_dict.keys()) #Kinoshita{210103}

    # ここから Ctrl-C が押されるまで無限ループ
    try:
        while True:
            # ここに処理を記載
            time.sleep(1)
            # 例
            """
            支配層と被支配層とに分けて「ロジック」（やりたいこと）を書き込むのではなくて
            やりたいことを表現する場を、上手に、被支配層と支配層とを突き抜けて、用意する方法を
            うまくつくっていく。そういう技法を身に着けなければいけない。
            複雑なことを、どう整理するか、
            UML 図　を描いてみようと思います。 Kコメント{210103}
            """
            #目標温度をGroup別に。現時点 {210104} では SSRに一対一対応している。
            ssr_group_dict[0].set_target_temp(40)   
            ssr_group_dict[1].set_target_temp(40)
            ssr_group_dict[2].set_target_temp(40)
            ssr_group_dict[3].set_target_temp(40)
            # print(f"que_len: {q_tc_temp.qsize()}")
            pass
        
    except KeyboardInterrupt:
        # Ctrl-C
        print('interrupted!')

        # SSRスレッド終了処理 ※先に止める
        for i, ssr in enumerate(ssr_group_dict.keys()): #現時点では、SSRのここに対応している。
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
