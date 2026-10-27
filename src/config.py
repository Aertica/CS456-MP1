HOST = "127.0.0.1"
PORT = 9100

# Monitor Config
MONITOR_HOST = "127.0.0.1"
MONITOR_PORT = 1025
HEARTBEAT_INTERVAL = 1.0
MISSED_BEATS_THRESHOLD = 3

MISSED_BEATS = 3            # beats missed before an alert
CRASH_PROBABILITY = 0.05    
FAULT_MIN_S = 10            # background fault fires between these times
FAULT_MAX_S = 60

BLACKLISTED_SOURCE_IPS = frozenset(
{
    "203.0.113.50",
    "198.51.100.7",
})


# Crash chances
BACKGROUND_CRASH_PROB = 0.02 #per sec
REQUEST_CRASH_PROB = 0.10 #per packet
MALFORMED_CRASH_PROB = 0.50 #per malformed packet