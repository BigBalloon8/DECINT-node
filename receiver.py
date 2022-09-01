import node
import os
from threading import Thread


def write_line(message, address):
    if "DIST" in message:
        with open(f"{os.path.dirname(__file__)}/dist_messages.txt", "a") as file:
            file.write(f"{address[0]} {message}\n")
            # file.write(f"{message.replace('DIST ','')}\n")
    else:
        if " " not in message and "ONLINE?" not in message and "BLOCKCHAIN?" not in message and "GET_NODES" not in message and "BLOCKCHAINLEN?" not in message:
            with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "r") as file:
                lines = []
                for line in file.read().split("\n"):
                    if ("VALID" in line and "]]" not in line) or ("BREQ" in line and ("]]]" not in line or "}]]"not in line)): #TODO this is temporary needs to define between valid and breq
                        lines.append(line + message)
                    else:
                        lines.append(line)
            with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w") as file:
                print("writing lines")
                file.write("\n".join(lines) + "\n")
        else:
            with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "a+") as file:
                file.write(f"{address[0]} {message}\n")

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
