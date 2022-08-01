import os
import node
import receiver
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
    open(f"{os.path.dirname(__file__)}./recent_messages.txt", "w").close()#clear recent message file
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"MY IP: {local_ip}")
    #os.system("pip3 install --upgrade ecdsa")
    #local_ip = input("IP: ").replace(" ", "")
    """
    try:
        os.remove("install_decint.py")
        os.remove("install.exe")
    except:
        pass#wont work after first time ill come up with better way later
    """

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(receiver.rec)  # start recieving ✅
        executor.submit(node.updator).result() # update Blockchain & Nodes ✅ # .result() is used to wait for the thread to finish
        executor.submit(reader.read)
        executor.submit(trans_reader.read)
        executor.submit(validator.am_i_validator)
        executor.submit(pre_reader.read)


if __name__ == '__main__':
    run()










