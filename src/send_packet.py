import argparse
import socket
import sys
import config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", default="10.0.0.1")
    parser.add_argument("--payload", default="")
    args = parser.parse_args()

    line = f"{args.src}|{args.dst}|{args.payload}\n"
    with socket.create_connection((args.host, args.port), timeout=5) as sock:
        sock.sendall(line.encode("utf-8"))
        reply = sock.recv(4096).decode("utf-8", errors="replace").strip()
    print(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
