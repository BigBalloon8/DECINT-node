import traceback
import node
import time
from requests import get
import blockchain


def read(chain):
    print("---READER STARTED---")
    #ip = get('https://api.ipify.org').text
    try:
        while True:
            node.dist_request_reader("LEFT_OVER")  # clear strange dist messages
            node_lines = node.request_reader("NODE")
            if node_lines:
                #print(f"NODE LINES: {node_lines}\n")
                for message in node_lines:
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

                    if message[1] == "VALID":  # update block to true
                        print("VALID")
                        blockchain.validate_blockchain(int(message[2]), message[0], float(message[3]), message[4], chain)

                    else:
                        pass
    except:
        import time
        while True:
            time.sleep(0.5)
            traceback.print_exc()



if __name__ == "__main__":
    read()
