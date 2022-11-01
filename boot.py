import os
import blockchain
import node
import threaded_reader
import trans_reader
import validator
import process_reader
import concurrent.futures
import socket
import multiprocessing
import threading


"""
update tensorflow
update Blockchain and nodes
"""
def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"MY IP: {local_ip}")
    #local_ip = input("IP: ").replace(" ", "")

    chain = blockchain.Blockchain()

    rec = multiprocessing.Process(target=node.receive)
    rec.start()

    update = threading.Thread(target=node.updator, args=(chain,))
    update.start()
    update.join()

    reader = multiprocessing.Process(target=process_reader.read)
    reader.start()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(threaded_reader.read, chain)
        executor.submit(trans_reader.read, chain)
        executor.submit(validator.am_i_validator, chain)


if __name__ == '__main__':
    run()










