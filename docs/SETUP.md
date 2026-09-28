# Run the TrapPot lab

[Back to the project](../README.md)

This guide targets Arch Linux with Docker Engine and Docker Compose. Run commands from `TrapPot/Trap-Pot` after cloning, unless a step says otherwise.

## Prepare the host

Install the required packages and start Docker:

```sh
sudo pacman -Syu
sudo pacman -S --needed git docker docker-compose docker-buildx openssh
sudo systemctl enable --now docker
```

If your user does not already have Docker access:

```sh
sudo usermod -aG docker "$USER"
newgrp docker
```

Check the tools and set the Elasticsearch kernel value:

```sh
docker --version
docker compose version
sudo sysctl -w vm.max_map_count=1048576
```

The `sysctl` setting above lasts until reboot. Reapply it before starting the lab after a reboot, or persist it using your host's sysctl configuration.

## Clone and configure

```sh
git clone https://github.com/bxrayxd/TrapPot.git
cd TrapPot/Trap-Pot
```

Compose provides default lab credentials, so an `.env` file is optional. To change the Elastic passwords and Kibana encryption key **before the first run**:

```sh
cp .env.example .env
```

Edit `.env` and keep `KIBANA_ENCRYPTION_KEY` at least 32 characters long. The repository ignores this file. These variables configure Elastic services; Cowrie's decoy login rules are in [`cowrie/etc/userdb.txt`](../Trap-Pot/cowrie/etc/userdb.txt).

| Service | Default lab login |
| --- | --- |
| Kibana | `elastic` / `trappotadmin` |
| Cowrie SSH and Telnet | `root` / `admin` |

### Network scope

The supplied Compose file publishes these ports on all host interfaces:

| Host port | Service |
| --- | --- |
| `2222` | Cowrie SSH / SFTP |
| `2223` | Cowrie Telnet |
| `5601` | Kibana |

Use an isolated lab network. For a local-only demo, change the three mappings in [`docker-compose.yml`](../Trap-Pot/docker-compose.yml) to `127.0.0.1:2222:2222`, `127.0.0.1:2223:2223`, and `127.0.0.1:5601:5601` before starting.

Elasticsearch requires authentication, and port `9200` is internal to the Docker network. The lab uses HTTP for Elastic services and supplies known demonstration passwords; public deployment requires separate network and security configuration.

## Start and open the dashboard

```sh
docker compose up --build -d
docker compose ps -a
```

The long-running services are `cowrie`, `zeek`, `ai_detector`, `elasticsearch`, `logstash`, and `kibana`. The `elastic_setup` and `kibana_setup` jobs should finish with exit code `0`. They configure service accounts, index templates, data views, and the dashboard. Check the dashboard itself as well as the setup-job status.

Open [http://localhost:5601](http://localhost:5601), log in with your Elastic credentials, and choose **Dashboards → TrapPot Overview**. Set the time range to **Last 24 hours**.

## Generate your first session

Connect to the local honeypot:

```sh
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@localhost -p 2222
# Password: admin
```

Inside the emulated shell, run:

```sh
whoami
uname -a
cat /etc/passwd
exit
```

Allow about 30 seconds for processing and refresh Kibana. Check the captured commands, connection activity, and RF network decisions. Continue with the [SSH, Telnet, and SFTP demo scenarios](../Trap-Pot/ATTACK_TESTS.md).

## Verify the data path

Follow one session from capture to display:

```sh
# Honeypot activity
docker compose logs cowrie

# Sensor output
cat ./zeek/logs/conn.log
cat ./zeek/logs/ssh.log

# Model processing and structured predictions
docker compose logs ai_detector
cat ./zeek/logs/detections.json

# Ingestion and setup diagnostics
docker compose logs logstash
docker compose logs elastic_setup kibana_setup
```

The detector prints `TrapPot AI is watching the network...` at startup. After it processes a connection, it prints `ALERT: <prediction> detected!` and appends a JSON record to `detections.json`. The word `ALERT` appears for every prediction, including `Normal`.

The **RF network decisions** panel is separate from Cowrie's behavior labels. A `Normal` prediction can appear alongside recorded failed logins or commands. Telnet produces connection records in `conn.log`; `ssh.log` is specific to SSH.

Cowrie's **Brute force attempt** label is a direct mapping from a failed-login event, without a repeated-attempt threshold. The model's `Command Execution` and `Malware Download` labels are predictions from connection metadata; the model does not inspect shell commands or file contents.

GeoIP enrichment can be empty for private or local source addresses. Public addresses may receive geographic fields when a GeoIP database is available; the included dashboard does not contain a map panel.

### Check Elasticsearch authentication

An unauthenticated request should return `401`:

```sh
docker compose exec elasticsearch curl -s -o /dev/null -w '%{http_code}\n' http://localhost:9200
```

To check the configured login, expand the password **inside the container**, where Compose has set it:

```sh
docker compose exec elasticsearch sh -c 'curl -fsS -u "elastic:$ELASTIC_PASSWORD" http://localhost:9200/_security/_authenticate'
```

The accounts have separate roles: `elastic` is the lab administrator, `kibana_system` connects Kibana to Elasticsearch, and `trappot_writer` lets Logstash write to `trappot-*` indices.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| A published port is busy | Change the host-side port in Compose and use that port in your test command or browser. |
| Elasticsearch does not start | Inspect `docker compose logs elasticsearch` and check `vm.max_map_count`. |
| Dashboard or data views are missing | Inspect `docker compose logs kibana_setup` for API errors. |
| Dashboard is empty | Generate a session, exit it, check the time range, wait for ingestion, and refresh. Then trace the logs above. |
| Detector produces no decisions | Check that `./zeek/logs/conn.log` exists and contains connection rows, then inspect detector logs. |
| Detector reports `Detector skipped malformed Zeek row` | Read the attached exception and check the input fields. The parser expects the standard tab-separated Zeek connection layout. |
| Logstash cannot write to Elasticsearch | Inspect `docker compose logs logstash elastic_setup` for authentication or mapping errors. |

## Stop and reset

Stop the stack while preserving its named volumes:

```sh
docker compose down
```

For a disposable lab reset, the following deletes named volumes, including stored Cowrie logs, Elasticsearch data, and Logstash read positions:

```sh
docker compose down -v
```

This does **not** remove the bind-mounted files in `./zeek/logs/`. Retained logs may be processed again after restart; archive or clear those generated files separately if you need an empty dataset.

Start again with:

```sh
docker compose up --build -d
```

Elasticsearch stores credentials in its data volume. Editing `.env` after initialization does not update the stored `elastic` password. For a disposable lab, reset the volumes before starting with new values; keep existing data only if you also update credentials through Elasticsearch's security API.
