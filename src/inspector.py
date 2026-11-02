import config
from models import InspectionResult, Packet, Verdict
from state import DynamicState


def inspect(packet: Packet, state: DynamicState) -> InspectionResult:
    if packet.payload.strip() == "+blacklist":
        state.add_blacklist(packet.src_ip)
        return InspectionResult(
            verdict=Verdict.ALLOW,
            reason=f"added {packet.src_ip} to dynamic blacklist",
        )

    if packet.src_ip in config.BLACKLISTED_SOURCE_IPS or state.is_blacklisted(packet.src_ip):
        return InspectionResult(
            verdict=Verdict.DENY,
            reason=f"blacklisted source IP {packet.src_ip}",
        )

    return InspectionResult(verdict=Verdict.ALLOW, reason="no policy violation")
