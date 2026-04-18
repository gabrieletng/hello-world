#!/usr/bin/env python3
"""Inject Microsoft Clarity snippet into every HTML file's <head>."""
import pathlib
import re
import sys

SNIPPET = """  <!-- Microsoft Clarity -->
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "wdsri555iv");
  </script>
"""

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD_RE = re.compile(r"(<head\b[^>]*>)", re.IGNORECASE)

def main() -> int:
    files = list(ROOT.rglob("*.html"))
    touched = skipped = missing = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "clarity.ms/tag" in text:
            skipped += 1
            continue
        m = HEAD_RE.search(text)
        if not m:
            missing += 1
            print(f"no <head>: {path}", file=sys.stderr)
            continue
        new_text = text[:m.end()] + "\n" + SNIPPET + text[m.end():]
        path.write_text(new_text, encoding="utf-8")
        touched += 1
    print(f"injected: {touched}  skipped: {skipped}  no-head: {missing}  total: {len(files)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
