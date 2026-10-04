#!/usr/bin/env python3
"""Embed a generated card list into index.html.

The list is inlined, not loaded from a separate file, so index.html works
when opened on its own (e.g. from a phone's Downloads via a content:// link,
where neighbouring files can't be loaded).

Usage: python3 tools/inline_data.py cards.js index.html
"""
import re
import sys
from pathlib import Path

data = Path(sys.argv[1]).read_text(encoding="utf-8").strip().replace("</script", "<\\/script")
page_path = Path(sys.argv[2])
page = page_path.read_text(encoding="utf-8")
block = f"<script id=\"card-data\">\n{data}\n</script>"
pattern = re.compile(r'<script id="card-data">.*?</script>|<script src="cards.js"></script>', re.S)
if not pattern.search(page):
    sys.exit("No card-data block found in " + str(page_path))
page_path.write_text(pattern.sub(lambda _: block, page, count=1), encoding="utf-8")
print(f"Inlined {sys.argv[1]} into {page_path}")
