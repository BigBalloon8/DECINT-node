import os
import blockchain
import node
import trans_reader
import validator
import reader
import concurrent.futures
import socket
import multiprocessing
import threading
import proccess_management



def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    local_ip = socket.gethostbyname(socket.gethostname())

    chain = blockchain.Blockchain()
    queue = multiprocessing.Queue(maxsize=1)

    rec = multiprocessing.Process(target=node.receive)
    rec.start()

    update = threading.Thread(target=node.updator, args=(chain,))
    update.start()
    update.join()

    multiproccess_chain = proccess_management.QueueWrapper(queue, chain)

    message_reader = multiprocessing.Process(target=reader.read, args=(multiproccess_chain,))
    message_reader.start()

    tr_reader = multiprocessing.Process(target=trans_reader.read, args=(multiproccess_chain,))
    tr_reader.start()

    val = multiprocessing.Process(target=validator.am_i_validator, args=(multiproccess_chain,))
    val.start()

    #with concurrent.futures.ProcessPoolExecutor() as executor:
        #executor.submit(threaded_reader.read, multiproccess_chain)
        #executor.submit(trans_reader.read, multiproccess_chain)
        #executor.submit(validator.am_i_validator, multiproccess_chain)


if __name__ == '__main__':
    run()










