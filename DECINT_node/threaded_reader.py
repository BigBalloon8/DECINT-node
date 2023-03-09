from DECINT_node import node
from DECINT_node import blockchain
from DECINT_node.messages import ValidMessage, GetMessage, Message

from typing import Union
import traceback
import json
import textwrap


def read(chain, queue):
    #ip = get('https://api.ipify.org').text
    try:
        if not queue.empty():
            message: Union[ValidMessage, GetMessage] = queue.get()
            #print(f"NODE LINES: {node_lines}\n")

            if message.m_cat.name == "BLOCKCHAIN":  # update block to true
                print("VALID")
                blockchain.validate_blockchain(block_index=message.b_idx,
                                               ip=message.m_from,
                                               time_=message.v_time,
                                               block=message.valid_transactions,
                                               chain=chain)

            elif message.m_cat.name == "GET" and message.g_type.name == "BLOCKCHAIN":
                send_chain = "BREQ " + json.dumps(chain.return_blockchain().present_chain).replace(" ", "")
                messages = textwrap.wrap(send_chain, 5000)
                message_hash = node.message_hash(send_chain)
                for message_ in messages[:-1]:
                    node.send(message.m_from, message_)
                node.send(message.m_from, messages[-1] + "END" + message_hash)

    except:
        import time
        while True:
            time.sleep(0.5)
            traceback.print_exc()



if __name__ == "__main__":
    read()
