# Overview
A Firewall Agent/Network Sentinel, fault-detection monitor, and attack script.

# Network Sentinel

## 1. Start the service

```text
python service.py
```

Listens on `127.0.0.1:9100` by default.

Or optionaly:

```text
python service.py --host <host> --port <port>
```

## 2. Send a packet

In a second terminal:

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
