import json
import socket
import threading
import time
import config


def wait_for_promotion() -> None:
    """Block until the monitor tells this secondary to take over."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config.SYNC_HOST, config.PROMOTE_PORT))
    while True:
        data, _ = sock.recvfrom(1024)
        try:
            if json.loads(data).get("type") == "promote":
                return
        except (ValueError, AttributeError):
            pass

def serve_as_primary(state, process_line, log, heartbeat_loop) -> None:
    """Take over the client port using the state already synced from the primary."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #Dead primary port can take a moment to free up, so retry

    for _ in range(20):
        try:
            server.bind((config.HOST, config.PORT))
            break
        except OSError:
            time.sleep(0.5)
    else:
        log("secondary", "PROMOTION FAILED: port still in use, is the primary still alive?")
        return
    server.settimeout(1)
    server.listen(5)
    log("seconday", f"PROMOTED: now serving as primary on {config.HOST}:{config.PORT} "
                        f"({len(state.snapshot())} dynamic blacklist entries)")

    #Only announce awe're primary after we hold the port
    threading.Thread(
        target=heartbeat_loop,
        args=("primary", config.MONITOR_HOST, config.MONITOR_PORT, config.HEARTBEAT_INTERVAL),
        daemon=True,
    ).start()

    while True:
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue
        with conn:
            try:
                line = conn.recv(4096).decode("utf-8", errors="replace").splitlines()[0]
                response = process_line(line, state, replicate=True)
            except (ValueError, IndexError) as exc:
                response = f"ERROR | {exc}\n"
            conn.sendall(response.encode("utf-8"))

def promote_when_told(state, process_line, log, heartbeat_loop) -> None:
    wait_for_promotion()
    log("secondary", "promotion recieved from monitor")
    serve_as_primary(state, process_line, log, heartbeat_loop)
    while True:
        time.sleep(3600) #stay alive even if promotion fails           
             
        