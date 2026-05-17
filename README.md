# TrapPot

TrapPot is a graduation project honeypot. It runs:

- Cowrie as the SSH/Telnet honeypot
- Zeek as the network log translator
- A Python Random Forest detector that reads Zeek `conn.log`

## Requirements

- Linux machine, tested with Ubuntu-style Docker commands
- Git
- Docker Engine
- Docker Compose plugin

If Docker is already installed, skip to [Run TrapPot](#run-trappot).

## Install Docker on Ubuntu/Debian

Use Docker's official install guide if your Linux distribution is different:

- Docker Engine: https://docs.docker.com/engine/install/
- Docker Compose plugin: https://docs.docker.com/compose/install/linux/

Install Docker on Ubuntu/Debian:

```sh
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Allow your user to run Docker:

```sh
sudo usermod -aG docker "$USER"
newgrp docker
```

Check Docker:

```sh
docker --version
docker compose version
```

## Run TrapPot

Clone the repository:

```sh
git clone https://github.com/bxrayxd/graduation-project.git
cd graduation-project/TrapPot
```

Start the stack:

```sh
docker compose up --build -d
```

Docker pulls the Cowrie and Zeek images, then builds the AI detector image.

Check the containers:

```sh
docker compose ps
```

You should see:

```text
cowrie
zeek
ai_detector
```

## Test the Honeypot

Connect to Cowrie:

```sh
ssh root@localhost -p 2222
```

Password:

```text
admin
```

Run test commands:

```sh
whoami
pwd
ls -la
mkdir test_dir
cat /etc/passwd
exit
```

## Check the Logs

Cowrie logs the SSH session:

```sh
docker compose logs cowrie
```

Zeek writes logs here:

```text
TrapPot/zeek/logs
```

Check Zeek connection logs:

```sh
cat ./zeek/logs/conn.log
```

Check Zeek SSH logs:

```sh
cat ./zeek/logs/ssh.log
```

Check the AI detector output:

```sh
docker compose logs ai_detector
```

Expected detector output:

```text
TrapPot AI is watching the network...
ALERT: Normal detected!
```

## Stop TrapPot

Stop the containers:

```sh
docker compose down
```

## Ports

TrapPot uses these local ports:

- `2222` for Cowrie SSH
- `2223` for Cowrie Telnet

If Docker says port `2222` is already in use, stop the other service or change the port mapping in `TrapPot/docker-compose.yml`.

## Safety Note

Run this project in a controlled lab environment. Do not expose the honeypot to the public internet or a university network without approval.
