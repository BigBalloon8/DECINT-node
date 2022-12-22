from DECINT_node.blockchain import priv_key_gen, pub_key_gen
from ecdsa import SigningKey, SECP112r2

# priv, hex_priv = priv_key_gen()
priv_key = input("priv: ")
priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
pub, hex_pub = pub_key_gen(priv_key)


print(hex_pub)