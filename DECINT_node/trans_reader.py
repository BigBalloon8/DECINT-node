import time
from ecdsa import VerifyingKey, SECP112r2
import copy
import ast
import requests
import traceback
from DECINT_node import threaded_reader
from DECINT_node.messages import TransMessage, StakeMessage


def AI_handler():
    pass


def trans_handler(line: TransMessage, chain):
    # print(line)
    trans = {"time": line.t_time,
             "sender": line.sender,
             "receiver": line.receiver,
             "amount": line.amount,
             "sig": line.signature
             }

    if not line.check_sig():
        return
    if trans in chain[-1] or trans in chain[-2]:
        return
    if trans["amount"] <= 0.0:
        return

    if float(trans["time"]) > (time.time() - 5.0):  # was announced in the last 5 seconds
        if not float(trans["time"]) > time.time():  # not from the future
            chain.add_transaction(trans)
            # blockchain.write_blockchain(chain)


def AI_job_handler(line, chain):
    line = line.split(" ")
    nodes = ast.literal_eval(line[3])
    nodes_info = []
    for AI_node in nodes:
        nodes_info.append(
            {"ip": AI_node["ip"], "wallet": AI_node["pub_key"], "work_done": 0.0})  # announce work done to update later
    job_announce = {"time": float(line[2]), "script_identity": float(line[4]), "nodes": nodes_info}
    r = requests.get(f"https://decint.com/si/{line[4]}")
    if r.status_code == 404:
        return
    if job_announce in chain[-1] or job_announce in chain[-2]:
        return
    if job_announce["time"] > (time.time() - 5.0):  # was announced in the last 5 seconds
        if not job_announce["time"] > time.time():  # not from the future
            chain.add_protocol(job_announce)
            # blockchain.write_blockchain(chain)


def staking_handler(line: StakeMessage, chain):
    if line.s_type.name == "STAKE":
        stake_trans = {"time": line.t_time,
                       "pub_key": line.staker,
                       "stake_amount": line.amount,
                       "sig": line.signature
                       }
    elif line.s_type.name == "UNSTAKE":
        stake_trans = {"time": line.t_time,
                       "pub_key": line.staker,
                       "unstake_amount": line.amount,
                       "sig": line.signature
                       }

    if not line.check_sig():
        return
    if stake_trans in chain[-1] or stake_trans in chain[-2]:
        return
    if line.amount < 0.0:
        return
    if stake_trans["time"] > (time.time() - 5.0):  # how late a message can be
        if not stake_trans["time"] > time.time():
            chain.add_protocol(stake_trans)
            # blockchain.write_blockchain(chain)


def AI_reward_handler(line):
    pass


def read(chain, trans_queue, thread_queue):
    print("---TRANSACTION READER STARTED---")
    print("---THREADED READER STARTED---")
    while True:
        try:
            threaded_reader.read(chain, thread_queue)
            if not trans_queue.empty():
                trans_line = trans_queue.get()
                if trans_line:
                    if trans_line.m_cat.name == "TRANSACTION":
                        if hasattr(trans_line, "staker"):
                            staking_handler(trans_line, chain)
                        elif hasattr(trans_line, "receiver"):
                            trans_handler(trans_line, chain)
                    """
                    if "AI_JOB" in trans_line:
                        AI_job_handler(trans_line, chain)
                        
                    elif "AI_REWARD" in trans_line:
                        AI_job_handler(trans_line, chain)
                    """

        except Exception:
            while True:
                traceback.print_exc()
            pass  # unable to find there error but for some reason the for loop break and I don't know why


if __name__ == "__main__":
    print("/".join((__file__.split("/"))[:-1]))
    read()
