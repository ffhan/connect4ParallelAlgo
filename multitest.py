import threading
import time


def f1():
    time.sleep(5)
    print('F1 DONE')


if __name__ == '__main__':
    t1 = threading.Thread(target=f1, daemon=True)
    t1.start()

    time.sleep(3)
    print('IM DONE')
