import threading


class DynamicState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._blacklist: set[str] = set()

    def add_blacklist(self, ip: str) -> None:
        with self._lock:
            self._blacklist.add(ip)

    def is_blacklisted(self, ip: str) -> bool:
        with self._lock:
            return ip in self._blacklist

    def snapshot(self) -> list[str]:
        with self._lock:
            return sorted(self._blacklist)
