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

    

def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    # local_ip = socket.gethostbyname(socket.gethostname())

    chain = blockchain.Blockchain()

    req_queue = multiprocessing.Queue()
    trans_queue = multiprocessing.Queue()
    process_queue = multiprocessing.Queue()
    thread_queue = multiprocessing.Queue()

    rec = multiprocessing.Process(target=node.receive, args=(req_queue, trans_queue, process_queue, thread_queue,))
    rec.start()

    update = threading.Thread(target=node.updator, args=(chain, req_queue))
    update.start()
    update.join()

    reader = multiprocessing.Process(target=process_reader.read, args=(process_queue,))
    reader.start()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        #executor.submit(threaded_reader.read, chain, thread_queue)
        executor.submit(trans_reader.read, chain, trans_queue, thread_queue)
        executor.submit(validator.am_i_validator, chain)


if __name__ == '__main__':
    run()










