import node
import os
from threading import Thread




def rec():
    print("---RECEIVER STARTED---")
    while True:
        message, address = node.receive()
        if "\n" in message:
            continue
        print(f"Message from {address} , {message}\n")
        thread = Thread(target=write_line, args=(message, address,))
        thread.start()
        continue
            


if __name__ == "__main__":
    rec()
