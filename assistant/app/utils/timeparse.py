from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import re

RELATIVE_PATTERN = re.compile(r"in\\s+(\\d+)\\s*(minutes?|hours?|days?)", re.IGNORECASE)


def parse_when(text: str) -> Optional[datetime]:
    """Parse simple natural language expressions from text and return datetime."""
    text = text.strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass

    match = RELATIVE_PATTERN.search(text)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        delta: timedelta
        if unit.startswith("minute"):
            delta = timedelta(minutes=value)
        elif unit.startswith("hour"):
            delta = timedelta(hours=value)
        else:
            delta = timedelta(days=value)
        return datetime.utcnow() + delta

    return None
