# TrapPot

TrapPot is an AI-powered IoT honeypot system for SSH and Telnet activity.

It runs a full local pipeline:

```text
Attacker SSH/Telnet session
        |
        v
Cowrie honeypot logs
        |
        v
Zeek conn.log and ssh.log
        |
        v
Random Forest detector
        |
        v
Logstash -> Elasticsearch -> Kibana dashboard
```

## What Runs

- **Cowrie** records fake SSH/Telnet attacker sessions.
- **Zeek** watches the Cowrie network traffic and writes `conn.log` and `ssh.log`.
- **AI detector** reads Zeek `conn.log` and runs the trained Random Forest model.
- **Logstash** cleans the logs and sends them to Elasticsearch.
- **Elasticsearch** stores Cowrie, Zeek, and detector records with login protection enabled.
- **Kibana** shows the ready-made TrapPot dashboard.

## Requirements

This guide targets Arch Linux.

Install the required packages:

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

Set the Elasticsearch kernel value:

```sh
sudo sysctl -w vm.max_map_count=1048576
```

## Run TrapPot

Clone the repo:

```sh
git clone https://github.com/bxrayxd/graduation-project.git
cd graduation-project/Trap-Pot
```

Optional: create a local password file if you want to change the default lab passwords:

```sh
cp .env.example .env
```

Default local credentials:

```text
Kibana username: elastic
Kibana password: trappotadmin
Cowrie username: root
Cowrie password: admin
```

TrapPot can start without `.env`; Docker Compose uses the same local defaults shown above. If you create `.env`, you can change the Elastic passwords before the first run. Keep `KIBANA_ENCRYPTION_KEY` at least 32 characters long.

Do not commit `Trap-Pot/.env`. The repo ignores it on purpose.

Start the system:

```sh
docker compose up --build -d
```

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
elastic_setup
logstash
kibana
kibana_setup
```

`elastic_setup` and `kibana_setup` should exit with code `0`. That is normal. They create users, templates, data views, and the dashboard.

## Test The Honeypot

Open a fake SSH session:

```sh
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@localhost -p 2222
```

Use this password:

```text
admin
```

Run a few commands:

```sh
whoami
pwd
uname -a
mkdir test_dir
cat /etc/passwd
exit
```

Wait about 30 seconds. Cowrie, Zeek, the AI detector, Logstash, Elasticsearch, and Kibana need a short moment to process the session.

## Check The Output

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

AI detector:

```sh
docker compose logs ai_detector
```

Expected detector output:

```text
TrapPot AI is watching the network...
ALERT: Normal detected!
```

Logstash should not show indexing errors:

```sh
docker compose logs logstash
```

## Open Kibana

Open:

```text
http://localhost:5601
```

Log in with:

```text
username: elastic
password: trappotadmin
```

Open **Dashboards**, then open:

```text
TrapPot Overview
```

The dashboard shows:

- Cowrie events
- login attempts
- captured commands
- Zeek connections
- AI detector decisions
- top source IPs, usernames, credentials, and commands

GeoIP fields can stay empty during a local Docker test because the source IP is private. GeoIP becomes useful when traffic comes from public IP addresses.

## Security Notes

TrapPot enables Elastic username/password security by default.

The local demo uses these accounts:

- `elastic`: Kibana login and admin account.
- `kibana_system`: Kibana service account.
- `trappot_writer`: Logstash writer account for `trappot-*` indices.

Elasticsearch port `9200` is not published to your host. Kibana port `5601` is published so you can open the dashboard.

This setup still uses HTTP inside the local Docker lab. Do not expose Kibana or Cowrie to a public network without approval and firewall rules.

Check that Elasticsearch rejects requests without a login:

```sh
docker compose exec elasticsearch curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9200
```

Expected result:

```text
401
```

Check that the Elastic login works:

```sh
docker compose exec elasticsearch curl -s -u "elastic:$ELASTIC_PASSWORD" http://localhost:9200/_security/_authenticate
```

## Useful Files

Main runtime files:

```text
Trap-Pot/docker-compose.yml
Trap-Pot/.env.example
Trap-Pot/cowrie/etc/cowrie.cfg
Trap-Pot/cowrie/etc/userdb.txt
Trap-Pot/ai_detector/detector.py
Trap-Pot/logstash/pipeline/trappot.conf
Trap-Pot/elasticsearch/templates/
Trap-Pot/kibana/
```

Generated logs:

```text
Trap-Pot/zeek/logs/conn.log
Trap-Pot/zeek/logs/ssh.log
Trap-Pot/zeek/logs/detections.json
```

## Stop Or Reset

Stop the containers:

```sh
docker compose down
```

Delete stored Cowrie and Elasticsearch data:

```sh
docker compose down -v
```

Use `down -v` when you want a clean test.

Run a clean reset:

```sh
docker compose down -v
docker compose up --build -d
```

If you change `.env` after Elasticsearch already started, run the clean reset command. Elasticsearch stores passwords inside its Docker volume.

## Ports

- `2222`: Cowrie SSH
- `2223`: Cowrie Telnet
- `5601`: Kibana

## Common Problems

If port `2222` is busy, stop the other service or change the Cowrie port in `Trap-Pot/docker-compose.yml`.

If Elasticsearch does not start, run:

```sh
sudo sysctl -w vm.max_map_count=1048576
```

If Kibana opens but shows no data, run the SSH test again and wait 30 seconds.

If the AI detector shows no alerts, check that Zeek created:

```text
./zeek/logs/conn.log
```

If the AI detector prints `Detector skipped malformed Zeek row`, check `conn.log`. The detector expects the normal Zeek connection fields.

If the dashboard or data views are missing, check:

```sh
docker compose logs kibana_setup
```

If Logstash cannot write to Elasticsearch, check:

```sh
docker compose logs logstash
docker compose logs elastic_setup
```

## Safety

Run TrapPot in a lab network. Do not expose it to the public internet or a university network without written approval.
