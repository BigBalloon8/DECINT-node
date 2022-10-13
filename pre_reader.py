import traceback
import node
import blockchain
import textwrap


def read(chain):
    print("---ONLINE READER STARTED---")
    while True:
        try:
            online_lines = node.request_reader("ONLINE")
            if online_lines:
                for message in online_lines:
                    if message and message != " ":
                        message = message.split(" ")

                    if message[1] == "ONLINE?":
                        pass
                        #print(f"yh sent to {message[0]}")
                        #node.send(message[0], "yh")

                    elif message[1] == "GET_NODES":
                        #print("GET_NODES")
                        node.send_node(message[0])

                    elif message[1] == "BLOCKCHAIN?":
                        #print("BLOCKCHAIN?")
                        chunk = "BREQ " + str(chain.return_blockchain()).replace(" ", "")
                        messages = textwrap.wrap(chunk, 5000)
                        for message_ in messages:
                            node.send(message[0], message_)


        except:
            import time
            while True:
                time.sleep(0.5)
                traceback.print_exc()


if __name__ == "__main__":
    read()