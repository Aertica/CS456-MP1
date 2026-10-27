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

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.MONITOR_HOST, config.MONITOR_PORT))
    sock.settimeout(0.5)
    log(f"listening on {config.MONITOR_HOST}:{config.MONITOR_PORT} (W = {WINDOW}s)")

    last_beat = None
    alive = False

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            beat = json.loads(data)

            #Baseline any heartbeat is trusted without auth 
            last_beat = time.monotonic()
            if not alive:
                log(f"service UP (seq {beat['seq']})")
                alive = True
            else:
                print(f" beat OK seq={beat['seq']}", flush=True)
        except socket.timeout:
            pass
        except (OSError, ValueError, KeyError, TypeError):
            pass #Ignore bad packet; monitor must never crash

        if alive and time.monotonic() - last_beat > WINDOW:
            log(f"ALERT: service down no heartbeat for {WINDOW}s")
            alive = False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
