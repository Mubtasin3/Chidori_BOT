from datetime import datetime, timezone
import re

def utcnow():
    return datetime.now(timezone.utc)

def clean_text(text: str, limit=2000):
    return (text or "")[:limit]

def parse_duration(value: str):
    m = re.fullmatch(r"(\d+)\s*(s|m|h|d|w)", value.lower().strip())
    if not m:
        raise ValueError("Use formats like 10m, 2h, 1d or 1w.")
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s":1,"m":60,"h":3600,"d":86400,"w":604800}[unit]
