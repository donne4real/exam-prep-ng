#!/usr/bin/env python3
"""Scrape past questions from SchoolNGR.com classroom sections.

Each classroom section lists questions for one exam+subject (5 per page);
answers and explanations live on per-question pages:

  listing:  /classroom/{exam}/{subject}?page=N
  question: /classroom/{subject}/{id}

Sections cover BECE, WAEC and NECO English Language and Mathematics —
the gaps TestDriller cannot fill (TestDriller publishes no NECO papers
and no WAEC English/Mathematics). robots.txt allows all paths.

Writes data/extracted/sngc_{exam}_{subject}.json with items shaped like
the tdw_* files (prompt, options, correctOptionId, explanation, year,
sourceUrl). Raw HTML is cached under data/raw/sng_cache/ so a re-run
never re-fetches; output files are only written when a section's
question pages are all cached (interrupt-safe: re-run to resume).

Run:  python scripts/scrape_schoolngr.py [--sleep 0.4] [--max-pages 200]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "data" / "extracted"
CACHE = ROOT / "data" / "raw" / "sng_cache"

BASE = "https://www.schoolngr.com/classroom"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# (exam, subject slug) -> classroom path under /classroom/
SECTIONS = {
    ("BECE", "english-language"): "bece/english-language",
    ("WAEC", "english-language"): "waec/english-language",
    ("WAEC", "mathematics"): "waec/mathematics",
    ("NECO", "english-language"): "neco/english-language",
    ("NECO", "mathematics"): "neco/mathematics",
}

# A question block on a listing page: question-year link, prompt, options,
# then the per-question "view answer" link that carries its id.
BLOCK_RE = re.compile(
    r'<div class="question-block">(.*?)(?=<div class="question-block">|<div class="pagination|$)',
    re.DOTALL,
)
YEAR_RE = re.compile(r"examyear=(\d{4})")
ID_RE = re.compile(rf'class="view-answer-btn"', re.DOTALL)
HREF_RE = re.compile(rf'href="{BASE}/([a-z-]+)/(\d+)"')


def fetch_html(url: str, cache_path: Path, sleep: float, retries: int = 2) -> str | None:
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        return cache_path.read_text(encoding="utf-8", errors="replace")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
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


def collect_ids(exam: str, subject: str, path: str, sleep: float, max_pages: int) -> dict[str, int]:
    """Walk listing pages; returns {question_id: year} in listing order."""
    ids: dict[str, int] = {}
    for page in range(1, max_pages + 1):
        cache_path = CACHE / f"list-{path.replace('/', '-')}-p{page}.html"
        from_net = not (cache_path.exists() and cache_path.stat().st_size > 1000)
        html = fetch_html(f"{BASE}/{path}?page={page}", cache_path, sleep)
        if from_net:
            time.sleep(sleep)
        if not html:
            break
        found = 0
        for block in BLOCK_RE.finditer(html):
            m = HREF_RE.search(block.group(1))
            if not m or m.group(1) != subject:
                continue
            year_m = YEAR_RE.search(block.group(1))
            qid = m.group(2)
            if qid not in ids:
                ids[qid] = int(year_m.group(1)) if year_m else 0
                found += 1
        print(f"  page {page}: +{found} (total {len(ids)})", flush=True)
        if found == 0:
            break
    return ids


OPT_RE = re.compile(r'data-option="([A-E])"[^>]*>\s*<span class="option-label">[A-E]</span>\s*(.*?)</li>', re.DOTALL)
ANSWER_RE = re.compile(r"Correct Answer:</strong>\s*Option\s*([A-E])")
EXPL_RE = re.compile(r'Explanation:</strong>(.*?)</div>', re.DOTALL)
# The question-text div runs until the options div; between them sit promo
# links ("SchoolNGR Classroom", the classroom/cbt banner) that must not
# leak into the prompt.
TEXT_RE = re.compile(r'<div class="question-text">(.*?)<div class="options', re.DOTALL)
PROMO_RE = re.compile(
    r"<a [^>]*classroom/cbt[^>]*>.*?</a>|<a [^>]*>SchoolNGR Classroom</a>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<br\s*/?>|</p>", re.IGNORECASE)


def strip_tags(fragment: str) -> str:
    text = TAG_RE.sub("\n", PROMO_RE.sub("", fragment))
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_question(html: str) -> dict | None:
    tm = TEXT_RE.search(html)
    am = ANSWER_RE.search(html)
    if not tm or not am:
        return None
    options = [{"id": m.group(1).lower(), "text": strip_tags(m.group(2))} for m in OPT_RE.finditer(html)]
    if len(options) < 2:
        return None
    correct = am.group(1).lower()
    if correct not in {o["id"] for o in options}:
        return None
    item = {
        "prompt": strip_tags(tm.group(1)),
        "options": options,
        "correctOptionId": correct,
    }
    em = EXPL_RE.search(html)
    if em:
        explanation = strip_tags(em.group(1))
        if explanation and not explanation.lower().startswith("no "):
            item["explanation"] = explanation
    return item


def scrape_section(exam: str, subject: str, path: str, sleep: float, max_pages: int) -> None:
    out_path = EXTRACTED / f"sngc_{exam.lower()}_{subject}.json"
    if out_path.exists():
        print(f"{exam} {subject}: output exists, skipping")
        return

    print(f"{exam} {subject}: collecting question ids…", flush=True)
    ids = collect_ids(exam, subject, path, sleep, max_pages)
    if not ids:
        print(f"{exam} {subject}: no questions found")
        return

    items: list[dict] = []
    misses = 0
    for n, (qid, year) in enumerate(ids.items(), start=1):
        url = f"{BASE}/{subject}/{qid}"
        cache_path = CACHE / f"q-{subject}-{qid}.html"
        from_net = not (cache_path.exists() and cache_path.stat().st_size > 1000)
        html = fetch_html(url, cache_path, sleep)
        if from_net:
            time.sleep(sleep)
        parsed = parse_question(html) if html else None
        if parsed is None:
            misses += 1
            continue
        year_m = YEAR_RE.search(html or "")
        parsed["questionNumber"] = n
        parsed["year"] = year or (int(year_m.group(1)) if year_m else 0)
        parsed["sourceUrl"] = url
        items.append(parsed)

    out_path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{exam} {subject}: wrote {len(items)} questions ({misses} unparseable)\n", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument("--max-pages", type=int, default=200)
    args = parser.parse_args()

    EXTRACTED.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    for (exam, subject), path in SECTIONS.items():
        scrape_section(exam, subject, path, args.sleep, args.max_pages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
