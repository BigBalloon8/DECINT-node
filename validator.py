import time
import random
#  from numba import jit
import os
import json
import traceback
import blockchain
import copy

def hash_num(block_hash):
    num = int(block_hash, 16)
    return num



def rb(block_hash, block_time, time_validation=None, invalid=False):
    """
    the random biased function returns a random node based on the amount a node has stakes
    the random node is calculated using a seed
    the seed used is the hash of the block. this gives all nodes the same node that will be its validator
    """
    if time_validation == None:
        time_validation = time.time()
    while True:
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                nodes = json.load(file)
            break
        except json.decoder.JSONDecodeError:
            pass
    while True:
        try:
            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                stake_transactions = json.load(file)
            break
        except json.decoder.JSONDecodeError:
            pass

    node_weights = []  # random biased
    for node in nodes:
        public = node["pub_key"]
        ip = node["ip"]
        amount_staked = 0.0
        for _, stake_trans in stake_transactions:
            if isinstance(stake_trans, dict):
                if float(stake_trans["time"]) < block_time:

                    if stake_trans["pub_key"] == public:
                        if "stake_amount" in stake_trans:
                            amount_staked += stake_trans["stake_amount"]
                        if "unstake_amount" in stake_trans:
                            amount_staked -= stake_trans["unstake_amount"]

            elif isinstance(stake_trans, str):
                if (public in stake_trans or ip in stake_trans) and "LIAR" in stake_trans:
                    amount_staked = 0.0
                    break

        #amount_staked = math.floor(amount_staked)
        node_weights.append(amount_staked)

    #print(node_weights)
    random.seed(hash_num(block_hash))
    time_since_complete = time_validation - block_time
    number_of_misses = int(time_since_complete//20)
    if number_of_misses > 100000:
        #print(number_of_misses)
        number_of_misses = 0
    #print("num misses: ", number_of_misses)
    rand_node = random.choices(nodes, weights=node_weights, k=(number_of_misses + 1))
    if not isinstance(rand_node, list):
        rand_node = [rand_node]
    if not invalid:
        return rand_node , time_validation
    return rand_node[-1], time_validation


def am_i_validator(chain_pipe):
    """
    Reads the Blockchain checking if blocks is going to be validated by your node

    # This problem with the current iteration is that it checks to see if valid blocks are valid or not. it may be
     possible to store a list of unvalid blocks in a json file
    """
    try:
        print("---VALIDATOR STARTED---")
        with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "r") as file:
            my_pub = file.read()
        validated_blocks = []
        while True:
            try:
                indexes = copy.copy(list(chain_pipe.chain.position_tracker.keys()))
                if len(indexes) != len(chain_pipe):  # during update of position_tracker
                    continue
                for i in indexes:
                    if len(chain_pipe[i]) <= 3:
                        continue
                    block_index = i
                    if isinstance(chain_pipe[i][-3], list):
                        if not chain_pipe[i][-1][0]:
                            if chain_pipe[i - 1][-1][0]:  # cant be on the line above
                                if (time.time() - float(chain_pipe[i][-3][1])) > 10.0:
                                    try:
                                        block_time = chain_pipe[i][1]["time"]
                                        block_hash = chain_pipe[i][0][0]
                                    except (IndexError, KeyError):
                                        continue
                                    if not isinstance(block_hash, str):
                                        continue
                                    nodes, time_of_valid = rb(block_hash, block_time)
                                    for node in nodes:
                                        if node["pub_key"] == my_pub and block_index not in validated_blocks:
                                            print(f"I AM VALIDATOR, B{block_index}")
                                            chain_pipe.validate(block_index, time_of_valid)
                                            validated_blocks.append(block_index)
            #except KeyError:  # caused by blockchain adding new block during chain[i][1]["time"]
                #continue
            except blockchain.SmartChainKeyError:
                traceback.print_exc()
                continue


    except:
        while True:
            time.sleep(1)
            traceback.print_exc()


if __name__ == '__main__':
    print(rb("c547877025c260fa5cad96072a16b51c85a99c01cc15058781a7a301ea5edcab", 1802.0))
    am_i_validator()