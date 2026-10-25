import argparse
import socket
import sys
from datetime import datetime, timezone
import config
from inspector import inspect
from models import Packet


def _log(message: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [sentinel] {message}", flush=True)


def handle_client(conn: socket.socket) -> None:
    data = conn.recv(4096)
    line = data.decode("utf-8", errors="replace").splitlines()[0]
    try:
        packet = Packet.from_line(line)
        result = inspect(packet)
        _log(f"inspecting {packet.src_ip} -> {packet.dst_ip}: {result.verdict.value} ({result.reason})")
        response = f"{result.verdict.value} | {result.reason}\n"
    except ValueError as exc:
        _log(f"bad request: {exc}")
        response = f"ERROR | {exc}\n"
    conn.sendall(response.encode("utf-8"))


def run_server(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        server.bind((host, port))
        server.settimeout(1)
        server.listen(5)
        _log(f"listening on {host}:{port}")

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
    try:
        run_server(args.host, args.port)
    except KeyboardInterrupt:
        _log("shutting down")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
