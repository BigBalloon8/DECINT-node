from blockchain import priv_key_gen, pub_key_gen

priv, hex_priv = priv_key_gen()
pub, hex_pub = pub_key_gen(priv)
print(hex_priv)
print(hex_pub)