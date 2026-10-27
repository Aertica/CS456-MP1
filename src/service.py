import argparse
import json
import os
import random
import socket
import sys
import threading
import time
from datetime import datetime, timezone
import config
from inspector import inspect
from models import Packet


#heartbeat

def send_heartbeats() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq = 0
    while True:
        seq += 1
        beat = {"service": "NetworkSentinelAgent", "seq": seq,
                "timestamp": time.time(), "status": "FILTERING_ACTIVE"}
        sock.sendto(json.dumps(beat).encode(), (config.MONITOR_HOST, config.MONITOR_PORT))
        time.sleep(config.HEARTBEAT_INTERVAL)

#kill the whole process
def crash(reason: str) -> None:
    _log(f"CRASH: {reason}")
    os._exit(1) 

def random_background_crash() -> None:
    while True:
        time.sleep(1)
        if random.random() < config.BACKGROUND_CRASH_PROB:
            crash("simulated memory exhaustion")

def _log(message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [sentinel] {message}", flush=True)


def maybe_crash() -> None:
    if random.random() < config.CRASH_PROBABILITY:
        _log("simulated crash on request: exiting")
        os._exit(1)


def heartbeat_loop(host: str, port: int, interval: float) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq = 0
    while True:
        seq += 1
        beat = {"service": "NetworkSentinelAgent", "seq": seq,
                "timestamp": time.time(), "status": "OK"}
        sock.sendto(json.dumps(beat).encode("utf-8"), (host, port))
        time.sleep(interval)


def fault_thread() -> None:
    time.sleep(random.uniform(config.FAULT_MIN_S, config.FAULT_MAX_S))
    _log("simulated background fault: exiting")
    os._exit(1)


def handle_client(conn: socket.socket) -> None:
    data = conn.recv(4096)
    maybe_crash()
    try:
        packet = Packet.from_line(line)
        if random.random() < config.REQUEST_CRASH_PROB:
            crash("simulated segfault on packet")
        result = inspect(packet)
        _log(f"inspecting {packet.src_ip} -> {packet.dst_ip}: {result.verdict.value} ({result.reason})")
        response = f"{result.verdict.value} | {result.reason}\n"
    except ValueError as exc:
        if random.random() < config.MALFORMED_CRASH_PROB:
            crash("simulated segfault on malformed packet")
        _log(f"bad request: {exc}")
        response = f"ERROR | {exc}\n"
    conn.sendall(response.encode("utf-8"))


def run_server(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.settimeout(1)
        server.listen(5)
        _log(f"listening on {host}:{port}")

        threading.Thread(
            target=heartbeat_loop,
            args=(config.MONITOR_HOST, config.MONITOR_PORT, config.HEARTBEAT_INTERVAL),
            daemon=True,
        ).start()
        threading.Thread(target=fault_thread, daemon=True).start()

        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                raise

            conn.settimeout(None)
            _log(f"connection from {addr[0]}:{addr[1]}")
            with conn:
                handle_client(conn)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Network sentinel firewall agent")
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    args = parser.parse_args(argv)
    threading.Thread(target=send_heartbeats, daemon=True).start()
    threading.Thread(target=random_background_crash, daemon=True).start()
    try:
        run_server(args.host, args.port)
    except KeyboardInterrupt:
        _log("shutting down")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
