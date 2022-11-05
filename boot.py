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

    def get_block(self, block_index):
        chain = self.get_chain()
        return chain.get_block(block_index)

    def block_sort(self, block):
        chain = self.get_chain()
        return chain.block_sort(block)

    def get_block_reward(self, block_index):
        chain = self.get_chain()
        return chain.get_block_reward(block_index)

    def hash_block(self, block):
        chain = self.get_chain()
        return chain.hash_block(block)

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

    def temp_to_final(self, block_index):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                chain.temp_to_final(block_index)
                self.queue.put(chain)
                break

    def block_valid(self, block_index: int, public_key: str, time_of_validation: float, block):
        while True:
            if not self.queue.empty():
                chain = self.queue.get()
                chain.block_valid(block_index, public_key, time_of_validation, block)
                self.queue.put(chain)
                break


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

    multiproccess_chain = QueueWrapper(queue, chain)

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










