import keyboard
import time
from ssr import Ssr
from temp_reader import TempReader
from threading import Event
import sys


def main():

    # stop_event = Event()
    # stop_event.clear()
    str_port_list = ["/dev/ttyUSB0",  "/dev/ttyUSB1",  "/dev/ttyUSB2"]
    temp_reader = [None, None, None]
    rate = 115200
    for i, str_port in enumerate(str_port_list):
        save_file = f"output_{i}.txt"
        temp_reader[i] = TempReader(str_port=str_port, rate=rate, save_file=save_file)
        # ssr[]
        temp_reader[i].start()
    time.sleep(10)

    # keyboard.wait("esc")
    # stop_event.set()
    # time.sleep(3)

    for i, str_port in enumerate(str_port_list):
        # temp_reader[i].join()
        print ('exiting at temp_reader.join')
        temp_reader[i].close()
        time.sleep(1)

    sys.exit()


if __name__ == "__main__":
    
    main()