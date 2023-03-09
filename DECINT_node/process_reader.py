from DECINT_node import node
from DECINT_node.messages import HelloMessage, DeleteMessage, UpdateMessage, OnlineMessage, GetMessage

import traceback
import json
import textwrap
import os
import time
from typing import Union


def read(queue):
    print("---PROCESS READER STARTED---")
    try:
        while True:
            if not queue.empty():
                message: Union[HelloMessage, UpdateMessage, DeleteMessage, OnlineMessage, GetMessage]
                message = queue.get()
                if message:

                    if message.m_cat.name == "NODE_INFO":
                        if message.check_sig():
                            if message.i_type.name == "HELLO":
                                node.new_node(initiation_time=message.h_time,
                                              ip=message.m_from,
                                              pub_key=message.wallet,
                                              port=message.port,
                                              node_version=message.version,
                                              node_type=message.node_type,
                                              )

                            elif message.i_type.name == "UPDATE":
                                node.update_node(ip=message.m_from,
                                                 new_key=message.new_wallet,
                                                 port=message.port,
                                                 node_version=message.version,
                                                 )

                            elif message.i_type.name == "DELETE":
                                node.delete_node(deletion_time=message.d_time,
                                                 ip=message.m_from,
                                                 pub_key=message.wallet,
                                                 )

                    elif message.m_cat.name == "MISCELLANEOUS":
                        pass

                    elif message.m_cat.name == "GET":
                        if message.g_type.name == "NODES":
                            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                                nodes = json.load(file)
                            str_node = json.dumps(nodes).replace(" ", "")
                            message_hash = node.message_hash("NREQ " + str_node)
                            messages = textwrap.wrap("NREQ " + str_node, 5000)
                            for message_ in messages[:-1]:
                                node.send(message.m_from, message_)
                            node.send(message.m_from, messages[-1] + "END" + message_hash)

                        elif message.g_type.name == "STAKE_TRANS":
                            with open(f"{os.path.dirname(__file__)}/info/stake_trans.json", "r") as file:
                                stake_trans = json.load(file)
                            temp_message = "SREQ " + json.dumps(stake_trans).replace(" ", "")
                            messages = textwrap.wrap(temp_message, 5000)
                            message_hash = node.message_hash(temp_message)
                            for message_ in messages[:-1]:
                                node.send(message.m_from, message_)
                            node.send(message.m_from, messages[-1] + "END" + message_hash)

    except:
        while True:
            time.sleep(0.5)
            traceback.print_exc()


if __name__ == "__main__":
    read()
