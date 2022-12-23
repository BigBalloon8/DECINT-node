
## Setup Docker Test Environment

```bash
mkdir DECINT-test
cd DECINT-test
git clone https://github.com/mayfieldmobster/DECINT-node.git
git clone https://github.com/mayfieldmobster/DECINT-dist.git
```

#### Windows
```powershell
FOR /f "tokens=*" %%i IN ('docker ps -aq') DO docker rm -f %%i
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
docker rm -f $(docker ps -aq)
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

#### Run the Docker test environment

Open each container in an external terminals (individual terminals for each container)

In the D2 container run
```bash
DECINT -d2
DECINT
```
In all the other containers except DT run
```bash
DECINT -ti
```

You now have a test environment with 3 nodes and 1 dist node.

#### Basic test
In the DT container run
```bash
DECINT -tt -tr=1
```
-tr stand for transaction rate, this will send 1 transaction per second to the network the maximum transaction rate will depend on how powerful your computer is on my laptop i can handle 10-20 on my PC with 16GB of RAM and ryzen 7 7800x I have tested up to 1000 to work successfully. 

You will be asked for a Private key, this is the private key of the main wallet.

```
PRIV: 28855ad3da56117366898695acf1
```