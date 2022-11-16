import traceback
import node
import time
from requests import get
import blockchain
import json
import textwrap
import os


def read(chain, queue):
    #ip = get('https://api.ipify.org').text
    try:
        if not queue.empty():
            line = queue.get()
            #print(f"NODE LINES: {node_lines}\n")
            message = line.split(" ")

            if message[1] == "VALID":  # update block to true
                blockchain.validate_blockchain(int(message[2]), message[0], float(message[3]), message[4], chain)

            elif message[1] == "BLOCKCHAIN?":
                send_chain = "BREQ " + json.dumps(chain.return_blockchain().present_chain).replace(" ", "")
                messages = textwrap.wrap(send_chain, 5000)
                for message_ in messages[:-1]:
                    node.send(message[0], message_)
                node.send(message[0], messages[-1] + "END")

    except:
        import time
        while True:
            time.sleep(0.5)
            traceback.print_exc()



if __name__ == "__main__":
    read()
