import time
import random
import pickle
import math
#from numba import jit
import blockchain
import os
import json

"""
check amount staked by node from that info
get current block hash seed 
"""


def hash_num(hash):
    num = int(hash,16)
    return num

#@jit(nopython=True)
def rb(hash, time):
    """
    the random biased function returns a random node based on the amount a node has stakes
    the random node is calculated using a seed
    the seed used is the hash of the block. this gives all nodes the same node that will be its validator
    """
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)

    with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
        stake_trans = json.load(file)

    rb = []  # random biased
    for node in nodes:
        public = node["pub_key"]
        ip = node["ip"]
        amount_staked = 0.0
        for stake_trans in stake_trans:
            if isinstance(stake_trans, dict):
                if float(stake_trans["time"]) < time:

                    if stake_trans["pub_key"] == public:
                        if "stake_amount" in stake_trans:
                            amount_staked += stake_trans["stake_amount"]
                        if "unstake_amount" in stake_trans:
                            amount_staked -= stake_trans["unstake_amount"]


            elif isinstance(stake_trans, str):
                if (public in stake_trans or ip in stake_trans) and "LIAR" in stake_trans:
                    amount_staked = 0.0
                    break

        amount_staked = math.floor(amount_staked)
        rb.append(amount_staked)

    random.seed(hash_num(hash))
    number_of_misses = math.ciel(300.0/time.time())
    rand_node = random.choices(nodes, weights=rb, k=(number_of_misses + 1))

    return rand_node[-1], time
    

def am_i_validator():
    """
    Reads the Blockchain checking if blocks is going to be validated by your node

    # This problem with the current iteration is that it checks to see if valid blocks are valid or not. a list of
      unvalid blocks
    """
    time.sleep(4)
    print("---VALIDATOR STARTED---")
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "r") as file:
        my_pub = file.read()
    while True:
        chain = blockchain.read_blockchain()
        chain = chain  # return actual chain not object
        block_index = 0
        for block in chain:  # not efficient as checking validated blocks
            if not block[-1][0]:
                if int(time.time() - float(chain[-1][1]["time"])) > 30:
                    block_time = block[-1][1]
                    hash = block[-3][0]
                    node,time_valid = rb(hash, block_time)

                    if node[-1][2] == my_pub:
                        chain = blockchain.read_blockchain()
                        chain.validate(block_index, time_valid)
            block_index += 1


