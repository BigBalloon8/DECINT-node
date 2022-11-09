import multiprocessing
import threading
import blockchain
import os
import json
import ast

def reader_queue_handler(r_rec_queue,r_sen_queue , chain:blockchain.Blockchain):
    while True:
        if not r_rec_queue.empty():
            command, args = r_rec_queue.get()
            if command == "VALID":
                with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                    nodes = json.load(file)
                block = ast.literal_eval(args[3])
                for node_ in nodes:
                    if node_["ip"] == args[1]:
                        wallet = node_["pub_key"]
                        chain.block_valid(args[0], wallet, args[2], block)

            elif command == "CHAIN":
                r_sen_queue.put(chain.chain)


class ReaderQueue:
    def __init__(self, rec_queue, send_queue):
        self.rec_queue = rec_queue
        self.send_queue = send_queue

    def valid(self, *args):
        self.send_queue.put(("VALID", args))

    @property
    def chain(self):
        self.send_queue.put(("CHAIN", ()))
        while True:
            if not self.rec_queue.empty():
                chain = self.rec_queue.get()
                return chain


def trans_queue_handler(t_rec_queue,t_sen_queue, chain:blockchain.Blockchain):
    while True:
        if not t_rec_queue.empty():
            command, args = t_rec_queue.get()
            if command == "TRANS":
                chain.add_transaction(*args)
            elif command == "PROTOCOL":
                chain.add_protocol(*args)
            elif command == "GETITEM":
                t_sen_queue.put(chain.chain.__getitem__(args))


class TransQueue:
    def __init__(self, rec_queue, send_queue):
        self.rec_queue = rec_queue
        self.send_queue = send_queue

    def __getitem__(self, item):
        self.send_queue.put(("GETITEM", item))
        while True:
            if not self.send_queue.empty():
                return self.rec_queue.get()

    def add_transaction(self, *args):
        self.send_queue.put(("TRANS", args))

    def add_protocol(self, *args):
        self.send_queue.put(("PROTOCOL", args))


def val_queue_handler(v_rec_queue,v_sen_queue, chain: blockchain.Blockchain):
    while True:
        if not v_rec_queue.empty():
            command, args = v_rec_queue.get()
            if command == "VALID":
                chain.validate(*args)
            elif command == "GETITEM":
                v_sen_queue.put(chain.chain.__getitem__(args))
            elif command == "CHAIN":
                v_sen_queue.put(chain.chain)
            elif command == "LEN":
                v_sen_queue.put(chain.__len__())


class ValQueue:
    def __init__(self, rec_queue, send_queue):
        self.rec_queue = rec_queue
        self.send_queue = send_queue

    def __getitem__(self, item):
        self.send_queue.put(("GETITEM", item))
        while True:
            if not self.rec_queue.empty():
                return self.rec_queue.get()

    def __len__(self):
        self.send_queue.put(("LEN", ()))
        while True:
            if not self.rec_queue.empty():
                return self.rec_queue.get()

    @property
    def chain(self):
        self.send_queue.put(("CHAIN", ()))
        while True:
            if not self.rec_queue.empty():
                return self.rec_queue.get()

    def validate(self, *args):
        self.send_queue.put(("VALID", args))


def blockchain_manager(chain, process_queues:tuple):
    """
    everytime a function is run on the current Blockchain it is done
    via this function
    1. function listens for certain commands from other processes and args for command
    2. function executes command on blockchain
    """
    (r_sender,r_receiver),(t_sender,t_receiver),(v_sender,v_receiver) = process_queues
    #reader_pipe, trans_pipe, validator_pipe = process_queues

    rh = threading.Thread(target=reader_queue_handler, args=(r_receiver, r_sender, chain,))
    rh.start()

    th = threading.Thread(target=trans_queue_handler, args=(t_receiver,t_sender, chain,))
    th.start()

    vh = threading.Thread(target=val_queue_handler, args=(v_receiver, v_sender, chain,))
    vh.start()
