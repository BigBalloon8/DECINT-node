"""
node
"""
import socket
import random
import time
import ast
import blockchain
import time
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import asyncio
import os
import json
from threading import Thread
import copy
import traceback



__version__ = "1.0"


# recieve from nodes
def receive():
    """
    message is split into array the first value the type of message the second value is the message
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", 1379))
    server.listen()
    message_handle = MessageManager()
    while True:
        try:
            client, address = server.accept()
            message = client.recv(2 ** 16).decode("utf-8")  # .split(" ")
            if "\n" in message:
                continue
            print(f"Message from {address} , {message}\n")
            message_handle.write(address, message)
            continue
        except Exception as e:
            traceback.print_exc()


class TimeOutList(): #TODO test in working simulation
    def __init__(self):
        self.t_list = []
        self.times = []

    def timeout(self):
        removed = 0
        if len(self.t_list) == 0:
            return
        for i in range(len(self.t_list)):
            if time.time()-self.times[i-removed] > 5.0:
                self.t_list.pop(i-removed)
                self.times.pop(i-removed)
                removed +=1

    def __len__(self):
        return len(self.t_list)

    def append(self, value):
        self.t_list.append(value)
        self.times.append(time.time())

    def __setitem__(self,index, value):
        return self.t_list.__setitem__(index,value)

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
    def __init__(self):
        self.long_messages = TimeOutList()

    def write(self, address, message):
        if "DIST" in message:
            with open(f"{os.path.dirname(__file__)}/dist_messages.txt", "a") as file:
                file.write(f"{address[0]} {message}\n")

        else:
            if (
                    " " not in message and "ONLINE?" not in message and "BLOCKCHAIN?" not in message and "GET_NODES" not in message  and "GET_STAKE_TRANS" not in message) or "VALID" in message or "BREQ" in message or "SREQ" in message or "NREQ" in message:  # TODO clean this up
                self.long_messages.append((address[0], message))

            else:
                with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "a+") as file:
                    file.write(f"{address[0]} {message}\n")

        for i in self.long_messages:
            if "]]" in i[1] or "]]]" in i[1] or "}]]" in i[1] or "}]" in i[1]:
                # if len([j for j in self.long_messages if j[0] == i[0]]) == len(self.long_messages):
                with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "a+") as file:
                    complete_message = [k for k in self.long_messages.t_list if k[0] == i[0]]
                    long_write_lines = ''.join([l[1] for l in complete_message])
                    file.write(f"{i[0]} {long_write_lines}\n")
                    #print(complete_message, "\n\n", self.long_messages.t_list)
                    for m in complete_message:
                        self.long_messages.remove(m)


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
        send(address, "ONLINE?") #TODO add a way to timeout
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


def dist_request_reader(type_="TRANS"):
    while True:
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                nodes = json.load(file)
            break
        except json.decoder.JSONDecodeError:  # somtimes clashes with other threads running the same function
            continue

    with open(f"{os.path.dirname(__file__)}/dist_messages.txt", "r") as file:
        lines = file.read().splitlines()
    dist_nodes = [node_ for node_ in nodes if node_["node_type"] == "dist"]

    trans_protocols = ["TRANS", "STAKE", "UNSTAKE", "AI_JOB_ANNOUNCE"]

    trans_lines = []
    left_over_lines = []

    trans_messages = []
    # left_over_messages = []

    for line in lines:
        message = line.split(" ")

        try:
            message_handler(message[2:])  # handle message without inputting dist and dist node address
        except NodeError as e:
            print([message], e)
            send(message[0], f"ERROR {e}")
            left_over_lines.append(line)
            continue
        except NotCompleteError as e:
            continue

        dist_node = False
        for node_ in dist_nodes:
            if node_["ip"] == message[0]:
                dist_node = True
                break

        if dist_node:
            message.pop(0)
            message.pop(0)

            if message[0] in ("", "\n"):
                lines.remove(" ".join(message))

            elif message[1] in trans_protocols:
                trans_lines.append(line)
                trans_messages.append(" ".join(message))


            else:
                left_over_lines.append(line)


    if type_ == "TRANS":
        if len(trans_messages) == 0:
            return trans_messages
        line_remover(trans_lines, f"{os.path.dirname(__file__)}/dist_messages.txt")
        return trans_messages

    elif type_ == "LEFT_OVER":
        line_remover(left_over_lines, f"{os.path.dirname(__file__)}/dist_messages.txt")


def request_reader(type_, ip="192.168.68.1"):
    """
    reads the recent messages and returns the message of the requested type
    """
    with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "r") as file:
        lines = file.read().splitlines()

    thread_protocols = ["VALID", "BLOCKCHAIN?"]

    process_lines = []
    thread_lines = []
    nreq_lines = []
    breq_lines = []
    sreq_lines = []
    del_lines = []
    if str(lines) != "[]":
        for line in lines:
            line = line.split(" ")
            try:
                message_handler(line)
            except NodeError as e:
                print("ERROR LINE: ", [" ".join(line)], e)
                send(" ".join(line), f"ERROR {e}")
                del_lines.append(" ".join(line))
                continue
            except NotCompleteError:
                continue

            if line[0] in ("", "\n"):
                lines.remove(" ".join(line))

            elif line[1] in thread_protocols:
                thread_lines.append(" ".join(line))

            elif line[1] == "NREQ":
                try:
                    ast.literal_eval(line[2])
                    nreq_lines.append(" ".join(line))
                except ValueError:
                    process_lines.append(" ".join(line))
                except IndexError:
                    process_lines.append(" ".join(line))
                except SyntaxError:
                    pass

            elif line[1] == "BREQ":
                try:
                    ast.literal_eval(line[2])
                    breq_lines.append(" ".join(line))
                except ValueError:
                    process_lines.append(" ".join(line))
                except IndexError:
                    process_lines.append(" ".join(line))
                except SyntaxError:
                    pass

            elif line[1] == "SREQ":
                try:
                    ast.literal_eval(line[2])
                    sreq_lines.append(" ".join(line))
                except ValueError:
                    process_lines.append(" ".join(line))
                except IndexError:
                    process_lines.append(" ".join(line))
                except SyntaxError:
                    pass

            else:
                try:
                    ast.literal_eval(line[4])
                    process_lines.append(" ".join(line))
                except ValueError:
                    process_lines.append(" ".join(line))
                except IndexError:
                    process_lines.append(" ".join(line))
                except SyntaxError:
                    pass

        if type_ == "NODE":
            if len(process_lines) == 0:
                return process_lines
            line_remover(process_lines + del_lines, f"{os.path.dirname(__file__)}/recent_messages.txt")
            return process_lines

        elif type_ == "NREQ":
            if len(nreq_lines) == 0:
                return nreq_lines
            line_remover(nreq_lines + del_lines, f"{os.path.dirname(__file__)}/recent_messages.txt")
            return nreq_lines

        elif type_ == "THREAD":
            if len(thread_lines) == 0:
                return thread_lines
            line_remover(thread_lines + del_lines, f"{os.path.dirname(__file__)}/recent_messages.txt")
            return thread_lines
        
        elif type_ == "BREQ":
            if len(breq_lines) == 0:
                return breq_lines
            line_remover(breq_lines + del_lines, f"{os.path.dirname(__file__)}/recent_messages.txt")
            return breq_lines

        elif type_ == "SREQ":
            if len(sreq_lines) == 0:
                return sreq_lines
            line_remover(sreq_lines + del_lines, f"{os.path.dirname(__file__)}/recent_messages.txt")
            return sreq_lines


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
        result = await _


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


def updator(chain):  # send ask the website for Blockchain as most up to date
    nodes = []
    nodes = get_nodes(nodes)
    nodes = get_blockchain(chain, nodes)
    get_stake_trans(nodes)


def get_blockchain(chain, nodes=[]):
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
            get_blockchain(chain, pre_nodes)
            return
        time.sleep(1)
        lines = request_reader("BREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                new_chain_1 = ast.literal_eval(line[2])
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
            get_blockchain(chain, pre_nodes)
            return
        time.sleep(1)
        lines = request_reader("BREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                new_chain_2 = ast.literal_eval(line[2])
                print(f"---BLOCKCHAIN NODE 2 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    check = chain.update(new_chain_1, new_chain_2)
    if not check:
        return get_blockchain(chain, pre_nodes)
    return nodes


def get_stake_trans(nodes=[]):
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
            return get_stake_trans(pre_nodes)
        time.sleep(1)
        lines = request_reader("SREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                stake_trans_1 = ast.literal_eval(line[2])
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
            return get_stake_trans(pre_nodes)
        time.sleep(1)
        lines = request_reader("SREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                stake_trans_2 = ast.literal_eval(line[2])
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
    return get_stake_trans(pre_nodes)


def get_nodes(nodes=[]):
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
            return get_nodes(pre_nodes)
        time.sleep(1)
        lines = request_reader("NREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                nodes_1 = ast.literal_eval(line[2])
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
            return get_nodes(pre_nodes)
        time.sleep(1)
        lines = request_reader("NREQ")
        if lines:
            line = lines[0].split(" ")
            if line[0] == node["ip"]:
                nodes_2 = ast.literal_eval(line[2])
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
    return get_nodes(pre_nodes)


def send_node(host):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    str_node = str(nodes)
    str_node = str_node.replace(" ", "")
    send(host, "NREQ " + str_node)


def new_node(initiation_time, ip, pub_key, port, node_version, node_type, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    if public_key.verify(bytes.fromhex(sig), str(initiation_time).encode()):
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
    else:
        return "node invalid"


def update_node(ip, update_time, old_key, new_key, port, node_version, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(old_key), curve=SECP112r2)
    if public_key.verify(bytes.fromhex(sig), str(update_time).encode()):
        for node in nodes:
            if node["ip"] == ip:
                node["pub_key"] = new_key
                node["port"] = port
                node["version"] = node_version
        with open(f"{os.path.dirname(__file__)}./info/nodes.json", "w") as file:
            json.dump(nodes, file)
            print("NODE UPDATED")
    else:
        return "update invalid"


def delete_node(deletion_time, ip, pub_key, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    if time.time() - float(deletion_time) < 60:
        public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
        if public_key.verify(bytes.fromhex(sig), str(deletion_time).encode()):
            for node in nodes:
                if node["ip"] == ip and node["pub_key"] == pub_key:
                    nodes.remove(node)
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
                json.dump(nodes, file)
        else:
            return "cancel invalid"


def version():
    asyncio.run(send_to_all(f"VERSION {__version__}"))


def version_update(ip, ver):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    for nod in nodes:
        if nod["ip"] == ip:
            nod["version"] = ver
            break


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
    BLOCKCHAINLEN? <ip>
    BLENREQ <ip> <number_of_chunks>
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
            ast.literal_eval(message[4])
        except ValueError:
            raise ValueTypeError("BLock is not given as block")
        except SyntaxError:
            raise NotCompleteError("block not complete")

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
            ast.literal_eval(message[2])
        except ValueError:
            raise ValueTypeError("Blockchain not given as Blockchain")
        except SyntaxError:
            raise NotCompleteError("Blockchain not complete yet")

    elif protocol == "SREQ":
        try:
            ast.literal_eval(message[2])
        except ValueError:
            raise ValueTypeError("Stake trans not given as Stake trans")
        except SyntaxError:
            raise NotCompleteError("Stake trans not complete yet")

    elif protocol == "NREQ":
        # host, NREQ, nodes
        try:
            ast.literal_eval(message[2])
        except ValueError:
            raise ValueTypeError("Nodes not given as Node List")
        except SyntaxError:
            raise NotCompleteError("NREQ list not complete yet")

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
    arr = TimeOutList()

    for i in (1,2,3,4,5,6):
        arr.append(i)
    time.sleep(1)
    print(arr.t_list)

    time.sleep(10)

    if arr:
        for i in arr:
            print([i])

    print(arr.t_list)
