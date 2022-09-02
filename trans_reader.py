import node
import time
from ecdsa import VerifyingKey, SECP112r2
import copy
import blockchain
import ast
import requests
import os
import traceback
import json
def AI_handler():
    pass

def trans_handler(line):
    #print(line)
    line = line.split(" ")
    trans = {"time": float(line[2]), "sender": line[3], "receiver": line[4], "amount": float(line[5]), "sig": line[6]}
    trans_no_sig = copy.copy(trans)
    trans_no_sig.pop("sig")  # left with trans without sig
    trans_no_sig = " ".join(map(str, list(trans_no_sig.values())))
    public_key = VerifyingKey.from_string(bytes.fromhex(trans["sender"]), curve=SECP112r2)
    if not public_key.verify(bytes.fromhex(trans["sig"]), trans_no_sig.encode()):
        return
    chain = blockchain.read_blockchain()
    if trans in chain[-1] or trans in chain[-2]:
        return
    if not trans["amount"] > 0.0:
        return

    if float(trans["time"]) > (time.time() - 20.0):  # was announced in the last 30 seconds
        if not float(trans["time"]) > time.time():  # not from the future
            chain.add_transaction(trans)
            #blockchain.write_blockchain(chain)

def AI_job_handler(line):
    line = line.split(" ")
    nodes = ast.literal_eval(line[3])
    nodes_info = []
    for AI_node in nodes:
        nodes_info.append({"ip": AI_node["ip"], "wallet": AI_node["pub_key"], "work_done": 0.0})  #  announce work done to update later
    job_announce = {"time": float(line[2]), "script_identity": float(line[4]), "nodes": nodes_info}
    r = requests.get(f"https://decint.com/si/{line[4]}")
    if r.status_code == 404:
        return
    chain = blockchain.read_blockchain()
    if job_announce in chain[-1] or job_announce in chain[-2]:
        return
    if job_announce["time"] > (time.time() - 20.0):  # was announced in the last 30 seconds
        if not job_announce["time"] > time.time():  # not from the future
            chain.add_protocol(job_announce)
            #blockchain.write_blockchain(chain)

def staking_handler(line):
    line = line.split(" ")
    if "STAKE" == line[1]:
        stake_trans = {"time": float(line[2]), "pub_key": line[3], "stake_amount": float(line[4]), "sig": line[5]}
    elif "UNSTAKE" == line[1]:
        stake_trans = {"time": float(line[2]), "pub_key": line[3], "unstake_amount": float(line[4]), "sig": line[5]}
    #print(bytes.fromhex(stake_trans["pub_key"]))
    public_key = VerifyingKey.from_string(bytes.fromhex(stake_trans["pub_key"]), curve=SECP112r2)
    if not public_key.verify(bytes.fromhex(stake_trans["sig"]), str(stake_trans["time"]).encode()):
        return
    chain = blockchain.read_blockchain()
    if stake_trans in chain[-1] or stake_trans in chain[-2]:
        return
    try:
        if not stake_trans["stake_amount"] > 0.0:
            return
    except KeyError:
        if not stake_trans["unstake_amount"] > 0.0:
            return
    if stake_trans["time"] > (time.time()-20.0):
        if not stake_trans["time"] > time.time():
            chain.add_protocol(stake_trans)
            #blockchain.write_blockchain(chain)



def AI_reward_handler(line):
    pass


def read():
    #time.sleep(20)
    print("---TRANSACTION READER STARTED---")
    while True:
        try:
            trans_lines = node.dist_request_reader()
            if trans_lines:
                print(f"TRANS LINES: {trans_lines}")
                for trans_line in trans_lines:
                    if "TRANS" in trans_line:
                        trans_handler(trans_line)
                        #  TODO add trans error handler
                    elif "AI_JOB" in trans_line:
                        AI_job_handler(trans_line)
                    elif "STAKE" in trans_line or "UNSTAKE" in trans_line:
                        staking_handler(trans_line)
                    elif "AI_REWARD" in trans_line:
                        AI_job_handler(trans_line)
        except Exception:
            while True:
                traceback.print_exc()
            pass  # unable to find there error but for some reason the for loop break and I don't know why



if __name__ == "__main__":
    print("/".join((__file__.split("/"))[:-1]))
    read()
