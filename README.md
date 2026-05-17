# TrapPot

TrapPot is a graduation project honeypot. It runs:

- Cowrie as the SSH/Telnet honeypot
- Zeek as the network log translator
- A Python Random Forest detector that reads Zeek `conn.log`
- Elasticsearch, Logstash, and Kibana for log storage and dashboards

## Requirements

- Arch Linux
- Git
- Docker Engine
- Docker Compose

If Docker is already installed, skip to [Run TrapPot](#run-trappot).

## Install Docker on Arch Linux

Install the required packages:

```sh
sudo pacman -Syu
sudo pacman -S --needed git docker docker-compose docker-buildx openssh
```

Start Docker:

```sh
sudo systemctl enable --now docker
```

Allow your user to run Docker without `sudo`:

```sh
sudo usermod -aG docker "$USER"
newgrp docker
```

Check Docker:

```sh
docker --version
docker compose version
```

Set the Elasticsearch kernel limit:

```sh
sudo sysctl -w vm.max_map_count=1048576
```

Arch package pages:

- Docker: https://archlinux.org/packages/extra/x86_64/docker/
- Docker Compose: https://archlinux.org/packages/extra/x86_64/docker-compose/

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

Docker pulls Cowrie, Zeek, and Elastic images, then builds the AI detector image.

Check the containers:

```sh
docker compose ps
```

You should see:

```text
cowrie
zeek
ai_detector
elasticsearch
logstash
kibana
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

Open Kibana:

```text
http://localhost:5601
```

Create data views for:

```text
trappot-cowrie
trappot-zeek-conn
trappot-zeek-ssh
```

Use `@timestamp` as the time field.

## Stop TrapPot

Stop the containers:

```sh
docker compose down
```

## Ports

TrapPot uses these local ports:

- `2222` for Cowrie SSH
- `2223` for Cowrie Telnet
- `5601` for Kibana

If Docker says port `2222` is already in use, stop the other service or change the port mapping in `TrapPot/docker-compose.yml`.

## Safety Note

Run this project in a controlled lab environment. Do not expose the honeypot to the public internet or a university network without approval.
