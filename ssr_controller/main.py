import keyboard
import time
from ssr import SsrController
from temp_reader import TempReader
from threading import Event
import sys
import queue

import RPi.GPIO as GPIO


def main():
 
    q_tc_temp = queue.Queue()
    # stop_event = Event()
    # stop_event.clear()
    str_port_list = ["/dev/ttyUSB0",  "/dev/ttyUSB1",  "/dev/ttyUSB2"]
    list_temp_reader = []
    rate = 115200
    for i, str_port in enumerate(str_port_list):
        save_file = f"output_{i}.txt"
        temp_reader = TempReader(str_port=str_port, rate=rate, save_file=save_file, q_tc_temp=q_tc_temp)
        temp_reader.start()
        list_temp_reader.append(temp_reader)
    time.sleep(1)

    ssr_pins = [2, 3, 4, 9, 10, 11]
    list_ssr = []
    for i, pin_num in enumerate(ssr_pins):
        ssr = SsrController(pin_num, q_tc_temp=q_tc_temp)
        ssr.start()
        list_ssr.append(ssr)

    try:
        while True:
            time.sleep(1)

            # print(f"que_len: {q_tc_temp.qsize()}")
            pass
    except KeyboardInterrupt:
        # Ctrl-C
        print('interrupted!')

        # SSR を先に止める
        for i, ssr in enumerate(list_ssr):
            # print (f"exiting at ssr.join({i})")
            ssr.close()
            time.sleep(0.1)

        for i, temp_reader in enumerate(list_temp_reader):
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