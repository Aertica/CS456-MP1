import json
import socket
import time     
from datetime import datetime, timezone

import config

WINDOW = config.HEARTBEAT_INTERVAL * config.MISSED_BEATS_THRESHOLD

def log(message):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] [monitor] {message}"
    print(line, flush=True)
    with open("monitor.log", "a") as f:
        f.write(line + "\n")

def send_promote(sock):
    sock.sendto(b'{"type": "promote"}', (config.SYNC_HOST, config.PROMOTE_PORT))

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.MONITOR_HOST, config.MONITOR_PORT))
    sock.settimeout(0.5)
    log(f"listening on {config.MONITOR_HOST}:{config.MONITOR_PORT} (W = {WINDOW}s)")

    last_beat = {} 
    alive = {}
    failed_over = False
    crash_time = None #set while waiting for the second take over

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            beat = json.loads(data)
            role = beat.get("role", "primary")
            seq = beat["seq"]
            now = time.monotonic()
            last_beat[role] = now
            if not alive.get(role):
                alive[role] = True
                if role == "primary" and crash_time is not None:
                    log(f"SERVICE RESTORED: secondary promoted to primary (MTTR {now - crash_time:.1f}s)")
                    crash_time = None
                else:
                    log(f"{role} UP (seq {seq})")
            else:
                print(f" beat OK {role} seq={seq}", flush=True)
        except socket.timeout:
            pass
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass #Ignore bad packet; monitor must never crash

        now = time.monotonic()
        for role in list(alive):
            if alive[role] and now - last_beat[role] > WINDOW:
                alive[role] = False
                log(f"CRASH DETECTED: {role} missed heartbeats for {WINDOW}s")
                if role != "primary":
                    continue
                if not failed_over and alive.get("secondary"):
                    log("FAILOVER TRIGGERED: promoting secondary")
                    send_promote(sock)
                    failed_over = True
                    crash_time = last_beat[role]
                elif not failed_over:
                    log("ALERT: no secondary available, failover impossible")
                else:
                    log("ALERT: promoted primary is down, no further failover")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
