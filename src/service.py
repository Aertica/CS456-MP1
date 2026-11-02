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
from state import DynamicState
from state_sync import run_sync_server, send_request_sync
from promote import promote_when_told


def _log(role: str, message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [{role}] {message}", flush=True)


def crash(role: str, reason: str) -> None:
    _log(role, f"CRASH: {reason}")
    os._exit(1)


def maybe_crash(role: str) -> None:
    if random.random() < config.CRASH_PROBABILITY:
        _log(role, "simulated crash on request: exiting")
        os._exit(1)


def heartbeat_loop(role: str, host: str, port: int, interval: float) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq = 0
    service_name = "NetworkSentinelAgent" if role == "primary" else "NetworkSentinelAgent-standby"
    while True:
        seq += 1
        beat = {
            "service": service_name,
            "role": role,
            "seq": seq,
            "timestamp": time.time(),
            "status": "OK",
        }
        
        sock.sendto(json.dumps(beat).encode("utf-8"), (host, port))
        time.sleep(interval)


def fault_thread(role: str) -> None:
    time.sleep(random.uniform(config.FAULT_MIN_S, config.FAULT_MAX_S))
    _log(role, "simulated background fault: exiting")
    os._exit(1)


def process_line(line: str, state: DynamicState, replicate: bool = True) -> str:
    packet = Packet.from_line(line)
    result = inspect(packet, state)
    tag = "primary" if replicate else "secondary"
    _log(tag, f"inspecting {packet.src_ip} -> {packet.dst_ip}: {result.verdict.value} ({result.reason})")
    return f"{result.verdict.value} | {result.reason}\n"


def handle_client(conn: socket.socket, state: DynamicState, sync_host: str, sync_port: int) -> None:
    data = conn.recv(4096)
    maybe_crash("primary")
    try:
        if random.random() < config.REQUEST_CRASH_PROB:
            crash("primary", "simulated segfault on packet")

        line = data.decode("utf-8", errors="replace").splitlines()[0]
        response = process_line(line, state, replicate=True)
        send_request_sync(sync_host, sync_port, line)
    except ValueError as exc:
        if random.random() < config.MALFORMED_CRASH_PROB:
            crash("primary", "simulated segfault on malformed packet")

        _log("primary", f"bad request: {exc}")
        response = f"ERROR | {exc}\n"
    conn.sendall(response.encode("utf-8"))


def run_primary(host: str, port: int, sync_host: str, sync_port: int) -> None:
    state = DynamicState()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.settimeout(1)
        server.listen(5)
        _log("primary", f"listening on {host}:{port}")

        threading.Thread(
            target=heartbeat_loop,
            args=(
                "primary",
                config.MONITOR_HOST,
                config.MONITOR_PORT,
                config.HEARTBEAT_INTERVAL,
            ),
            daemon=True,
        ).start()
        threading.Thread(target=fault_thread, args=("primary",), daemon=True).start()

        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                raise

            _log("primary", f"connection from {addr[0]}:{addr[1]}")
            with conn:
                handle_client(conn, state, sync_host, sync_port)


def run_secondary(sync_host: str, sync_port: int) -> None:
    state = DynamicState()
    run_sync_server(sync_host, sync_port, state, process_line)
    _log("secondary", f"sync listening on {sync_host}:{sync_port}")

    threading.Thread(
        target=heartbeat_loop,
        args=(
            "secondary",
            config.MONITOR_HOST,
            config.MONITOR_PORT,
            config.HEARTBEAT_INTERVAL,
        ),
        daemon=True,
    ).start()

    promote_when_told(state, process_line, _log, heartbeat_loop)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Network sentinel firewall agent")
    parser.add_argument(
        "--role",
        choices=("primary", "secondary"),
        default="primary",
    )
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--sync-host", default=config.SYNC_HOST)
    parser.add_argument("--sync-port", type=int, default=config.SYNC_PORT)
    args = parser.parse_args(argv)

    try:
        if args.role == "primary":
            run_primary(args.host, args.port, args.sync_host, args.sync_port)
        else:
            run_secondary(args.sync_host, args.sync_port)
    except KeyboardInterrupt:
        _log(args.role, "shutting down")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
