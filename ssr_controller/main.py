import keyboard

import ssr
import temp_reader


def main():

    temp_reader = TempReader()
    # ssr[]
    temp_reader.start()
    time.sleep(3)

    keyboard.wait("esc")

    temp_reader.join()
    print ('exiting at temp_reader.join')
    temp_reader.close()


if __name__ == "__main__":
    
    main()