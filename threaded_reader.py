import traceback
import node
import time
from requests import get
import blockchain
import json
import textwrap
import os


def read(chain):
    print("---THREADED READER STARTED---")
    #ip = get('https://api.ipify.org').text
    try:
        while True:
            node_lines = node.request_reader("THREAD")
            if node_lines:
                #print(f"NODE LINES: {node_lines}\n")
                for message in node_lines:
                    message = message.split(" ")

                    if message[1] == "VALID":  # update block to true
                        print("VALID")
                        blockchain.validate_blockchain(int(message[2]), message[0], float(message[3]), message[4], chain)

                    elif message[1] == "BLOCKCHAIN?":
                        #print("BLOCKCHAIN?")
                        send_chain = "BREQ " + str(chain.return_blockchain()).replace(" ", "")
                        messages = textwrap.wrap(send_chain, 5000)
                        for message_ in messages:
                            node.send(message[0], message_)

    except:
        import time
        while True:
            time.sleep(0.5)
            traceback.print_exc()



if __name__ == "__main__":
    read()
