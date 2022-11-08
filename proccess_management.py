import multiprocessing
import blockchain

def reader_handler(pipe_connection:multiprocessing.Connection):
    while True:
        command = pipe_connection.recv()
        if command == 



def blockchain_manager(chain, process_shared_vals:list):
    """
    everytime a function is run on the current Blockchain it is done
    via this function
    1. function listens for certain commands from other processes and args for command
    2. function executes command on blockchain

    COMMAND ARGS
    get_chain -
    chain -
    __repr__ -
    __len__ -
    __call__ -
    __getitem__ -
    __iter__ -
    update -
    wallet_value -
    get_stake_value -
    add_transaction -
    add_protocol -
    validate -
    block_valid -
    """
    while True:
        pass


class blockchain_command_caller:
    pass

class QueueWrapper:  # TODO use decorators to neaten up
    def __init__(self, queue: multiprocessing.Queue, chain: blockchain.Blockchain):
        self.queue = queue
        self.queue.put(chain)

    def get_chain(self) -> blockchain.Blockchain:
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                self.queue.put(chain)
                return chain

    @property
    def chain(self):
        return self.get_chain().chain

    def __repr__(self):
        chain = self.get_chain()
        return chain.__repr__()

    def __len__(self):
        chain = self.get_chain()
        return chain.__len__()

    def __call__(self):
        chain = self.get_chain()
        return chain.__call__()

    def __getitem__(self, item):
        chain = self.get_chain()
        return chain.__getitem__(item)

    def __iter__(self):
        chain = self.get_chain()
        return chain.__iter__()

    def update(self, new_chain1, new_chain2):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                status = chain.update(new_chain1, new_chain2)
                self.queue.put(chain)
                return status

    def wallet_value(self, wallet_address, block_index):
        chain = self.get_chain()
        return chain.wallet_value(wallet_address, block_index)

    def get_stake_value(self, wallet_address, block_index):
        chain = self.get_chain()
        return chain.get_stake_value(wallet_address, block_index)

    def add_transaction(self, trans):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                chain.add_transaction(trans)
                self.queue.put(chain)
                break

    def add_protocol(self, announcment):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                chain.add_protocol(announcment)
                self.queue.put(chain)
                break

    def validate(self, block_index: int, time_of_validation: float, validating: bool = True, block=None):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                status = chain.validate(block_index, time_of_validation, validating, block)
                self.queue.put(chain)
                return status

    def block_valid(self, block_index: int, public_key: str, time_of_validation: float, block):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                chain.block_valid(block_index, public_key, time_of_validation, block)
                self.queue.put(chain)
                break