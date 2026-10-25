import config
from models import InspectionResult, Packet, Verdict


def inspect(packet: Packet) -> InspectionResult:
    if packet.src_ip in config.BLACKLISTED_SOURCE_IPS:
        return InspectionResult(
            verdict=Verdict.DENY,
            reason=f"blacklisted source IP {packet.src_ip}",
        )

    return InspectionResult(verdict=Verdict.ALLOW, reason="no policy violation")
