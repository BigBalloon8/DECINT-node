import click
import install_decint
import node
import time
import blockchain
import pickle
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import boot
import os

@click.command()
@click.option("--install", "-i", is_flag=True, help="Will Install DecInt")
@click.option("--update", "-u", is_flag=True, help="Will send Update protocol to other nodes")
@click.option("--delete", "-d", is_flag=True, help="Will send Delete protocol to other nodes")
@click.option("--stake", "-s", is_flag=True, help="Will send a Stake request")
@click.option("--unstake", "-un", is_flag=True, help="Will send a Unstake request")
@click.option("--trans", "-t", is_flag=True, help="Will send a transaction")
@click.option("--run_node", "-r", is_flag=True, help="Will run node, you can also give no option to do the same thing")
def run(install, update, delete, stake, unstake, trans, run_node):

    if install:
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            key = file.read()
        if not key:
            install_decint.run()
        else:
            click.echo("DECINT is already installed (if DECINT is not installed run install_decint.py)\n")

    elif update:
        node.get_nodes_no_blockchain()
        click.prompt("In order to update your Node please enter a bit of information")
        time.sleep(2)
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            pub_key = file.read()
        click.echo("\nLeave Port blank to use default")
        port = click.prompt("Enter Port", default="1379")
        port = str(port)
        version = str(node.__version__)
        click.echo("\nNew Public Key is required if you are changing Keys, please use the old Enter Private Key when Prompted")
        new_key = click.prompt("Enter New Public Key")
        priv_key = click.prompt("Enter Private Key")
        node.update(pub_key, port, version, priv_key, new_key)

    elif delete:
        node.get_nodes_no_blockchain()
        click.prompt("In order to delete your Node please enter a bit of information")
        time.sleep(2)
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            pub_key = file.read()
        priv_key = click.prompt("Private Key", type=str)
        node.delete(pub_key, priv_key)

    elif stake:
        node.get_nodes_no_blockchain()
        priv_key = click.prompt("Private Key", type=str)
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            pub_key = file.read()
        click.echo("\nCalculating wallet value")
        val = blockchain.get_wallet_val(pub_key)
        while True:
            amount = click.prompt(f"How much would you like to Stake [Max {val}]", default=0.0, type=float)
            if amount <= val:
                break
            else:
                click.echo("\nInserted value is more than available")
        current_time = str(time.time())
        priv_key = VerifyingKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
        sig = str(priv_key.sign(current_time.encode()).hex())
        node.send_to_dist(f"STAKE {current_time} {pub_key} {amount} {sig}")

    elif unstake:
        node.get_nodes_no_blockchain()
        priv_key = click.prompt("Private Key", type=str)
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            pub_key = file.read()
        click.echo("\nCalculating amount your wallet has staked")
        val = 0.0
        with open(f"{os.path.dirname(__file__)}./info/stake_trans.pickle", "rb") as f:
            stake_transactions = pickle.load(f)
        for stake_trans in stake_transactions:
            if stake_trans["pub_key"] == pub_key and "stake_amount" in stake_trans:
                val += stake_trans["stake_amount"]
        while True:
            amount = click.prompt(f"How much would you like to Unstake [Max {val}]", default=0.0, type=float)
            if amount <= val:
                break
            else:
                click.echo("\nInserted value is more than available")
        current_time = str(time.time())
        priv_key = VerifyingKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
        sig = str(priv_key.sign(current_time.encode()).hex())
        node.send_to_dist(f"UNSTAKE {current_time} {pub_key} {amount} {sig}")

    elif trans:
        node.get_nodes_no_blockchain()
        priv_key = click.prompt("Private Key", type=str)
        with open(f"{os.path.dirname(__file__)}./info/Public_key.txt", "r") as file:
            pub_key = file.read()
        receiver = click.prompt("Receiver Public Key", type=str)
        click.echo("\nCalculating wallet value")
        val = blockchain.get_wallet_val(pub_key)
        while True:
            amount = click.prompt(f"How much would you like to Stake [Max {val}]", default=0.0, type=float)
            if amount <= val:
                break
            else:
                click.echo("\nInserted value is more than available")
        trans = blockchain.transaction(priv_key, receiver, amount)
        node.send_to_dist(f"TRANS {' '.join(trans)}")

    elif run_node:
        boot.run()

    else:
        boot.run()

if __name__ == '__main__':
    run()