import node
import os


def rec():
    print("---RECEIVER STARTED---")
    while True:
        message, address = node.receive()
        print(f"Message from {address} , {message}\n")
        if "DIST" in message:
            with open(f"{os.path.dirname(__file__)}/dist_messages.txt", "a") as file:
                file.write(f"{address[0]} {message}\n")
                #file.write(f"{message.replace('DIST ','')}\n")
        else:
            with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "a") as file:
                file.write(f"{address[0]} {message}\n")
            


if __name__ == "__main__":
    rec()
