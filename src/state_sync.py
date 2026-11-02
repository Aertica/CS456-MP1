import json
import socket
import threading

from state import DynamicState


def send_request_sync(host: str, port: int, line: str) -> None:
    msg = {"type": "request", "line": line.strip()}
    payload = json.dumps(msg).encode("utf-8") + b"\n"
    try:
        with socket.create_connection((host, port), timeout=2) as conn:
            conn.sendall(payload)
    except OSError:
        pass


def _read_line(conn: socket.socket) -> str:
    buf = b""
    while b"\n" not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
    if not buf:
        return ""
    return buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")


def apply_sync_message(state: DynamicState, msg: dict, process_line) -> None:
    if msg.get("type") != "request":
        return
    line = msg.get("line", "")
    if not line:
        return
    process_line(line, state, replicate=False)


def run_sync_server(host: str, port: int, state: DynamicState, process_line) -> None:
    def server() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(8)
            while True:
                conn, _ = server.accept()
                with conn:
                    raw = _read_line(conn)
                    if not raw:
                        continue
                    try:
                        msg = json.loads(raw)
                    except ValueError:
                        continue
                    apply_sync_message(state, msg, process_line)

    threading.Thread(target=server, daemon=True).start()
