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


class QueueWrapper():
    def __int__(self, queue, chain):
        self.queue = queue
        self.queue.put(chain)

    

def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    # local_ip = socket.gethostbyname(socket.gethostname())

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










