import os

#os.system("pip3 install ecdsa objsize numba")

from DECINT_node import node
from DECINT_node import blockchain
"""
install dependencies
create folders
request nodes and Blockchain with
ask for wallet to use and how much to stake
announce self and time of creation
"""
def run():
    print("\nBy Using our product you except our Terms and Conditions")
    accept = input("To Accept type 'ACCEPT'  : ")
    if accept != "ACCEPT":
        exit()

    print("Your Private key is needed to verify that your public key belongs to you, make sure you are using the official version of decint")
    priv_key = input("Private Key: ")
    print("This is the the key that will be rewarded")
    pub_key = input("Public Key: ")
    print("Bellow insert Port that will be forwarded for communication (Leave Blank to Default)")
    norm_port = input("Port: ")
    if not norm_port:
        norm_port = "1379"

    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "w") as file:
        file.write(pub_key)


    print("That's you,\n"
          "make sure you are port forwarding BOTH PORTS!!!,\n"
          "run DECI.exe to start,\n"
          "if you want to change anything run this again.\n")

    node.announce(pub_key, norm_port, node.__version__, "Blockchain", priv_key)

def test_install():
    priv_key, hex_priv = blockchain.priv_key_gen()
    pub_key, hex_pub = blockchain.pub_key_gen(priv_key)
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "w") as file:
        file.write(hex_pub)
    with open(f"{os.path.dirname(__file__)}/info/priv_key_testing.txt", "w") as file:
        file.write(hex_priv)
    node.announce(hex_pub, "1379", node.__version__, "Blockchain", hex_priv)

if __name__ == '__main__':
    test_install()