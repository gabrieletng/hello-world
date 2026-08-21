#!/usr/bin/env python3
"""Strip PostHog and Microsoft Clarity snippets from every HTML file's <head>.

The off switch for the analytics that install_posthog.py / install_clarity.py
inject. Removing the snippets means no third-party script loads and no cookies
are set, so the site needs no cookie banner. The analytics wrapper in
js/analytics.js stays in place but silently no-ops (its calls guard on
`window.posthog`, which no longer exists).

To turn tracking back on, re-run:
    python3 scripts/install_posthog.py
    python3 scripts/install_clarity.py
"""
import pathlib
import re
import sys

# Each snippet is a `<!-- Label -->` comment immediately followed by its
# <script> block. Match the comment through the closing </script>, plus one
# trailing blank line so removal doesn't leave a gap behind.
BLOCKS = {
    "PostHog": re.compile(
        r"[ \t]*<!-- PostHog -->\n.*?</script>\n\n?",
        re.IGNORECASE | re.DOTALL,
    ),
    "Microsoft Clarity": re.compile(
        r"[ \t]*<!-- Microsoft Clarity -->\n.*?</script>\n\n?",
        re.IGNORECASE | re.DOTALL,
    ),
}

ROOT = pathlib.Path(__file__).resolve().parent.parent

def main() -> int:
    files = list(ROOT.rglob("*.html"))
    touched = skipped = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new_text = text
        for pattern in BLOCKS.values():
            new_text = pattern.sub("", new_text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            touched += 1
        else:
            skipped += 1
    print(f"stripped: {touched}  unchanged: {skipped}  total: {len(files)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
