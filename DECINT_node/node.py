"""
node
"""
import hashlib
import socket
import random
import threading
import time
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import asyncio
import os
import json
import copy
import traceback
import multiprocessing

import DECINT_node.messages as messages

__version__ = "1.0"


class TimeOutList:
    def __init__(self):
        self.t_list = []
        self.times = []

    def timeout(self):
        removed = 0
        if len(self.t_list) == 0:
            return
        for i in range(len(self.t_list)):
            if time.time() - self.times[i - removed] > 10.0:
                self.t_list.pop(i - removed)
                self.times.pop(i - removed)
                removed += 1

    def __len__(self):
        return len(self.t_list)

    def append(self, value):
        self.t_list.append(value)
        self.times.append(time.time())

    def __setitem__(self, index, value):
        return self.t_list.__setitem__(index, value)

    def __getitem__(self, index):
        self.timeout()
        return self.t_list.__getitem__(index)

    def remove(self, value):
        self.times.pop(self.t_list.index(value))
        self.t_list.remove(value)

    def __iter__(self):
        self.timeout()
        for i in self.t_list:
            yield i

    def __delitem__(self, index):
        self.t_list.__delitem__(index)
        self.times.__delitem__(index)

    def insert(self, index, value):
        self.t_list.insert(index, value)
        self.times.insert(index, time.time())


class MessageManager:
    def __init__(self, req_queue, trans_queue, process_queue, thread_queue):
        self.long_messages = TimeOutList()
        self.req_queue = req_queue
        self.trans_queue = trans_queue
        self.process_queue = process_queue
        self.thread_queue = thread_queue

    @staticmethod
    def str_to_message(address, message: str, hint=None):
        if not hint:
            message = message.split(" ")
            hint = message[0]
        else:
            message = message.split(" ")
        #print("hint:", hint)
        if hint == "GET_NODES":
            m = messages.GetMessage(m_from=address,
                                    g_type=messages.GetType.NODES
                                    )
        elif hint == "BLOCKCHAIN?":
            m = messages.GetMessage(m_from=address,
                                    g_type=messages.GetType.BLOCKCHAIN
                                    )
        elif hint == "GET_STAKE_TRANS":
            m = messages.GetMessage(m_from=address,
                                    g_type=messages.GetType.STAKE_TRANS
                                    )
        elif hint == "TRANS":
            m = messages.TransMessage(m_from=address,
                                      t_time=float(message[1]),
                                      sender=message[2],
                                      receiver=message[3],
                                      amount=float(message[4]),
                                      signature=message[5]
                                      )
        elif hint == "STAKE":
            m = messages.StakeMessage(m_from=address,
                                      s_type=messages.StakeType.STAKE,
                                      t_time=float(message[1]),
                                      staker=message[2],
                                      amount=float(message[3]),
                                      signature=message[4]
                                      )
        elif hint == "UNSTAKE":
            m = messages.StakeMessage(m_from=address,
                                      s_type=messages.StakeType.UNSTAKE,
                                      t_time=float(message[1]),
                                      staker=message[2],
                                      amount=float(message[3]),
                                      signature=message[4]
                                      )

        elif hint == "NREQ":
            m = messages.NREQMessage(m_from=address,
                                     node_list=json.loads(message[1])
                                     )
        elif hint == "BREQ":
            m = messages.BREQMessage(m_from=address,
                                     chain=json.loads(message[1])
                                     )
        elif hint == "SREQ":
            m = messages.SREQMessage(m_from=address,
                                     stake_list=json.loads(message[1])
                                     )

        elif hint == "HELLO":
            m = messages.HelloMessage(m_from=address,
                                      h_time=float(message[1]),
                                      i_type=messages.InfoType.HELLO,
                                      wallet=message[2],
                                      port=int(message[3]),
                                      version=float(message[4]),
                                      node_type=message[5],
                                      signature=message[6]
                                      )

        elif hint == "UPDATE":
            m = messages.UpdateMessage(m_from=address,
                                       u_time=float(message[1]),
                                       i_type=messages.InfoType.UPDATE,
                                       old_wallet=message[2],
                                       new_wallet=message[3],
                                       port=int(message[4]),
                                       version=float(message[5]),
                                       signature=message[6]
                                       )

        elif hint == "DELETE":
            m = messages.DeleteMessage(m_from=address,
                                       d_time=float(message[1]),
                                       i_type=messages.InfoType.DELETE,
                                       wallet=message[2],
                                       signature=message[3]
                                       )

        elif hint == "VALID":
            m = messages.ValidMessage(m_from=address,
                                      b_idx=int(message[1]),
                                      v_time=float(message[2]),
                                      valid_transactions=json.loads(message[3])
                                      )
        elif hint == "ONLINE?":
            m = messages.OnlineMessage(m_from=address)

        elif hint == "ERROR":
            m = messages.ErrorMessage(m_from=address,
                                      error=message[1]
                                      )
        else:
            # TODO Im being lazy fix this
            print(message)
            m = messages.Message

        return m

    def write(self, address, message_):
        # print(f"Message from {address} , {message_}\n")
        if "DIST" in message_:
            message = f"{address[0]} {message_}".split(" ")
            while True:
                try:
                    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                        nodes = json.load(file)
                    break
                except json.decoder.JSONDecodeError:  # somtimes clashes with other threads running the same function
                    continue

            dist_nodes = [node_ for node_ in nodes if node_["node_type"] == "dist"]

            try:
                message_handler(message[2:])
            except NodeError as e:
                print([message], e)
                send(message[0], f"ERROR {e}")
            except NotCompleteError:
                return

            dist_node = False
            for node_ in dist_nodes:
                if node_["ip"] == message[0]:
                    dist_node = True
                    break

            if dist_node:
                message.pop(0)
                message.pop(0)
                self.trans_queue.put(self.str_to_message(message[0], " ".join(message[1:])))

        else:
            #if (" " not in message_ and "ONLINE?" not in message_ and "BLOCKCHAIN?" not in message_ and "GET_NODES" not in message_ and "GET_STAKE_TRANS" not in message_) or "VALID" in message_ or "BREQ" in message_ or "SREQ" in message_ or "NREQ" in message_:  # TODO clean this up
            if "#" in message_ or "VALID" in message_ or "REQ" in message_:
                self.long_messages.append((address[0], message_))
            else:
                message = f"{address[0]} {message_}".split(" ")

                try:
                    message_handler(message)
                except NodeError as e:
                    print([message], e)
                    send(message[0], f"ERROR {e}")
                except NotCompleteError:
                    return

                if "BLOCKCHAIN?" in message:
                    self.thread_queue.put(self.str_to_message(address[0], message_))
                else:
                    self.process_queue.put(self.str_to_message(address[0], message_))

        for i in self.long_messages:
            if i[1][-67:-64] == "END":
                print("FOUND LONG MESSAGE "*5)
                if "#" in i[1]:  # valid messages are sent with # to prevent clashing with _REQ messages
                    complete_message = [k for k in self.long_messages.t_list if "#" in k[1] and i[0] == k[0]]
                    if message_hash("".join([k[1].replace("#", "") for k in complete_message])[:-67]) == i[1][-64:]:
                        long_write_lines = ''.join([j[1].replace("#", "") for j in complete_message])
                    else:
                        continue

                else:
                    complete_message = [k for k in self.long_messages.t_list if "#" not in k[1] and i[0] == k[0]]
                    if message_hash(" ".join([k[1] for k in complete_message])[:-67]) == i[1][-64:]:
                        long_write_lines = ''.join([j[1] for j in complete_message])
                    else:
                        continue

                message = f"{i[0]} {long_write_lines[:-67]}".split(" ")  # [:-4] is to remove END

                try:
                    message_handler(message)
                except NodeError as e:
                    print([message], e)
                    send(message[0], f"ERROR {e}")
                except NotCompleteError:
                    return

                if "VALID" in message:
                    print("long valid message found")
                    self.thread_queue.put(self.str_to_message(i[0], long_write_lines[:-67]))

                elif "BREQ" in message or "SREQ" in message or "NREQ" in message:
                    self.req_queue.put(self.str_to_message(i[0], long_write_lines[:-67]))

                for m in complete_message:
                    self.long_messages.remove(m)


def message_manager_process(message_manager: MessageManager, message_pipeline):
    while True:
        message_manager.write(*message_pipeline.recv())


# recieve from nodes
def receive(req_queue, trans_queue, process_queue, thread_queue):
    """
    message is split into array the first value the type of message the second value is the message
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", 1379))
    server.listen()
    message_handle = MessageManager(req_queue, trans_queue, process_queue, thread_queue)
    receive_pipe, send_pipe = multiprocessing.Pipe()
    p = multiprocessing.Process(target=message_manager_process, args=(message_handle, receive_pipe))
    p.start()
    while True:
        try:
            client, address = server.accept()
            message = client.recv(2 ** 16).decode("utf-8")  # .split(" ")
            send_pipe.send((address, message))
        except Exception as e:
            traceback.print_exc()


def receive_with_thread(req_queue, trans_queue, process_queue, thread_queue):  # allows proccess to be closed properly
    """
    message is split into array the first value the type of message the second value is the message
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", 1379))
    server.listen()
    message_handle = MessageManager(req_queue, trans_queue, process_queue, thread_queue)
    receive_pipe, send_pipe = multiprocessing.Pipe()
    p = threading.Thread(target=message_manager_process, args=(message_handle, receive_pipe))
    p.start()
    while True:
        try:
            client, address = server.accept()
            message = client.recv(2 ** 16).decode("utf-8")  # .split(" ")
            send_pipe.send((address, message))
        except Exception as e:
            traceback.print_exc()


# send to node
def send(host, message, port=1379, send_all=False):
    """
    sends a message to the given host
    tries the default port and if it doesn't work search for actual port
    this process is skipped if send to all for speed
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((host, port))
        client.sendall(message.encode("utf-8"))
        print(f"Message to {host} {message}\n")
    except ConnectionRefusedError:
        if send_all:
            return
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                nodes = json.load(file)
            for node in nodes:
                if node["ip"] == host:
                    if not int(node["port"]) == 1379:
                        client.connect((host, int(node["port"])))
                        client.sendall(message.encode("utf-8"))
                        print(f"Message to {host} {message}\n")
        except ConnectionRefusedError:
            return "node offline"
    client.close()


async def async_send(host, message, port=1379, send_all=False):
    """
    sends a message to the given host
    tries the default port and if it doesn't work search for actual port
    this process is skipped if send to all for speed
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        client.sendall(message.encode("utf-8"))
        print(f"Message to {host} {message}\n")
    except ConnectionError:
        if not send_all:
            try:
                with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                    nodes = json.load(file)
                for node in nodes:
                    if node[1] == host:
                        if not int(node["port"]) == 1379:
                            client.connect((host, int(node["port"])))
                            client.sendall(message.encode("utf-8"))
                            print(f"Message to {host} {message}\n")
            except ConnectionError:
                return "node offline"

    client.close()


# check if nodes online
def online(address):
    try:
        send(address, "ONLINE?")  # TODO add a way to timeout
        return True
    except TimeoutError:
        return False


def send_to_dist(message):
    """
    sends to all nodes
    """
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        all_nodes = json.load(file)
    dist_nodes = [node for node in all_nodes if node["node_type"] == "dist"]
    d_node = random.choice(dist_nodes)
    send(d_node["ip"], message)


def rand_act_node(num_nodes=1, type_=None):
    """
    returns a list of random active nodes which is x length
    """
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "r") as file:
        key = file.read()
    nodes = []
    i = 0
    while i != num_nodes:  # turn into for loop
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
            all_nodes = json.load(file)
        if type_:
            all_nodes = [node for node in all_nodes if node["node_type"] == type_]
        me = socket.gethostbyname(socket.gethostname())
        node_index = random.randint(0, len(all_nodes) - 1)
        node = all_nodes[node_index]
        # print(node)
        if node["pub_key"] == key or node["ip"] == me:
            continue
        alive = online(node["ip"])
        if alive:
            nodes.append(node)
            i += 1

    if len(nodes) == 1:
        return nodes[0]
    return nodes


def line_remover(del_lines, file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    new_lines = [line for line in lines if line.strip("\n") not in del_lines]
    open(file_path, "w").close()
    with open(file_path, "a") as file:
        for line in new_lines:
            file.write(line)


async def send_to_all(message, no_dist=False):
    """
    sends to all nodes
    """
    while True:
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                all_nodes = json.load(file)
                break
        except json.decoder.JSONDecodeError:
            pass
    if no_dist:
        all_nodes = [i for i in all_nodes if i["node_type"] != "dist"]
    for _ in asyncio.as_completed(
            [async_send(node["ip"], message, port=node["port"], send_all=True) for node in all_nodes]):
        await _


def announce(pub_key, port, version_, node_type, priv_key):
    announcement_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(announcement_time.encode()).hex())
    asyncio.run(send_to_all(f"HELLO {announcement_time} {pub_key} {port} {version_} {node_type} {sig}"))


def update(old_key, port, version_, priv_key, new_key=None):
    if not new_key:
        new_key = old_key
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    asyncio.run(send_to_all(f"UPDATE {update_time} {old_key} {new_key} {port} {version_} {sig}"))
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "w") as file:
        file.write(new_key)


def delete(pub_key, priv_key):
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    asyncio.run(send_to_all(f"DELETE {update_time} {pub_key} {sig}"))


def stake(priv_key, amount):
    priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    pub_key = priv_key.verifying_key
    stake_time = time.time()
    sig = priv_key.sign(("STAKE " + str(stake_time)).encode())
    send_to_dist(f"STAKE {stake_time} {pub_key} {amount} {sig}")


def unstake(priv_key, amount):
    priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    pub_key = priv_key.verifying_key
    stake_time = time.time()
    sig = priv_key.sign(("UNSTAKE " + str(stake_time)).encode())
    send_to_dist(f"UNSTAKE {stake_time} {pub_key} {amount} {sig}")


def updator(chain, queue):  # send ask the website for Blockchain as most up to date
    nodes = []
    nodes = get_nodes(nodes, queue)
    nodes = get_blockchain(chain, nodes, queue)
    get_stake_trans(nodes, queue)


def get_blockchain(chain, nodes, queue):
    print("---GETTING BLOCKCHAIN---")
    pre_nodes = copy.copy(nodes)
    while True:
        node = rand_act_node(type_="Blockchain")
        if node in nodes:
            break  # TODO remoev all these breaks for testing
            continue
        else:
            break
    time.sleep(1)
    send(node["ip"], "BLOCKCHAIN?")
    tries = 0
    while True:
        if tries == 10:
            get_blockchain(chain, pre_nodes, queue)
            return
        time.sleep(1)
        line: messages.BREQMessage = queue.get()
        if line:
            if line.m_from == node["ip"]:
                new_chain_1 = line.chain
                print(f"---BLOCKCHAIN NODE 1 RECEIVED---")
                break
        else:
            tries += 1
    time.sleep(1)
    nodes.append(node)
    while True:
        node = rand_act_node(type_="Blockchain")
        if node in nodes:
            break
            continue
        else:
            break
    time.sleep(0.1)
    send(node["ip"], "BLOCKCHAIN?")
    tries = 0
    while True:
        if tries == 10:
            get_blockchain(chain, pre_nodes, queue)
            return
        time.sleep(1)
        line = queue.get()
        if line:
            if line.m_from == node["ip"]:
                new_chain_2 = line.chain
                print(f"---BLOCKCHAIN NODE 2 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    check = chain.update(new_chain_1, new_chain_2)
    if not check:
        return get_blockchain(chain, pre_nodes, queue)
    return nodes


def get_stake_trans(nodes, queue):
    print("---GETTING STAKE TRANS---")
    pre_nodes = copy.copy(nodes)
    while True:
        node = rand_act_node(type_="Blockchain")
        if node in nodes:
            break
            continue
        else:
            break
    send(node["ip"], "GET_STAKE_TRANS")
    tries = 0
    while True:
        if tries == 10:
            return get_stake_trans(pre_nodes, queue)
        time.sleep(1)
        line: messages.SREQMessage = queue.get()
        if line:
            if line.m_from == node["ip"]:
                stake_trans_1 = line.stake_list
                print("---STAKE TRANS 1 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    while True:
        node = rand_act_node(type_="Blockchain")
        if node in nodes:
            break
            continue
        else:
            break
    send(node["ip"], "GET_STAKE_TRANS")
    tries = 0
    while True:
        if tries == 10:
            return get_stake_trans(pre_nodes, queue)
        time.sleep(1)
        line = queue.get()
        if line:
            if line.m_from == node["ip"]:
                stake_trans_2 = line.stake_list
                print("---STAKE TRANS 2 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    if stake_trans_1 == stake_trans_2:
        with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "w") as file:
            json.dump(stake_trans_1, file)
        print("---STAKE TRANS UPDATED---")
        return nodes
    return get_stake_trans(pre_nodes, queue)


def get_nodes(nodes, queue):
    print("---GETTING NODES---")
    pre_nodes = copy.copy(nodes)
    while True:
        node = rand_act_node()
        if node in nodes:
            break
            continue
        else:
            break
    time.sleep(0.1)
    send(node["ip"], "GET_NODES")
    tries = 0
    while True:
        if tries == 10:
            return get_nodes(pre_nodes, queue)
        time.sleep(1)
        line: messages.NREQMessage = queue.get()
        if line:
            if line.m_from == node["ip"]:
                nodes_1 = line.node_list
                print("---NODES 1 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    while True:
        node = rand_act_node()
        if node in nodes:
            break
            continue
        else:
            break
    time.sleep(0.1)
    send(node["ip"], "GET_NODES")
    tries = 0
    while True:
        if tries == 10:
            return get_nodes(pre_nodes, queue)
        time.sleep(1)
        line: messages.NREQMessage = queue.get()
        if line:
            if line.m_from == node["ip"]:
                nodes_2 = line.node_list
                print("---NODES 2 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    if nodes_1 == nodes_2:
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes_1, file)
        print("---NODES UPDATED---")
        return nodes
    return get_nodes(pre_nodes, queue)


def new_node(initiation_time, ip, pub_key, port, node_version, node_type):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    new_node_ = {"time": initiation_time, "ip": ip, "pub_key": pub_key, "port": port, "version": node_version,
                 "node_type": node_type}
    for node in nodes:
        if node["pub_key"] == pub_key:
            return
        if node["ip"] == ip:
            return
    nodes.append(new_node_)
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
        json.dump(nodes, file)
    print("---NODE ADDED---")


def update_node(ip, new_key, port, node_version):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    for node in nodes:
        if node["ip"] == ip:
            node["pub_key"] = new_key
            node["port"] = port
            node["version"] = node_version
    with open(f"{os.path.dirname(__file__)}./info/nodes.json", "w") as file:
        json.dump(nodes, file)
        print("NODE UPDATED")


def delete_node(deletion_time, ip, pub_key):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    if time.time() - float(deletion_time) < 30:
        for node in nodes:
            if node["ip"] == ip and node["pub_key"] == pub_key:
                nodes.remove(node)
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes, file)


def version():
    asyncio.run(send_to_all(f"VERSION {__version__}"))


def version_update(ip, ver):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    for nod in nodes:
        if nod["ip"] == ip:
            nod["version"] = ver
            break


def message_hash(message):
    return hashlib.sha256(message.encode()).hexdigest()


class NotCompleteError(Exception):
    """
    Raised when problem with line but the line is needed to be kept in recent messages
    """
    pass


class NodeError(Exception):
    pass


class UnrecognisedCommand(NodeError):
    pass


class ValueTypeError(NodeError):
    pass


class UnrecognisedArg(NodeError):
    pass


def check_float(value):
    try:
        float(value)
        if float(value) < 0:
            raise ValueTypeError
        if value.isdigit():
            raise ValueTypeError
        return True
    except ValueError:
        return False


def check_int(value):
    if value.isdigit():
        return True
    return False


#  TODO add AI_JOB protocols
def message_handler(message):
    """
    All messages are in the form of "<ip> PROTOCOL <args...>"

    HELLO <ip> <port> <pub_key> <version> <node_type> <signature>
    UPDATE <ip> <update_time> <old_key> <new_key> <port> <version> <signature>
    DELETE <ip> <deletion_time> <public_key> <signature>
    GET_NODES <ip>
    NREQ <ip> <nodes>
    BLOCKCHAIN? <ip>
    BREQ <ip> <blockchain>
    VALID <ip> <block_index> <validation_time> <block>
    TRANS <ip> <transaction_time> <sender_public_key> <recipient_public_key> <transaction_value> <signature>
    STAKE <ip> <staking_time> <public_key> <stake_value> <signature>
    UNSTAKE <ip> <unstaking_time> <public_key> <unstake_value> <signature>
    ONLINE? <ip>
    ERROR <ip> <error_message>
    """
    len_1_messages = ["ONLINE?", "BLOCKCHAIN?", "GET_NODES", "BLOCKCHAINLEN?", "GET_STAKE_TRANS"]
    if len(message) == 2:
        if message[1] not in len_1_messages:
            raise UnrecognisedArg("No Protocol Found")
    if len(message) < 2:
        raise UnrecognisedArg("number of args given incorrect")
    protocol = message[1]

    node_types = ["Lite", "Blockchain", "AI", "dist"]

    if protocol == "GET_NODES":
        if len(message) != 2:
            raise UnrecognisedArg(f"number of args given incorrect during {protocol}")

    elif protocol == "HELLO":
        # host, HELLO, announcement_time, public key, port, version, node type, sig
        if len(message) != 8:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        if not check_int(message[4]):
            raise ValueTypeError("port not given as int")
        else:
            port = int(message[4])

        if not port > 0 and port < 65535:
            raise ValueTypeError("TCP port out of range")

        if not check_float(message[5]):
            raise ValueTypeError("version not given as float")

        if message[6] not in node_types:
            raise UnrecognisedArg("Node Type Unknown")

        if len(message[7]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "VALID":
        # host, VALID , block index, time of validation, block
        if len(message) != 5:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_int(message[2]):
            raise ValueTypeError("Block Index not given as int")

        if not check_float(message[3]):
            raise ValueTypeError("time not given as float")

        try:
            if not isinstance(json.loads(message[4]), list):
                raise ValueTypeError("Blockchain not given as Blockchain")
        except json.decoder.JSONDecodeError:
            raise NotCompleteError("Blockchain not complete yet")

    elif protocol == "ONLINE?":
        # host, ONLINE?
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")

    elif protocol == "BLOCKCHAIN?":
        # host, BLOCKCHAIN?
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")

    elif protocol == "GET_STAKE_TRANS":
        # host, GET_STAKE_TRANS
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")

    elif protocol == "UPDATE":
        # host, UPDATE, update time, old public key, new public key, port, version, sig
        if len(message) != 7:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Old Public Key is the wrong size")

        if len(message[4]) != 56:
            raise UnrecognisedArg("New Public Key is the wrong size")

        if not check_int(message[5]):
            raise ValueTypeError("port not given as int")
        else:
            port = int(message[5])

        if not port >= 0 and port < 65535:
            raise ValueTypeError("TCP port out of range")

        if not check_float(message[6]):
            raise ValueTypeError("version not given as float")

        if len(message[7]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "DELETE":
        # host, DELETE, time, public key, sig
        if len(message) != 5:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        if len(message[4]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "BREQ":
        # host, BREQ, blockchain
        try:
            if not isinstance(json.loads(message[2]), list):
                raise ValueTypeError("Blockchain not given as Blockchain")
        except json.decoder.JSONDecodeError:
            raise NotCompleteError("Blockchain not complete yet")

    elif protocol == "SREQ":
        try:
            if not isinstance(json.loads(message[2]), list):
                raise ValueTypeError("Blockchain not given as Blockchain")
        except json.decoder.JSONDecodeError:
            raise NotCompleteError("Blockchain not complete yet")

    elif protocol == "NREQ":
        # host, NREQ, nodes
        try:
            if not isinstance(json.loads(message[2]), list):
                raise ValueTypeError("Blockchain not given as Blockchain")
        except json.decoder.JSONDecodeError:
            raise NotCompleteError("Blockchain not complete yet")

    elif protocol == "TRANS":
        # host, TRANS, time of transaction, sender public key, receiver public key, amount sent, sig
        if len(message) != 7:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Senders Public Key is the wrong size")

        if len(message[4]) != 56:
            raise UnrecognisedArg("Receivers Public Key is the wrong size")

        if not check_float(message[5]):
            raise ValueTypeError("Amount not given as float")

        if len(message[6]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "ERROR":
        pass

    elif protocol == "yh":
        pass

    elif protocol == "STAKE":
        # host, STAKE, time of stake, public key, amount, sig
        if len(message) != 6:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        if not check_float(message[4]):
            raise ValueTypeError("Stake value not given as float")

        if len(message[5]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "UNSTAKE":
        if len(message) != 6:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_float(message[2]):
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        if not check_float(message[4]):
            raise ValueTypeError("Unstake value not given as float")

        if len(message[5]) != 56:
            raise UnrecognisedArg("Signature is the wrong size")

    elif protocol == "BLOCKCHAINLEN?":
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")

    elif protocol == "BLENREQ":
        if len(message) != 3:
            raise UnrecognisedArg("number of args given incorrect")

        if not check_int(message[2]):
            raise ValueTypeError("Blockchain length not given as int")

    elif len(message) == 2:  # will have to be part of a large message
        pass

    else:
        raise UnrecognisedCommand("protocol unrecognised")


if __name__ == '__main__':
    pass
