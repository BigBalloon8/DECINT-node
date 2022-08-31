import asyncio
import itertools
import hashlib
import ast
import traceback
import functools
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import node
from ecdsa.util import randrange_from_seed__trytryagain
import os
import validator
import copy
from numba import jit
import time
import random
import json
from timeit import default_timer as timer
import math


def priv_key_gen():
    seed = os.urandom(SECP112r2.baselen)
    secexp = randrange_from_seed__trytryagain(seed, SECP112r2.order)
    key = SigningKey.from_secret_exponent(secexp, curve=SECP112r2)
    hex_key = key.to_string().hex()
    return key, hex_key


def pub_key_gen(private_key):
    public_key = private_key.verifying_key
    hex_key = public_key.to_string().hex()
    return public_key, hex_key


def sign_trans(private_key, transaction):
    signature = private_key.sign(transaction.encode())
    return signature


def quick_sort_block(block):
    less = []
    equal = []
    greater = []
    # print(block)

    if len(block) > 1:
        pivot = block[len(block) // 2]
        for trans in block:
            # print(trans)
            if trans["time"] < pivot["time"]:
                less.append(trans)
            elif trans["time"] == pivot["time"]:
                equal.append(trans)
            elif trans["time"] > pivot["time"]:
                greater.append(trans)
        return quick_sort_block(less) + equal + quick_sort_block(greater)
    else:
        return list(block)


class SmartBlock(object):
    def __init__(self, block: list, block_num: int, paths: list):
        self.block = block
        self.block_num = block_num
        self.paths = paths

    def __getitem__(self, item):
        return self.block[item]

    def __setitem__(self, key, value):
        self.block[key] = value
        SmartChain()[self.block_num] = self.block

    def append(self, trans):
        self.block.append(trans)
        SmartChain()[self.block_num] = self.block
        return self.block

    def pop(self, index):
        return self.block.pop(index)

    def insert(self, index, val):
        return self.block.insert(index, val)

    def __next__(self):
        for trans in self.block:
            yield trans

    def __len__(self):
        return len(self.block)

    def __repr__(self):
        return str(self.block)

    def __str__(self):
        return str(self.block)

    # def __list__(self):


class SmartChain(object):  # to prevent running out of memory access different parts of the list at a time
    def __init__(self):
        self.paths = [f"{os.path.dirname(__file__)}/info/blockchain/" + file_path for file_path in
                      os.listdir(os.path.dirname(__file__) + "/info/blockchain/")]
        # TODO have most recent chunk not have to be opened every time (store in memory as list)

    def read_chunk(self, index):  # problem with 2 threads reading file at the same time
        while True:
            try:
                with open(self.paths[index], "r") as file:
                    return json.load(file)
            except json.decoder.JSONDecodeError:
                pass

    def write_chunk(self, index, chunk):
        while True:
            try:
                with open(self.paths[index], "w") as file:
                    return json.dump(chunk, file)
            except json.decoder.JSONDecodeError:  # not sure if this is hte correct acception check later
                pass

    def __getitem__(self, index):
        if index >= 0:
            file_num = index // 10000
            block_index = index - (file_num * 10000)
            chunk = self.read_chunk(file_num)
            return SmartBlock(chunk[block_index], index, self.paths)

        else:
            chunk = self.read_chunk(-1)
            if len(chunk) > 1:
                return SmartBlock(chunk[index], index, self.paths)
            else:  # you never have to go back than 1 or 2 blocks using -index
                chunk = self.read_chunk(-2)
                return SmartBlock(chunk[index + 1], index, self.paths)

    def __len__(self, files=False):
        chunk = self.read_chunk(-1)
        return ((len(self.paths) - 1) * 10000) + len(chunk)

    def __next__(self):
        path_index = 0
        for path in self.paths:
            chunk = self.read_chunk(path_index)
            for block in chunk:
                yield block
            path_index += 1

    """
    def __repr__(self):
        chain = "["
        for path in self.paths:
            with open(path, "r") as file:
                chain = chain + str(json.load(file))[1:-1] + ","
        return chain + "]"
    """

    def __setitem__(self, key, value):
        if key >= 0:
            chunk = self.read_chunk(key // 10000)
            chunk[key - ((key // 10000) * 10000)] = value
            self.write_chunk(key // 10000, chunk)
        else:
            chunk = self.read_chunk(-1)
            if len(chunk) > 1:
                chunk[key] = value
                self.write_chunk(-1, chunk)
            else:
                chunk = self.read_chunk(-2)
                chunk[key + 1] = value
                self.write_chunk(-2, chunk)

    def append(self, block):
        with open(self.paths[-1], "r") as file:
            chunk = json.load(file)
        if len(chunk) == 10000:
            with open(f"{os.path.dirname(__file__)}/info/blockchain/blockchain{len(self.paths)}.json",
                      "w+") as file:
                json.dump([block], file)
            self.paths.append(f"{os.path.dirname(__file__)}/info/blockchain/blockchain{len(self.paths)}.json")
        else:
            with open(self.paths[-1], "w") as file:
                json.dump(chunk + [block], file)

    def update(self, chunk_num, chunk):
        with open(self.paths[chunk_num], "w") as file:
            json.dump(chunk, file)

    def return_chunk(self, chunk_num):
        with open(self.paths[chunk_num], "r") as file:
            chunk = json.load(file)
        print(chunk)
        return chunk


class Blockchain:

    def __init__(self):
        self.chain = SmartChain()

    def __repr__(self):
        return str(self.chain)  # .replace("]", "]\n")

    def print_block(self, block_index):
        return str(self.chain[block_index]).replace("]", "]\n")

    def __len__(self):
        return len(self.chain)

    def __bool__(self):
        print("The Blockchain never lies")
        return True

    def __call__(self):
        return self.chain

    def __getitem__(self, item):
        return self.chain[item]

    def get_block(self, block_index: int):
        try:
            return self.chain[block_index]
        except IndexError:
            print("block not found")

    def block_sort(self, block):
        sort = copy.copy(block)
        block_head = sort.pop(0)
        return [block_head] + quick_sort_block(sort)

    def all_transactions(self, address: str):
        transactions = []
        for block in self.chain:
            for trans in block:
                if trans["sender"] == address:
                    transactions.append(trans)
                    print(trans)
                if trans["receiver"] == address:
                    transactions.append(trans)
                    print(trans)
        return transactions

    def get_block_reward(self, block_index):
        total = 0.0
        for trans in self.chain[block_index]:
            if isinstance(trans, dict):
                if "amount" in trans:
                    total += trans["amount"]*0.01
        return round(total,8)

    @property
    def transaction_total(self):
        total = 0.0
        for block in self.chain:
            total += block[-2][0]
        return total

    def hash_block(self, block):
        string_block = str(block).replace(" ", "")
        hashed = hashlib.sha256(string_block.encode())
        hex_hashed = hashed.hexdigest()
        return hex_hashed

    def update(self, new_chunk1, new_chunk2, chunk_num):
        index = 0
        for block in new_chunk1[::-1]:  # removing invalid blocks and comparing with other
            if isinstance(block[-1], list):
                if not block[-1][0]:
                    index += 1
                    continue
                else:
                    shortened_new_chunk1 = new_chunk1[:-index]
                    break
            else:
                index += 1
                continue

        index = 0
        for block in new_chunk2[::-1]:  # removing invalid blocks and comparing with other
            if isinstance(block[-1], list):
                if not block[-1][0]:
                    index += 1
                    continue
                else:
                    shortened_new_chunk2 = new_chunk2[:-index]
                    break
            else:
                index += 1
                continue
        hash1 = hashlib.sha3_512(str(shortened_new_chunk1).encode())
        hash2 = hashlib.sha3_512(str(shortened_new_chunk2).encode())
        print("\n", hash1.hexdigest(), hash2.hexdigest())
        if hash1.hexdigest() == hash2.hexdigest():
            new_chunk = new_chunk1
        else:
            return False
        self.chain.update(chunk_num, new_chunk)
        print(f"CHUNK {chunk_num} UPDATED SUCCESSFULLY")
        return True

    # @jit(nopython=True)
    def reducable_trans_value(self, total, trans, wallet_address, block_status):  # runs per block

        # print(wallet_address)
        if not isinstance(trans, dict):  # TODO add AI reward system
            return total
        if "amount" in trans:
            if trans["sender"] == wallet_address:
                return total - trans["amount"]
            if trans["receiver"] == wallet_address:
                if block_status:
                    return total + round(trans["amount"] * 0.99, 8)
            else:
                return total
        elif "stake_amount" in trans and trans["pub_key"] == wallet_address:
            return total - trans["stake_amount"]
        elif "unstake_amount" in trans and trans["pub_key"] == wallet_address:
            if block_status:
                return total + trans["unstake_amount"]
        else:
            return total

    def reducable_block_value(self, total, block, wallet, upto):
        block_status = False
        print(block)
        block_index = block[0]
        block = block[1]
        if upto:
            if upto >= block_index:
                return total
        if len(block) > 3:
            if isinstance(block[-1], list):
                if block[-1][0]:
                    block_status = True
                    if block[-1][2] == wallet:
                        total += block[-2][0]

        return total + functools.reduce(
            functools.partial(self.reducable_trans_value, wallet_address=wallet, block_status=block_status), block, 0.0)

    def new_wallet_value(self, wallet_address, block_index=None):  # potentially better have to test
        return functools.reduce(functools.partial(self.reducable_block_value, wallet=wallet_address, upto=block_index),
                                enumerate(self.chain), 0.0)

    #@jit()
    def wallet_value(self, wallet_address, block_index=None):
        value = 0.0
        cur_index = 0  # this has to ber done as self.chain[:block_index + 1] doesn't work with BigList class
        for block in self.chain:
            if block_index == cur_index:
                break
            for trans in block:
                if isinstance(trans, dict):
                    if "amount" in trans:
                        if trans["sender"] == wallet_address:
                            value -= float(trans["amount"])
                            continue
                        if trans["receiver"] == wallet_address:
                            if isinstance(block[-1], list):
                                if block[-1][0]:  # don't add trans amount to value if block not valid
                                    value += round(trans["amount"] * 0.99, 8)
                                    continue
                    elif "stake_amount" in trans and trans["pub_key"] == wallet_address:
                        value -= trans["stake_amount"]
                        continue
                    elif "unstake_amount" in trans and trans["pub_key"] == wallet_address:
                        if isinstance(block[-1], list):
                            if block[-1][0]:
                                value += trans["unstake_amount"]
                                continue
                    elif "AI_reward" in trans and wallet_address in trans["pub_keys"]:
                        value += (trans["AI_reward"] * (
                                trans["AI_reward"][trans["pub_keys"].index(wallet_address)] / sum(
                            trans["AI_reward"])))
            if isinstance(block[-1], list):
                if block[-1][0]:
                    if block[-1][2] == wallet_address:
                        value += block[-2][0] * 0.5
            cur_index += 1

        return value

    def get_stake_value(self, wallet_address, block_index=None):
        value = 0.0
        cur_index = 0  # this has to ber done as self.chain[:block_index + 1] doesn't work with BigList class
        for block in self.chain:  # the reason to not use stake_trans.json is you don't know what block trans is in
            if cur_index == block_index:
                break
            for trans in block:
                if isinstance(trans, dict):
                    if "amount" in trans:
                        continue
                    if trans["pub_key"] == wallet_address:
                        if "stake_amount" in trans:
                            if block[-1][0]:
                                value += trans["stake_amount"]
                        elif "unstake_amount" in trans:
                            value -= trans["stake_amount"]

                if isinstance(trans, str):
                    if wallet_address in trans:
                        if "LIAR" in trans:
                            return 0.0
            cur_index += 1
        return value

    def add_transaction(self, trans: dict):
        if len(self.chain[-1]) == 1:
            time.sleep(0.01)# give time for new block to load
        relative_time = int(float(trans["time"]) - float(self.chain[-1][1]["time"]))
        prev_relative_time = int(float(trans["time"]) - float(self.chain[-2][1]["time"]))
        # prev_relative_time = 10000

        if relative_time < 900:
            if relative_time < 0:
                if prev_relative_time < 900:
                    if not self.chain[-2][-1][0]:
                        self.chain[-2].insert(-3, trans)

                        temp_block = copy.copy(self.chain[-2])

                        temp_block.pop()
                        temp_block.pop()
                        temp_block.pop()

                        self.chain[-2][-3] = [self.hash_block(temp_block), trans["time"]]
                        self.chain[-1][0] = [self.hash_block(temp_block)]
                        self.chain[-2][-2] = [self.chain[-2][-2][0] + round(trans["amount"] * 0.01, 8)]  # += not work
                        self.chain[-2][-1] = [False, trans["time"]]  # block cant be true yet
                        print("--ADDED TO PREVIOUS BLOCK--")

            elif relative_time > 0:
                self.chain[-1].append(trans)
                print("--TRANSACTION ADDED--")

        elif relative_time > 900:
            b_time = self.chain[-1][-1]["time"]
            block_hash = self.hash_block(self.chain[-1])
            trans_fees = 0.0
            for b_trans in self.chain[-1]:
                if isinstance(b_trans, dict):
                    if "amount" in b_trans:
                        trans_fees += round(b_trans["amount"] * 0.01,8)

            block = copy.copy(self.chain[-1])
            self.chain[-1] = self.block_sort(block)
            # self.chain[-1] = block.insert(0, self.chain[-1][0]) #  this was coded a while ago there may be a reason but idk
            self.chain[-1].append([block_hash, b_time])
            self.chain[-1].append([trans_fees])
            self.chain[-1].append([False, b_time])

            new_block = [[block_hash], trans]
            self.chain.append(new_block)
            print("--NEW BLOCK ADDED--")

    def add_protocol(self, announcement):
        relative_time = int(float(announcement["time"]) - float(self.chain[-1][1]["time"]))
        prev_relative_time = int(float(announcement["time"]) - float(self.chain[-2][1]["time"]))
        # prev_relative_time = 10000

        if relative_time < 900:  # if within the 15 mins of current block
            if relative_time < 0:  # if not from the past
                if prev_relative_time < 900:  # in order to add to previous block if within the aloud lateness time in
                    if not self.chain[-2][-1][0]:
                        self.chain[-2].insert(-3, announcement)

                        temp_block = []
                        temp_block = copy.copy(self.chain)

                        temp_block.pop()
                        temp_block.pop()
                        temp_block.pop()

                        self.chain[-2][-3] = [self.hash_block(temp_block), announcement["time"]]
                        self.chain[-1][0] = [self.hash_block(temp_block)]
                        self.chain[-2][-1] = [False, announcement["time"]]
                        print("--STAKE ADDED TO PREVIOUS BLOCK--")

            elif relative_time > 0:  # if in current block
                self.chain[-1].append(announcement)
                print("--STAKE ADDED--")

        elif relative_time > 900:  # if new block is needed
            b_time = self.chain[-1][-1]["time"]
            block_hash = self.hash_block(self.chain[-1])
            trans_fees = 0.0
            for b_trans in self.chain[-1]:
                if isinstance(b_trans, dict):
                    if "amount" in b_trans:
                        trans_fees += round(b_trans["amount"] * 0.01,8)

            block = copy.copy(self.chain[-1])
            self.chain[-1] = self.block_sort(block)
            # self.chain[-1] = block.insert(0, self.chain[-1][0])
            self.chain[-1].append([block_hash, b_time])
            self.chain[-1].append([trans_fees])
            self.chain[-1].append([False, b_time])

            new_block = [[block_hash], announcement]
            self.chain.append(new_block)
            print("--NEW BLOCK--")

    def validate(self, block_index: int, time_of_validation: float, validating: bool = True, block=None):
        # TODO check block hash is the same as other nodes?
        # SEND transactions to other nodes
        valid_trans = []
        if block is None:
            block = self.chain[block_index]

        positions = [0,-1,-2,-3]
        for i in positions:
            if not isinstance(block[i], list):
                if not validating:
                    while True:
                        print("not list")
                    return False

        for trans in block:
            if isinstance(trans, dict):
                if trans["time"] < self.chain[block_index-1][-3][1]:
                    if not validating:
                        while True:
                            print("not correct time")
                        return False
                    else:
                        continue
                if trans["time"] - block[1]["time"] > 900:
                    if not validating:
                        while True:
                            print("not correct time")
                        return False
                    else:
                        continue


                if "amount" in trans:
                    if self.wallet_value(trans["sender"], block_index=block_index) > trans["amount"] > 0.0:
                        if validating:
                            valid_trans.append(trans)
                        else:
                            valid_trans.append(trans)
                            trans_no_sig = copy.copy(trans)
                            trans_no_sig.pop("sig")  # left with trans without sig
                            trans_no_sig = " ".join(map(str, list(trans_no_sig.values())))
                            public_key = VerifyingKey.from_string(bytes.fromhex(trans["sender"]), curve=SECP112r2)
                            if not public_key.verify(bytes.fromhex(trans["sig"]), trans_no_sig.encode()):
                                while True:
                                    print("not correct sig")
                                return False
                    else:
                        if not validating:
                            while True:
                                print("not enough funds")
                            return False

                if "stake_amount" in trans:
                    if self.wallet_value(trans["pub_key"], block_index=block_index) > trans["stake_amount"] > 0.0:
                        if validating:
                            valid_trans.append(trans)
                        else:
                            valid_trans.append(trans)
                            public_key = VerifyingKey.from_string(bytes.fromhex(trans["pub_key"]), curve=SECP112r2)
                            if not public_key.verify(bytes.fromhex(trans["sig"]), str(trans["time"]).encode()):
                                while True:
                                    print("sig wrong")
                                return False
                    else:
                        if not validating:
                            while True:
                                print("not enough funds")
                            return False

                if "unstake_amount" in trans:
                    if self.get_stake_value(trans["pub_key"], block_index=block_index) > trans["unstake_amount"] > 0.0:
                        if validating:
                            valid_trans.append(trans)
                        else:
                            valid_trans.append(trans) # optimise
                            public_key = VerifyingKey.from_string(bytes.fromhex(trans["pub_key"]), curve=SECP112r2)
                            if not public_key.verify(bytes.fromhex(trans["sig"]), str(trans["time"]).encode()):
                                while True:
                                    print("sigs wrong")
                                return False

                    else:
                        if not validating:
                            while True:
                                print("not enough funds")
                            return False
                        
            elif isinstance(trans, list):
                if isinstance(trans[0], float) and len(trans) == 1:  # if is the reward amount list
                    total = 0.0
                    for i in valid_trans:
                        if isinstance(i, dict) and "amount" in i:
                            total += round(i["amount"]*0.01, 8)
                    if not validating:
                        if total != block[-2][0]:
                            print("wrong reward given")
                            return False
                    valid_trans.append([total])
                elif isinstance(trans[0], str) and len(trans) == 2:  # if block hash
                    b_hash = self.hash_block(valid_trans)
                    print("valid_trans: ",valid_trans)
                    b_time = block[-3][1]
                    if not validating:
                        if b_hash != trans[0]:
                            while True:
                                print(b_hash)
                                print(trans)
                                print("wrong block hash")
                            return False
                    valid_trans.append([b_hash, b_time])
                else:
                    valid_trans.append(trans)

        if validating: #TODO give same treatment to BREQ
            message = f"VALID {str(block_index)} {str(time_of_validation)} {str(valid_trans).replace(' ','')}"
            message_len = len(message)
            if message_len < 10000:
                asyncio.run(node.send_to_all(message))
            else:
                messages = [message[i:i + 10000] for i in range(0, message_len, 10000)]
                for message_ in messages:
                    asyncio.run(node.send_to_all(message_))
                    time.sleep(0.5)


            time.sleep(5)  # stop sending multiple VALIDs to dist node

        if not validating:
            return True

    def invalid_trans(self, block_index: int, trans_index: int, ip: str):
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
            nodes = json.load(file)
        node_pub = None
        validators = []
        for bhash in self.chain[block_index][-3]:
            if isinstance(bhash, str):
                # TODO figure out how to include validation time to ony return one node
                validators + validator.rb(block_hash=bhash, block_time=self.chain[-3][1],
                                          invalid=True)  # hmmmmm not sure
        for node_ in nodes:
            if node_["ip"] == ip:
                if node_ in validators:
                    node_pub = node_["pub_key"]

        if not node_pub:
            return

        block_index = int(block_index)
        trans_index = int(trans_index)
        if self.chain[block_index][0]:  # TODO must complete invalid trans before validating
            return
        trans = self.chain[block_index][trans_index]
        if self.wallet_value(trans["sender"], block_index=block_index) < float(trans["amount"]):
            invalid_trans_ = False
        else:
            invalid_trans_ = True

        if invalid_trans_:
            self.chain[block_index].pop(trans_index)
            pre_hashed_blocks = copy.copy(self.chain)

            for i in range(len(self.chain) - block_index):  # update hashes
                pre_hashed_blocks[block_index + i].pop()
                pre_hashed_blocks[block_index + i].pop()
                pre_hashed_blocks[block_index + i].pop()
                block_hash = self.hash_block(pre_hashed_blocks[block_index + i])
                self.chain[block_index + i][-3] = self.chain[block_index + i][-3][0] + [block_hash]
                self.chain[block_index + i + 1][0] = [block_hash]

        if not invalid_trans_:  # TODO update liar system
            stake_removal = f"LIAR {node_pub} {ip}"
            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                stake_trans = json.load(file)
            stake_trans.append(stake_removal)
            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as file:
                json.dump(file)

    def block_valid(self, block_index: int, public_key: str, time_of_validation: float, block):
        # check if is actual validator
        try:
            nodes = []
            stake_trans = []
            for block_hash in self.chain[block_index][0]:
                if isinstance(block_hash, str):
                    val_node = validator.rb(block_hash, self.chain[block_index][1]["time"], time_of_validation)
                    nodes += val_node[0]
            # print(f"VALIDATOR NODES: {nodes}")
            print(f"VALIDATOR NODES: {nodes}")
            for ran_node in nodes:
                if ran_node["pub_key"] == public_key:
                    print("CHECKING CORRECT VALIDATION")
                    correct_validation = self.validate(block_index, time_of_validation, validating=False, block=block)
                    if correct_validation:
                        print("CORRECT VALIDATION")
                        if not self.chain[block_index][-1][0]:
                            self.chain[block_index] = block
                            self.chain[block_index][-1] = [True, time_of_validation, public_key]
                            self.chain[block_index+1][0] = [self.chain[block_index][-3][0]]
                            for trans in self.chain[block_index]:
                                if isinstance(trans, dict):
                                    if "stake_amount" in trans or "unstake_amount" in trans:
                                        stake_trans.append(trans)
                            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as f:
                                stake_transactions = json.load(f)
                            stake_transactions = stake_transactions + stake_trans
                            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as f:
                                json.dump(stake_transactions, f)

                    else:
                        print("LIAR WAS FOUND")
                        stake_removal = f"LIAR {ran_node['pub_key']} {ran_node['ip']}"
                        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                            stake_trans = json.load(file)
                        stake_trans.append(stake_removal)
                        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as file:
                            json.dump(stake_trans, file)
        except:
            while True:
                traceback.print_exc()

    def return_blockchain(self, chunk):
        return self.chain.return_chunk(chunk)


def read_blockchain():
    return Blockchain()


def read_nodes():
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        return json.load(file)


def validate_blockchain(block_index, ip, time_, block):
    chain = read_blockchain()
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    block = ast.literal_eval(block)
    for node_ in nodes:
        if node_["ip"] == ip:
            wallet = node_["pub_key"]
            print("CHECKING IF BLOCK IS VALID")
            chain.block_valid(block_index, wallet, time_, block)
            break


def invalid_blockchain(block_index, transaction_index, ip):
    chain = read_blockchain()
    chain.invalid_trans(block_index, transaction_index, ip)


def get_wallet_val(pub_key):
    chain = read_blockchain()
    return chain.wallet_value(pub_key)


def transaction(priv_key, receiver, amount):
    priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    pub, hex_pub = pub_key_gen(priv_key)
    trans = [str(time.time()), str(hex_pub), receiver, str(amount)]
    trans_str = " ".join(trans)
    sig = priv_key.sign(trans_str.encode()).hex()
    trans.append(sig)
    return trans


def key_tester():
    priv, hex_priv = priv_key_gen()
    pub, hex_pub = pub_key_gen(priv)
    cur_time = 2
    sig1 = sign_trans(priv, str(cur_time))
    sig2 = sign_trans(priv, str(cur_time))
    print(sig1, sig2)
    print(hex_priv, hex_pub, sig1.hex(), cur_time)
    public_key = VerifyingKey.from_string(bytes.fromhex(hex_pub), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig1.hex()), str(cur_time).encode())
        assert public_key.verify(bytes.fromhex(sig2.hex()), str(cur_time).encode())
        print("complete")
    except:
        print("LLLLL")


def tester():
    main_prv = input("PRIV: ")
    for _ in range(100000):
        #main_pub = os.environ["PUB_KEY"]
        time.sleep(1)
        path1 = True #bool(random.randint(0, 1))
        open(f"{os.path.dirname(__file__)}/testing_keys.txt", "w+").close()
        if path1:
            priv, hex_priv = priv_key_gen()
            pub, hex_pub = pub_key_gen(priv)
            amount = float(random.randint(100, 1000))
            with open(f"{os.path.dirname(__file__)}/testing_keys.txt", "a") as file:
                file.write(f"{hex_priv} {hex_pub} {amount}\n")
            trans = transaction(main_prv, hex_pub, amount)
            node.send_to_dist(f"TRANS {' '.join(trans)}")
        else:
            continue
            with open(f"{os.path.dirname(__file__)}/testing_keys.txt", "r") as file:
                test_keys = file.read().splitlines()
            wallet = random.choices(test_keys)
            wallet = wallet[0].split(" ")
            trans = transaction(wallet[0], hex(12), 25.0)
            node.send_to_dist(f"TRANS {' '.join(trans)}")


if __name__ == "__main__":
    # trans = test_transaction("", "da886ae3ec4c355170586317fed0102854f2b9705f58772415577265", 100)
    # print(trans)
    # key_tester()
    CHAIN = Blockchain()
    # print("hash: ", CHAIN.hash_block(1))
    # write_blockchain(CHAIN)
    # print(CHAIN)
    # print(CHAIN.hash_block(CHAIN[-1]))
    # print(read_blockchain().send_blockchain())
    # print(len(CHAIN))
    # CHAIN[-1][-1] = 3
    # print(CHAIN)
    start = timer()
    print(CHAIN.wallet_value("6efa5bfa8a9bfebaacacf9773f830939d8cb4a2129c1a2aaafaaf549"))
    print(timer() - start)
    # print(CHAIN.block_sort(CHAIN[-1]))
