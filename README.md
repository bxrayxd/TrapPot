# TrapPot

TrapPot is a graduation project honeypot for SSH/Telnet traffic.

It runs these parts together with Docker:

- **Cowrie**: fake SSH/Telnet server that records attacker sessions.
- **Zeek**: watches the network traffic and writes `conn.log` and `ssh.log`.
- **AI detector**: reads Zeek `conn.log` and runs the trained Random Forest model.
- **Elasticsearch**: stores Cowrie and Zeek logs.
- **Logstash**: cleans Zeek values, adds GeoIP when possible, and sends logs into Elasticsearch.
- **Kibana**: lets you view the logs in a browser.
- **ELK setup**: creates Elasticsearch templates, Kibana data views, and a starter dashboard.

The basic flow is:

```text
SSH/Telnet connection -> Cowrie -> Zeek logs -> Random Forest detector
                                      |
                                      -> Logstash -> Elasticsearch -> Kibana
```

## Requirements

This guide is for Arch Linux.

You need:

- Git
- Docker
- Docker Compose
- OpenSSH client

## Install Docker

Install the packages:

```sh
sudo pacman -Syu
sudo pacman -S --needed git docker docker-compose docker-buildx openssh
```

Start Docker:

```sh
sudo systemctl enable --now docker
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

Set the Elasticsearch kernel setting:

```sh
sudo sysctl -w vm.max_map_count=1048576
```

## Run TrapPot

Clone the repo:

```sh
git clone https://github.com/bxrayxd/graduation-project.git
cd graduation-project/TrapPot
```

Start everything:

```sh
docker compose up --build -d
```

Check that the containers are running:

```sh
docker compose ps
```

You should see these services:

```text
cowrie
zeek
ai_detector
elasticsearch
logstash
kibana
elk_setup
```

## Test Cowrie

Open a fake SSH session:

```sh
ssh root@localhost -p 2222
```

Use this password:

```text
admin
```

Run a few commands:

```sh
whoami
pwd
ls -la
mkdir test_dir
cat /etc/passwd
exit
```

This creates logs for Cowrie, Zeek, the AI detector, and Kibana.

## Check the Logs

Cowrie logs:

```sh
docker compose logs cowrie
```

Zeek connection log:

```sh
cat ./zeek/logs/conn.log
```

Zeek SSH log:

```sh
cat ./zeek/logs/ssh.log
```

AI detector output:

```sh
docker compose logs ai_detector
```

Expected detector output:

```text
TrapPot AI is watching the network...
ALERT: Normal detected!
```

Logstash output:

```sh
docker compose logs logstash
```

## Open Kibana

Open Kibana in your browser:

```text
http://localhost:5601
```

Kibana can take a minute to load the first time.

## Configure Kibana

TrapPot creates the Kibana data views for you when Docker starts.

Open **Discover** in Kibana and choose one of these data views:

```text
Cowrie logs
Zeek connection logs
Zeek SSH logs
```

TrapPot also creates a starter dashboard named:

```text
TrapPot Overview
```

If the data views are missing, create them manually.

In Kibana:

1. Open the menu.
2. Go to **Stack Management**.
3. Open **Data Views**.
4. Click **Create data view**.

Create this data view:

```text
Name: Cowrie logs
Index pattern: trappot-cowrie
Time field: @timestamp
```

Create this data view:

```text
Name: Zeek connection logs
Index pattern: trappot-zeek-conn
Time field: @timestamp
```

Create this data view:

```text
Name: Zeek SSH logs
Index pattern: trappot-zeek-ssh
Time field: @timestamp
```

After that, open **Discover** in Kibana and choose one of the data views.

Useful things to search for:

- `eventid : "cowrie.command.input"`
- `service : "ssh"`
- `trappot_source : "zeek_conn"`
- `trappot_source : "cowrie"`

GeoIP can be empty in a local Docker test because the source IP is private. It is useful when the source IP is public.

## Stop TrapPot

Stop the containers:

```sh
docker compose down
```

Stop and delete the stored Elasticsearch/Cowrie Docker volumes:

```sh
docker compose down -v
```

Use `down -v` only when you want a clean reset.

## Ports

TrapPot uses these local ports:

- `2222`: Cowrie SSH
- `2223`: Cowrie Telnet
- `5601`: Kibana

## Common Problems

If port `2222` is already used, stop the other service or change the port in `TrapPot/docker-compose.yml`.

If Elasticsearch does not start, run this again:

```sh
sudo sysctl -w vm.max_map_count=1048576
```

If Kibana opens but shows no data, run the SSH test again and wait 30 seconds.

If the AI detector shows no alerts, check that Zeek created `./zeek/logs/conn.log`.

If the Kibana data views are missing, check the setup container:

```sh
docker compose logs elk_setup
```

## Safety

Run TrapPot in a lab network. Do not expose it to the public internet or a university network without approval.
