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

    r_conn1, r_conn2 = multiprocessing.Pipe(duplex=True)
    t_conn1, t_conn2 = multiprocessing.Pipe(duplex=True)
    v_conn1, v_conn2 = multiprocessing.Pipe(duplex=True)

    r_pipe = process_management.ReaderPipe(r_conn2)
    t_pipe = process_management.TransPipe(t_conn2)
    v_pipe = process_management.ValPipe(v_conn2)

    process_manager = multiprocessing.Process(target=process_management.blockchain_manager,
                                              args=(chain, (r_conn1, t_conn1, v_conn1),))
    process_manager.start()

    message_reader = multiprocessing.Process(target=reader.read, args=(r_pipe,))
    message_reader.start()

    tr_reader = multiprocessing.Process(target=trans_reader.read, args=(t_pipe,))
    tr_reader.start()

    val = multiprocessing.Process(target=validator.am_i_validator, args=(v_pipe,))
    val.start()

    #with concurrent.futures.ProcessPoolExecutor() as executor:
        #executor.submit(threaded_reader.read, multiproccess_chain)
        #executor.submit(trans_reader.read, multiproccess_chain)
        #executor.submit(validator.am_i_validator, multiproccess_chain)


if __name__ == '__main__':
    run()










