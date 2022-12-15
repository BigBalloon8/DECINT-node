import asyncio
from base64 import decode
import hashlib
import ast
import traceback
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import node
from ecdsa.util import randrange_from_seed__trytryagain
import os
import validator
import copy
import time
import random
import json
from timeit import default_timer as timer
import math
import textwrap
from contextlib import suppress


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


def sign_trans(private_key, trans):
    signature = private_key.sign(trans.encode())
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
    return list(block)


class SmartBlock(object):
    def __init__(self, block: list, block_num: int, chain_obj: list):
        self.block = block
        self.block_num = block_num
        self.chain_obj = chain_obj

    def __getitem__(self, item):
        return self.block[item]

    def __setitem__(self, key, value):
        self.block[key] = value
        self.chain_obj[self.block_num] = self.block

    def append(self, trans):
        self.block.append(trans)
        self.chain_obj[self.block_num] = self.block
        return self.block

    def pop(self, index):
        item = self.block.pop(index)
        self.chain_obj[self.block_num] = self.block
        return item

    def insert(self, index, val):
        self.block.insert(index, val)
        self.chain_obj[self.block_num] = self.block
        return self.block

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


class BlockchainError(Exception):
    pass


class SmartChainKeyError(BlockchainError):
    pass


class SmartChainV2:

    def __init__(self):
        self.present_chain = [[["c484eb3cfd69ad6c289dcc1e1b671929cdb7b6a63f75a4d21e8d1e126ad8433d", 1, 901.0], {"0": 0.0,"6efa5bfa8a9bfebaacacf9773f830939d8cb4a2129c1a2aaafaaf549": 8388607.0}, ["6db4f412053b48a7f2579ed59d28a7d623ef6ebc9d5023b17cb331b8b92d5be8", 902.0], [0], [True, 903.0, "0"]], [["6db4f412053b48a7f2579ed59d28a7d623ef6ebc9d5023b17cb331b8b92d5be8", 2, 1802.0], {"time": 1802.0, "pub_key": "6efa5bfa8a9bfebaacacf9773f830939d8cb4a2129c1a2aaafaaf549", "stake_amount": 1.0, "sig": "225a69aee9a4a360ba496c11b3e030321371246cfccf86e9ed7c8056"}]]
        self.position_tracker = {1:0, 2:1}

    def __getitem__(self, index):
        if index < 0:
            return SmartBlock(self.present_chain[index], index, self)
        else:
            try:
                return SmartBlock(self.present_chain[self.position_tracker[index]], index, self)
            except KeyError:
                print(index)
                raise SmartChainKeyError

    def get_index(self, index):
        for i, block in enumerate(self.present_chain):
            if block[0][1] == index:
                return i

    def __setitem__(self, index, value):
        if index < 0:
            self.present_chain[index] = value
        else:
            self.present_chain[self.position_tracker[index]] = value

    def __iter__(self):
        for i, block in zip(self.position_tracker.values(), self.present_chain):
            yield SmartBlock(block, i ,self)

    def append(self, block):
        self.present_chain.append(block)
        self.position_tracker[block[0][1]] = len(self.position_tracker)

    def update(self,chain):
        self.present_chain = chain
        self.position_tracker = {}
        for i, block in enumerate(chain):
            self.position_tracker[block[0][1]] = i

    def update_pos_tracker(self):
        self.position_tracker = {}
        for i, block in enumerate(copy.copy(self.present_chain)):
            self.position_tracker[block[0][1]] = i

    def pop(self, index):
        popped = self.present_chain.pop(self.position_tracker[index])
        self.update_pos_tracker()
        return popped

    def __str__(self):
        return str(self.present_chain)

    def __len__(self):
        return len(self.present_chain)

    def exists(self,index):
        if index in self.position_tracker.keys():
            return True
        return False

    def save_state(self):
        with open(f"{os.path.dirname(__file__)}/info/blockchain.json", "w") as file:
            json.dump(self.present_chain, file)


class Blockchain:

    def __init__(self):
        self.chain = SmartChainV2()  # smart chain is just a list

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

    def __iter__(self):
        for block in self.chain:
            yield block

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

    def update(self, new_chain1, new_chain2):
        index = 0
        for block in new_chain1[::-1]:  # removing invalid blocks and comparing with other
            if isinstance(block[-1], list):
                if not block[-1][0]:
                    index += 1
                    continue
                else:
                    if index: #if not 0
                        shortened_new_chain1 = new_chain1[:-index]
                    else:
                        shortened_new_chain1 = new_chain1
                    break
            else:
                index += 1
                continue

        index = 0
        for block in new_chain2[::-1]:  # removing invalid blocks and comparing with other
            if isinstance(block[-1], list):
                if not block[-1][0]:
                    index += 1
                    continue
                else:
                    shortened_new_chain2 = new_chain2[:-index]
                    break
            else:
                index += 1
                continue
        hash1 = hashlib.sha3_512(str(shortened_new_chain1).encode())
        hash2 = hashlib.sha3_512(str(shortened_new_chain2).encode())
        print("\n", hash1.hexdigest(), hash2.hexdigest())
        if hash1.hexdigest() == hash2.hexdigest():
            new_chain = new_chain1
        else:
            return False
        self.chain.update(new_chain)
        print(f"BLOCKCHAIN UPDATED SUCCESSFULLY")
        return True

    #@jit()
    def wallet_value(self, wallet_address, block_index=None):
        value = 0.0
        if not block_index:
            block_index = self.chain[-1][0][1]


        while True:
            i = 1
            if self.chain[block_index-i][-1][0]:
                if "sig" not in self.chain[block_index-i][1]:
                    wallets = self.chain[block_index-i][1]
                    break
                else:
                    pass
            else:
                i+=1
        with suppress(IndexError):
            value += wallets[wallet_address]


        for j in range(i):
            block = self.chain[block_index-j]
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


        return value

    def get_stake_value(self, wallet_address, block_index=None):
        value = 0.0

        while True:
            try:
                with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                    stake_trans = json.load(file)
                    break
            except json.decoder.JSONDecodeError:
                pass

            for block_i, trans in stake_trans:
                if block_i < block_index:
                    if isinstance(trans, dict):
                        if trans["pub_key"] == wallet_address:
                            if "stake_amount" in trans:
                                if self.chain[block_i][-1][0]:
                                    value += trans["stake_amount"]
                            elif "unstake_amount" in trans:
                                value -= trans["stake_amount"]

                if isinstance(trans, str):
                    if wallet_address in trans:
                        if "LIAR" in trans:
                            return 0.0
        return value

    def add_transaction(self, trans: dict):
        relative_time = int(float(trans["time"]) - float(self.chain[-1][1]["time"]))
        prev_relative_time = int(float(trans["time"]) - float(self.chain[-2][0][2]))
        # prev_relative_time = 10000

        if relative_time < 120:
            if relative_time < 0:
                if prev_relative_time < 120:
                    if not self.chain[-2][-1][0]:
                        self.chain[-2].insert(-3, trans)

                        temp_block = copy.copy(self.chain[-2])

                        temp_block.pop()
                        temp_block.pop()
                        temp_block.pop()

                        self.chain[-2][-3] = [self.hash_block(temp_block), trans["time"]]
                        self.chain[-1][0] = [self.hash_block(temp_block),self.chain[-2][0][1]+1,self.chain[-1][1]["time"]]
                        self.chain[-2][-2] = [self.chain[-2][-2][0] + round(trans["amount"] * 0.01, 8)]  # += not work
                        self.chain[-2][-1] = [False, trans["time"]]  # block cant be true yet
                        print("--ADDED TO PREVIOUS BLOCK--")

            elif relative_time > 0:
                self.chain[-1].append(trans)
                print(f"--TRANSACTION ADDED--{trans['sig']}--")

        elif relative_time > 120:
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

            new_block = [[block_hash, self.chain[-1][0][1]+1, trans["time"]], trans]
            self.chain.append(new_block)
            print("--NEW BLOCK ADDED--")

    def add_protocol(self, announcement):
        relative_time = int(float(announcement["time"]) - float(self.chain[-1][1]["time"]))
        prev_relative_time = int(float(announcement["time"]) - float(self.chain[-2][0][2]))
        # prev_relative_time = 10000

        if relative_time < 120:  # if within the 15 mins of current block
            if relative_time < 0:  # if from the past
                if prev_relative_time < 120:  # in order to add to previous block if within the aloud message lateness time in
                    if not self.chain[-2][-1][0]:
                        self.chain[-2].insert(-3, announcement)

                        temp_block = []
                        temp_block = copy.copy(self.chain)

                        temp_block.pop()
                        temp_block.pop()
                        temp_block.pop()

                        self.chain[-2][-3] = [self.hash_block(temp_block), announcement["time"]]
                        self.chain[-1][0] = [self.hash_block(temp_block), self.chain[-2][0][1]+1, self.chain[-1][1]["time"]]
                        self.chain[-2][-1] = [False, announcement["time"]]
                        print("--STAKE ADDED TO PREVIOUS BLOCK--")

            elif relative_time > 0:  # if in current block
                self.chain[-1].append(announcement)
                print("--STAKE ADDED--")

        elif relative_time > 120:  # if new block is needed
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

            new_block = [[block_hash, self.block[-1][0][1]+1, announcement["time"]], announcement]
            self.chain.append(new_block)
            print("--NEW BLOCK--")

    def validate(self, block_index: int, time_of_validation: float, validating: bool = True, block=None):
        # SEND transactions to other nodes
        valid_trans = []
        if block is None:
            block = self.chain[block_index]
            #print("VALDATING_BLOCK: ", block)

        positions = [0, -1, -2, -3]
        for i in positions:
            if not isinstance(block[i], list):
                if not validating:
                    return False

        for trans in block:
            if isinstance(trans, dict):
                if trans["time"] < self.chain[block_index-1][-3][1]:
                    if not validating:
                        return False
                    else:
                        continue
                if trans["time"] - block[1]["time"] > 120:
                    if not validating:
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

        if validating:
            message = f"VALID {block_index} {time_of_validation} {json.dumps(valid_trans).replace(' ','')}"
            message_len = len(message)
            if message_len < 5000:
                asyncio.run(node.send_to_all("#" + message + "END", no_dist=True))
            else:
                messages = textwrap.wrap(message, 5000)
                for message_ in messages[:-1]:
                    asyncio.run(node.send_to_all("#" + message_, no_dist=True))
                    time.sleep(0.005)
                asyncio.run(node.send_to_all("#" + messages[-1] + "END", no_dist=True))
            time.sleep(1)  # stop sending multiple VALIDs

        if not validating:
            return True

    def temp_to_final(self, block_index):
        """
        Takes transaction based block and converts to a wallet based
        """
        block_head = self.chain[block_index][0]
        block_tail = self.chain[block_index][-3:]
        block_wallets = self.chain[block_index-1][1]

        for trans in self.chain[block_index][1:-3]:
            if "amount" in trans:
                block_wallets[trans["sender"]] -= trans["amount"]
                try:
                    block_wallets[trans["receiver"]] += round(trans["amount"]*0.99,8)
                except KeyError:
                    block_wallets[trans["receiver"]] = round(trans["amount"]*0.99,8)

            elif "stake_amount" in trans:
                block_wallets[trans["pub_key"]] -= trans["stake_amount"]

            elif "unstake_amount" in trans:
                block_wallets[trans["pub_key"]] -= trans["unstake_amount"]

        block_wallets[self.chain[block_index][-1][2]] += self.chain[block_index][-2][0]

        self.chain[block_index] = [block_head, block_wallets] + block_tail
        self.chain.pop(block_index-1)
        self.chain.save_state()



    def block_valid(self, block_index: int, public_key: str, time_of_validation: float, block):
        # check if is actual validator
        try:
            nodes = []
            stake_trans = []
            for block_hash in self.chain[block_index][0]:
                if isinstance(block_hash, str):
                    if "time" in self.chain[block_index][1]:
                        val_node = validator.rb(block_hash, self.chain[block_index][1]["time"], time_of_validation)
                        nodes += val_node[0]
                    else:
                        return
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
                            self.chain[block_index+1][0] = [self.chain[block_index][-3][0], self.chain[block_index][0][1]+1, self.chain[block_index+1][1]["time"]]
                            for trans in self.chain[block_index]:
                                if isinstance(trans, dict):
                                    if "stake_amount" in trans or "unstake_amount" in trans:
                                        stake_trans.append([block_index, trans])
                            while True:
                                try:
                                    with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as f:
                                        stake_transactions = json.load(f)
                                    stake_transactions = stake_transactions + stake_trans
                                    with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as f:
                                        json.dump(stake_transactions, f)
                                    break
                                except json.decoder.JSONDecodeError:
                                    pass

                            self.temp_to_final(block_index)

                    else:
                        print("LIAR WAS FOUND") # UPDATE this to add late validators to liars
                        stake_removal = f"LIAR {ran_node['pub_key']} {ran_node['ip']}"
                        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                            stake_trans = json.load(file)
                        stake_trans.append(stake_removal)
                        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as file:
                            json.dump(stake_trans, file)
        except SmartChainKeyError:
            self.block_valid(block_index, public_key, time_of_validation, block)
        except:
            while True:
                traceback.print_exc()

    def return_blockchain(self):
        return self.chain



def read_nodes():
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        return json.load(file)


def validate_blockchain(block_index, ip, time_, block, chain):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    block = json.loads(block)
    for node_ in nodes:
        if node_["ip"] == ip:
            wallet = node_["pub_key"]
            print("CHECKING IF BLOCK IS VALID")
            chain.block_valid(block_index, wallet, time_, block)
            break



def get_wallet_val(pub_key, chain):
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


def tester(rate = 1):
    main_prv = input("PRIV: ")
    start_time = time.time()
    for _ in range(9000):
        #main_pub = os.environ["PUB_KEY"]
        time.sleep(1/rate)
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
            print(time.time()-start_time)
        else:
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
    for a in CHAIN:
        print(a)
    # print(CHAIN)
    # print(CHAIN.hash_block(CHAIN[-1]))
    # print(read_blockchain().send_blockchain())
    # print(len(CHAIN))
    CHAIN[-1][-1] = 3
    print(CHAIN)
    #print(CHAIN[-3][:2])
    #start = timer()
    #print(CHAIN.wallet_value("6efa5bfa8a9bfebaacacf9773f830939d8cb4a2129c1a2aaafaaf549"))
    #print(timer() - start)
    # print(CHAIN.block_sort(CHAIN[-1]))
