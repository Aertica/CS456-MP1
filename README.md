# Overview

A Firewall Agent/Network Sentinel, fault-detection monitor, and attack script.

---

# Network Sentinel

## Architecture

* **service.py**: A TCP server that enforces access control by checking packet source IPs against known blacklisted source IPs.
* **monitor.py**: UDP monitor that alerts if heartbeats are not recieved.
* **attack_script.py**: An audit script that demonstrates heartbeat spoofing and message replay attacks against the monitor.

---

## 1. Start the monitor

In the first terminal:

```text
python monitor.py
```
* Listens on port 1025 by default
* Triggers an alert when no heartbeat arrives within 3 seconds
* The service sends a heartbeat every 1 second. If 3 are missed, the monitor
prints an alert and saves it to `monitor.log`.
*The service crashes at random, so keep sending packets until it does.
Settings are in `config.py`.

## 2. Start the service

In a second terminal:

```text
python service.py
```

* Listens on `127.0.0.1:9100` by default.
* Emits periodic heartbeat signals to 127.0.0.1:1025 every second.

Or optionally:

```text
python service.py --host <host> --port <port>
```

## 3. Send a packet

In a third terminal:

```text
python send_packet.py --src 192.168.1.10 --payload "hello"
```

The client prints the server reply:

```text
ALLOW | no policy violation
DENY | blacklisted source IP 198.51.100.7
```

### Arguments


| Flag                | Meaning                                  |
| ------------------- | ---------------------------------------- |
| `--src`             | Source IP (required)                     |
| `--dst`             | Destination IP (default `10.0.0.1`)      |
| `--payload`         | Packet body (default empty)              |
| `--host` / `--port` | Server address (must match `service.py`) |


Blocked IP addresses are stored in config.py.

