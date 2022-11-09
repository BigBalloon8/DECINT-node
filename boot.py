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
import process_management



def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    local_ip = socket.gethostbyname(socket.gethostname())

    chain = blockchain.Blockchain()

    rec = multiprocessing.Process(target=node.receive)
    rec.start()

    update = threading.Thread(target=node.updator, args=(chain,))
    update.start()
    update.join()

    r_sender = multiprocessing.Queue()
    r_receiver = multiprocessing.Queue()
    t_sender = multiprocessing.Queue()
    t_receiver = multiprocessing.Queue()
    v_sender = multiprocessing.Queue()
    v_receiver = multiprocessing.Queue()
    queues = ((r_sender, r_receiver), (t_sender, t_receiver), (v_sender, v_receiver))

    r_queue = process_management.ReaderQueue(r_sender, r_receiver)  # supposed to be in this order
    t_queue = process_management.TransQueue(t_sender, t_receiver)
    v_queue = process_management.ValQueue(v_sender, v_receiver)

    process_manager = multiprocessing.Process(target=process_management.blockchain_manager,
                                              args=(chain, queues,))
    process_manager.start()

    message_reader = multiprocessing.Process(target=reader.read, args=(r_queue,))
    message_reader.start()

    tr_reader = multiprocessing.Process(target=trans_reader.read, args=(t_queue,))
    tr_reader.start()

    val = multiprocessing.Process(target=validator.am_i_validator, args=(v_queue,))
    val.start()

    #with concurrent.futures.ProcessPoolExecutor() as executor:
        #executor.submit(threaded_reader.read, multiproccess_chain)
        #executor.submit(trans_reader.read, multiproccess_chain)
        #executor.submit(validator.am_i_validator, multiproccess_chain)


if __name__ == '__main__':
    run()










