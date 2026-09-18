#!/usr/bin/env python3
"""Scrape WAEC SSCE objective past questions from TestDriller.com.

URL pattern (public pages, allowed by robots.txt):
  /past-questions/waec-objective-{subject}-{year}-{question-number}

Writes one JSON per subject+year to data/extracted/tdw_{subject}_{year}.json
with items shaped like the existing td_* files (prompt, options, answer) plus
an explicit year. Raw HTML is cached under data/raw/tdw_cache/ so a re-run
never re-fetches pages it already has. Existing output files are skipped,
so the scraper is safe to interrupt and resume.

Politeness: single-threaded, 0.4s between network fetches, robots.txt for
testdriller.com does not disallow /past-questions/.

Run:  python scripts/scrape_testdriller.py [--sleep 0.4] [--max-q 60]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "data" / "extracted"
CACHE = ROOT / "data" / "raw" / "tdw_cache"

BASE = "https://www.testdriller.com/past-questions"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

SUBJECTS = {
    "biology": "Biology",
    "chemistry": "Chemistry",
    "physics": "Physics",
    "economics": "Economics",
}

# Probed Sept 2026: the sciences have 2010-2021, Economics only 2010-2011.
# Government (and every other WAEC subject, under any slug variant tried)
# returns 404 — the site simply does not publish them.
SUBJECT_YEARS = {
    "biology": range(2010, 2022),
    "chemistry": range(2010, 2022),
    "physics": range(2010, 2022),
    "economics": (2010, 2011),
}


def fetch_html(url: str, cache_path: Path, sleep: float, retries: int = 2) -> str | None:
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        return cache_path.read_text(encoding="utf-8", errors="replace")
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "20", "-H", f"User-Agent: {UA}",
                 "-o", str(cache_path), "-w", "%{http_code}_%{size_download}", url],
                capture_output=True, text=True, timeout=30,
            )
            code, _, size = result.stdout.strip().partition("_")
            if code == "200" and size.isdigit() and int(size) > 1000:
                return cache_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        if attempt < retries:
            time.sleep(sleep * 2)
    return None


def parse_waec_page(html: str) -> dict | None:
    """Extract {prompt, options, correctOptionId} from a question page.

    Stripped-text shape: '... Biology > 2020 > 21 WASSCE {question} A. x
    B. y ... Answer: C To see detailed solution ...'
    The question body is everything after the LAST 'WASSCE' marker before
    'Answer:' (earlier hits are page title/navigation).
    """
    text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    ans = re.search(r"Answer:\s*([A-E])", text)
    if not ans:
        return None
    prefix = text[: ans.start()]
    marker = prefix.rfind("WASSCE")
    if marker == -1:
        return None
    body = prefix[marker + len("WASSCE"):].strip()

    split = re.search(r"\s+A\.\s+", body)
    if not split:
        return None
    prompt = body[: split.start()].strip()
    # Keep the leading whitespace: the split pattern anchors on \s+ before
    # each letter, so stripping it would silently drop option A (and any
    # question whose correct answer is A would then fail the letter check).
    options_text = body[split.start():]
    parts = re.split(r"\s+([A-E])\.\s+", options_text)

    options = []
    for i in range(1, len(parts) - 1, 2):
        options.append({"id": parts[i].lower(), "text": parts[i + 1].strip()})
    if len(options) < 2 or not prompt:
        return None

    letters = {o["id"] for o in options}
    correct = ans.group(1).lower()
    if correct not in letters:
        return None
    return {"prompt": prompt, "options": options, "correctOptionId": correct}


def scrape_year(slug: str, year: int, sleep: float, max_q: int) -> list[dict] | None:
    out_path = EXTRACTED / f"tdw_{slug}_{year}.json"
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if existing:
                print(f"  {slug} {year}: cached output ({len(existing)} questions)")
                return existing
        except json.JSONDecodeError:
            pass

    items: list[dict] = []
    misses = 0
    for qnum in range(1, max_q + 1):
        url = f"{BASE}/waec-objective-{slug}-{year}-{qnum}"
        cache_path = CACHE / f"{slug}-{year}-q{qnum}.html"
        from_net = not (cache_path.exists() and cache_path.stat().st_size > 1000)
        html = fetch_html(url, cache_path, sleep)
        if from_net:
            time.sleep(sleep)
        parsed = parse_waec_page(html) if html else None
        if parsed is None:
            misses += 1
            if misses >= 3 and qnum > 5:
                break
            continue
        misses = 0
        parsed["questionNumber"] = qnum
        parsed["year"] = year
        parsed["sourceUrl"] = url
        items.append(parsed)

    if items:
        out_path.write_text(
            json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  {slug} {year}: {len(items)} questions")
    else:
        print(f"  {slug} {year}: none found")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--max-q", type=int, default=60)
    parser.add_argument("--subjects", nargs="*", default=list(SUBJECTS))
    args = parser.parse_args()

    EXTRACTED.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    total = 0
    for slug in args.subjects:
        if slug not in SUBJECTS:
            print(f"unknown subject {slug!r}, skipping")
            continue
        print(f"{SUBJECTS[slug]}:", flush=True)
        for year in SUBJECT_YEARS[slug]:
            items = scrape_year(slug, year, args.sleep, args.max_q)
            total += len(items or [])
    print(f"\nTotal questions: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
