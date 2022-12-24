
## Setup Docker Test Environment
### 1. Clone Project Files
```bash
mkdir DECINT-test
cd DECINT-test
git clone https://github.com/mayfieldmobster/DECINT-node.git
git clone https://github.com/mayfieldmobster/DECINT-dist.git
```
### 2. Initiate Docker Containers

#### Windows
```powershell
docker rm --force D2
docker rm --force D3
docker rm --force D4
docker rm --force DD
docker rm --force DT
docker rmi decint
docker rmi decint-dist
cd DECINT-node
docker build -t="decint" .
cd ..\DECINT-dist
docker build -t="decint-dist" .
docker run -d -i --name D2 decint
docker run -d -i --name D3 decint
docker run -d -i --name D4 decint
docker run -d -i --name DD decint-dist
docker run -d -i --name DT decint
cd ..
```

#### Linux
```bash
docker rm --force D2
docker rm --force D3
docker rm --force D4
docker rm --force DD
docker rm --force DT
docker rmi decint
docker rmi decint-dist
cd DECINT-node
docker build -t="decint" .
cd ../DECINT-dist
docker build -t="decint-dist" .
docker run -d -i --name D2 decint
docker run -d -i --name D3 decint
docker run -d -i --name D4 decint
docker run -d -i --name DD decint-dist
docker run -d -i --name DT decint
```

### 3. Run the Docker test environment

#### (i) Open each container in an external terminals (individual terminals for each container) 

Use this command:
```bash
docker exec -it D_ bash
```
Where D_ is the name of the container you want to open.

Or use docker desktop to open a terminal for each container.

#### (ii) Initialize the D2 node

In the D2 container run
```bash
DECINT -d2
DECINT
```
The -d2 command is only built in for testing purposes. It will be removed in the future.
It does a few different things, It changes the only node in the list of nodes to the D2 nodes ip address. 
It also changes the nodes stored local public key to the main public key and disable waiting for updates from other
nodes before excepting new nodes (to essentially jump start the network).

#### (iii) Initialize the D3, D4, DD nodes

In all the  D3, D4 and DD containers run
```bash
DECINT -ti
```
The -ti command is only built in for testing purposes. It will be removed in the future.
It generates a random private and public key to be used for the node and announces the node to the network. 
Finally, it starts the node as usual.

You now have a test environment with 3 nodes and 1 dist node.

### 4. Basic test
In the DT container run
```bash
DECINT -tt -tr=1
```
-tt and -tr commands are only built in for testing purposes. It will be removed in the future.
-tt stands for test transactions it sends a constant flow of transactions to a dist node to be sent to the network.

-tr stand for transaction rate, this will send 1 transaction per second to the network. 
The maximum transaction rate will depend on how powerful your computer is, on my low spec laptop I can handle 10-20 on 
my PC with 16GB of RAM and ryzen 7 3800x I have tested up to 1000 transaction per second to work successfully. 

You will be asked for a Private key, this is the private key of the main wallet.
```
PRIV: 28855ad3da56117366898695acf1
```

For more information on how nodes work see the whitepaper.