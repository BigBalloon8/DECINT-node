import node
import blockchain



def read():
    print("---ONLINE READER STARTED---")
    while True:
        online_lines = node.request_reader("ONLINE")
        if online_lines:
            for message in online_lines:
                if message and message != " ":
                    message = message.split(" ")
                try:
                    node.message_handler(message)
                except Exception as e:
                    node.send(message[0], f"ERROR {e}")
                    print(message[1], e)
                    continue

                if message[1] == "ONLINE?":
                    pass
                    #print(f"yh sent to {message[0]}")
                    #node.send(message[0], "yh")

                elif message[1] == "GET_NODES":
                    #print("GET_NODES")
                    node.send_node(message[0])

                elif message[1] == "BLOCKCHAIN?":
                    #print("BLOCKCHAIN?")
                    chain = blockchain.read_blockchain()
                    node.send(message[0], "BREQ " + str(chain.return_blockchain(int(message[2]))).replace(" ", ""))

                elif message[1] == "BLOCKCHAINLEN?":
                    #print("getting BLOCKCHAINLEN?")
                    chain = blockchain.read_blockchain()
                    node.send(message[0], "BLENREQ " + str(len(chain)))


if __name__ == "__main__":
    read()