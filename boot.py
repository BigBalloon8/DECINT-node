import os
import blockchain
import node
import reader
import trans_reader
import validator
import pre_reader
import concurrent.futures
import socket


"""
update tensorflow
update Blockchain and nodes
"""
def run():
    open(f"{os.path.dirname(__file__)}/recent_messages.txt", "w").close()#clear recent message file
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"MY IP: {local_ip}")
    #local_ip = input("IP: ").replace(" ", "")
    """
    try:
        os.remove("install_decint.py")
        os.remove("install.exe")
    except:
        pass#wont work after first time ill come up with better way later
    """
    chain = blockchain.Blockchain()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.submit(node.receive)  # start recieving ✅
        executor.submit(node.updator, chain).result() # update Blockchain & Nodes ✅ # .result() is used to wait for the thread to finish
        executor.submit(pre_reader.read, chain)
        executor.submit(reader.read, chain)
        executor.submit(trans_reader.read, chain)
        executor.submit(validator.am_i_validator, chain)



if __name__ == '__main__':
    run()










