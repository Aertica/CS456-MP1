from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True)
class Packet:
    src_ip: str
    dst_ip: str
    payload: str

    @classmethod
    def from_line(cls, line: str) -> Packet:
        parts = line.strip().split("|", 2)
        if len(parts) < 3:
            raise ValueError("expected format SRC|DST|PAYLOAD")
        return cls(src_ip=parts[0].strip(), dst_ip=parts[1].strip(), payload=parts[2])


@dataclass(frozen=True)
class InspectionResult:
    verdict: Verdict
    reason: str
