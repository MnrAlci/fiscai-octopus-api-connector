"""git pre-commit helper: reject files that look like they contain Octopus credentials or an API key. Prints file names only, never the match."""
import re
import sys
from pathlib import Path

PATTERNS = [r"am_[A-Za-z0-9]{10,}", r"sk-[A-Za-z0-9]{16,}", r"(?i)OCTOPUS_(?:PASSWORD|SOFTWARE_HOUSE_UUID|CACHE_KEY)\s*=\s*\S{8,}", r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"]
bad = []
for f in sys.argv[1:]:
    try:
        t = Path(f).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if any(re.search(p, t) for p in PATTERNS):
        bad.append(f)
if bad:
    print("Possible secret in: " + ", ".join(bad))
    sys.exit(1)
