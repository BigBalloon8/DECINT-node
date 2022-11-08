import multiprocessing
import threading
import blockchain
import os
import json
import ast


def reader_pipe_handler(r_pipe, chain:blockchain.Blockchain):
    while True:
        command, args = r_pipe.recv()
        if command == "VALID":
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                nodes = json.load(file)
            block = ast.literal_eval(args[3])
            for node_ in nodes:
                if node_["ip"] == args[1]:
                    wallet = node_["pub_key"]
                    chain.block_valid(args[0], wallet, args[2], block)

        elif command == "CHAIN":
            r_pipe.send(chain.chain)


class ReaderPipe:
    def __init__(self, pipe):
        self.pipe = pipe

    def valid(self, *args):
        self.pipe.send(("VALID", args))

    @property
    def chain(self):
        self.pipe.send(("CHAIN", ()))
        chain = self.pipe.recv()
        return chain


def trans_pipe_handler(t_pipe, chain:blockchain.Blockchain):
    while True:
        command, args = t_pipe.recv()
        if command == "TRANS":
            chain.add_transaction(*args)
        elif command == "PROTOCOL":
            chain.add_protocol(*args)
        elif command == "GETITEM":
            t_pipe.send(chain.chain.__getitem__(args))


class TransPipe:
    def __init__(self, pipe):
        self.pipe = pipe

    def __getitem__(self, item):
        self.pipe.send(("GETITEM", item))
        return self.pipe.recv()

    def add_transaction(self, *args):
        self.pipe.send(("TRANS", args))

    def add_protocol(self, *args):
        self.pipe.send(("PROTOCOL", args))


def val_pipe_handler(v_pipe, chain: blockchain.Blockchain):
    while True:
        command, args = v_pipe.recv()
        if command == "VALID":
            chain.validate(*args)
        elif command == "GETITEM":
            v_pipe.send(chain.chain.__getitem__(args))
        elif command == "CHAIN":
            v_pipe.send(chain.chain)
        elif command == "LEN":
            v_pipe.send(chain.__len__())


class ValPipe:
    def __init__(self, pipe):
        self.pipe = pipe

    def __getitem__(self, item):
        self.pipe.send(("GETITEM", item))
        return self.pipe.recv()

    def __len__(self):
        self.pipe.send(("LEN", ()))
        return self.pipe.recv()

    @property
    def chain(self):
        self.pipe.send(("CHAIN", ()))
        return self.pipe.recv()

    def validate(self, *args):
        self.pipe.send(("VALID", args))


def blockchain_manager(chain, process_pipes:tuple):
    """
    everytime a function is run on the current Blockchain it is done
    via this function
    1. function listens for certain commands from other processes and args for command
    2. function executes command on blockchain
    """
    reader_pipe, trans_pipe, validator_pipe = process_pipes

    rh = threading.Thread(target=reader_pipe_handler, args=(reader_pipe, chain,))
    rh.start()

    th = threading.Thread(target=trans_pipe_handler, args=(trans_pipe, chain,))
    th.start()

    vh = threading.Thread(target=val_pipe_handler, args=(validator_pipe, chain,))
    vh.start()
