import random
import traceback
import node
import blockchain
import json
import textwrap
import os
import time
import random


def read(queue):
    print("---PROCESS READER STARTED---")
    #ip = get('https://api.ipify.org').text
    try:
        while True:
            if not queue.empty():
                message = queue.get()
                if message:
                    message = message.split(" ")

                    if message[1] == "HELLO":
                        print("HELLO")
                        node.new_node(float(message[2]), message[0], message[3], int(message[4]), float(message[5]), message[6], message[7])

                    elif message[1] == "UPDATE":
                        print("UPDATE")
                        node.update_node(message[0], float(message[2]), message[3], message[4], int(message[5]), float(message[6]), message[7])

                    elif message[1] == "DELETE":
                        print("DELETE")
                        node.delete_node(float(message[2]), message[0], message[3], message[4])

                    elif message[1] == "ONLINE?":
                        pass
                    #print(f"yh sent to {message[0]}")
                        #node.send(message[0], "yh")

                    elif message[1] == "GET_NODES":
                        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                            nodes = json.load(file)
                        str_node = json.dumps(nodes).replace(" ", "")
                        messages = textwrap.wrap("NREQ " + str_node, 5000)
                        for message_ in messages[:-1]:
                            node.send(message[0], message_)
                        node.send(message[0], messages[-1] + "END")


                    elif message[1] == "GET_STAKE_TRANS":
                        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                            stake_trans = json.load(file)
                        temp_message = "SREQ " + json.dumps(stake_trans).replace(" ", "")
                        messages = textwrap.wrap(temp_message, 5000)
                        for message_ in messages[:-1]:
                            node.send(message[0], message_)
                        node.send(message[0], messages[-1] + "END")
    except:
        while True:
            time.sleep(0.5)
            traceback.print_exc()



if __name__ == "__main__":
    read()
