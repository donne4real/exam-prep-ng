#!/usr/bin/env python3
"""Rebuild public/data/questions.json from REAL extracted past questions only.

Content policy (v2 bank):
  INCLUDE  td_*.*   TestDriller Nigerian BECE objective past questions
  INCLUDE  sng_bst  SchoolNGR.com BECE past questions
  INCLUDE  jamb_*   EduPadi JAMB UTME past questions
  EXCLUDE  bece_*   Kuulchat.com GHANA BECE papers (not Nigerian; keep for a
                    possible Ghana edition later)
  EXCLUDE  ms_*     MySchool.ng forum-recalled questions (unverified keys)
  EXCLUDE  curriculum_*  AI-generated practice items (not past questions)

Every shipped question carries a source label; TestDriller/SchoolNGR items
also carry their sourceUrl. Fill-in-the-blank letter prefixes ("A) ...") are
stripped from option texts because the app renders its own option letters.
Duplicate questions within an exam+subject are dropped (richest copy wins:
the one with a sourceUrl and topic). Filler explanations are removed.

Run:  python scripts/build_bank.py
Then: python scripts/validate_questions.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_questions import OPTION_PREFIX_RE, is_junk_explanation

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "data" / "extracted"
OUT = ROOT / "public" / "data" / "questions.json"

SUBJECT_NAMES = {
    "agricultural-science": "Agricultural Science",
    "basic-science": "Basic Science",
    "civic-education": "Civic Education",
    "commerce": "Commerce",
    "computer-studies": "Computer Studies",
    "crk": "Christian Religious Knowledge",
    "english": "English Language",
    "english-language": "English Language",
    "history": "History",
    "home-economics": "Home Economics",
    "irk": "Islamic Religious Knowledge",
    "mathematics": "Mathematics",
}

# Generic fallback topics from the old keyword tagger; not useful for the
# weak-topics dashboard, so they are dropped outright.
TOPIC_BLACKLIST = {"", "general", "general science", "general knowledge"}

# td_*.json — file stem -> (exam, source label)
TD_FILES = {
    "td_agricultural-science": ("BECE", "TestDriller BECE past questions"),
    "td_civic-education": ("BECE", "TestDriller BECE past questions"),
    "td_history": ("BECE", "TestDriller BECE past questions"),
    "td_home-economics": ("BECE", "TestDriller BECE past questions"),
    "td_mathematics": ("BECE", "TestDriller BECE past questions"),
}

EXAMS_META = [
    {
        "id": "BECE",
        "name": "BECE",
        "fullName": "Basic Education Certificate Examination",
        "description": "Junior secondary school leaving exam (also called Junior WAEC).",
        "durationMinutes": 60,
    },
    {
        "id": "NECO",
        "name": "NECO",
        "fullName": "National Examinations Council (SSCE)",
        "description": "Senior secondary school leaving exam.",
        "durationMinutes": 60,
    },
    {
        "id": "JAMB",
        "name": "JAMB",
        "fullName": "Joint Admissions and Matriculation Board (UTME)",
        "description": "University entrance examination.",
        "durationMinutes": 40,
    },
    {
        "id": "WAEC",
        "name": "WAEC",
        "fullName": "West African Examinations Council (SSCE)",
        "description": "Senior secondary school leaving exam (West Africa).",
        "durationMinutes": 60,
    },
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def fingerprint(prompt: str, option_texts: list[str]) -> str:
    return norm(prompt) + "||" + "|".join(sorted(norm(t) for t in option_texts))


def clean_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def strip_prefix(text: str) -> str:
    """Remove embedded labels like "A) " or "C. ", including doubled ones.

    The app renders its own option letters, so any leading single-letter
    label is a scrape artifact and gets removed. Scrapes sometimes carry
    doubled labels ("B) A. 2x + 6") or misaligned letters (slot 3 carrying
    "C."), so labels are stripped repeatedly and need not match the slot.
    """
    text = text.strip()
    while True:
        m = OPTION_PREFIX_RE.match(text)
        if not m:
            return text
        rest = text[m.end():].strip()
        if not rest:
            return text
        text = rest


def parse_lettered_options(raw_options: list[str], correct_letter: str) -> tuple[list[dict], str] | None:
    """Convert ["A) x", "B) y"] + correct letter into app-format options.

    Uses embedded letters as ids when every option carries a unique one,
    otherwise falls back to positional ids. Returns (options, correctOptionId)
    or None when the answer key cannot be resolved.
    """
    parsed = []
    for raw in raw_options:
        raw = clean_text(raw)
        m = OPTION_PREFIX_RE.match(raw)
        # The first label (when present on every option) identifies the slot;
        # any further labels are artifacts removed from the text itself.
        parsed.append((m.group(1).lower() if m else None, strip_prefix(raw)))

    embedded = [letter for letter, _ in parsed if letter]
    letters_unique = len(embedded) == len(parsed) and len(set(embedded)) == len(parsed)

    options = []
    for i, (letter, text) in enumerate(parsed):
        oid = letter if letters_unique else chr(ord("a") + i)
        options.append({"id": oid, "text": text})

    correct = (correct_letter or "").lower()
    ids = {o["id"] for o in options}
    if correct in ids:
        return options, correct

    # Positional fallback: "A)" in slot 0 means correct "A" -> id at 0.
    idx = ord(correct) - ord("a")
    if not letters_unique and 0 <= idx < len(options):
        return options, options[idx]["id"]
    return None


def clean_explanation(explanation: str | None) -> str | None:
    text = clean_text(explanation)
    if not text or is_junk_explanation(text):
        return None
    return text


def clean_topic(topic: str | None) -> str | None:
    text = clean_text(topic)
    return text if text and text.lower() not in TOPIC_BLACKLIST else None


class Bank:
    def __init__(self) -> None:
        self.questions: list[dict] = []
        self.seen: dict[str, str] = {}  # "exam|subject|fingerprint" -> id kept
        self.used_ids: set[str] = set()
        self.dropped: dict[str, int] = {}
        self.duplicates = 0

    def _next_id(self, exam: str, subject: str, year: int, number: int) -> str:
        base = f"{slug(exam)}-{slug(subject)}-{year}-q{number:03d}"
        qid, n = base, 2
        while qid in self.used_ids:
            qid = f"{base}-{n}"
            n += 1
        self.used_ids.add(qid)
        return qid

    def add(
        self,
        *,
        exam: str,
        subject: str,
        year: int,
        prompt: str,
        options: list[dict],
        correct_option_id: str,
        number: int,
        topic: str | None = None,
        explanation: str | None = None,
        source: str = "",
        source_url: str | None = None,
        richness: int = 0,
    ) -> bool:
        prompt = clean_text(prompt)
        if not prompt or not (2 <= len(options) <= 6):
            self.dropped["malformed"] = self.dropped.get("malformed", 0) + 1
            return False
        option_ids = {o["id"] for o in options}
        if correct_option_id not in option_ids:
            self.dropped["unresolved answer key"] = self.dropped.get("unresolved answer key", 0) + 1
            return False
        texts = [o["text"] for o in options]
        if any(not t for t in texts):
            self.dropped["empty option text"] = self.dropped.get("empty option text", 0) + 1
            return False

        key = f"{exam}|{subject}|{fingerprint(prompt, texts)}"
        if key in self.seen:
            self.duplicates += 1
            return False

        qid = self._next_id(exam, subject, year, number)
        question = {
            "id": qid,
            "exam": exam,
            "subject": subject,
            "year": year,
            "prompt": prompt,
            "options": options,
            "correctOptionId": correct_option_id,
        }
        explanation = clean_explanation(explanation)
        if explanation:
            question["explanation"] = explanation
        topic = clean_topic(topic)
        if topic:
            question["topic"] = topic
        if source:
            question["source"] = source
        if source_url:
            question["sourceUrl"] = source_url
        self.seen[key] = qid
        self.questions.append(question)
        return True

    def has(self, exam: str, subject: str, prompt: str, texts: list[str]) -> bool:
        return f"{exam}|{subject}|{fingerprint(prompt, texts)}" in self.seen


def load_td(bank: Bank) -> None:
    """TestDriller format: already close to app schema, carries sourceUrl+topic."""
    for stem, (exam, source) in TD_FILES.items():
        path = EXTRACTED / f"{stem}.json"
        if not path.exists():
            continue
        subject = SUBJECT_NAMES[stem.replace("td_", "")]
        with open(path, encoding="utf-8") as fh:
            items = json.load(fh)
        added = 0
        for item in items:
            url = item.get("sourceUrl") or ""
            m = re.search(r"(19|20)\d{2}", url)
            year = int(m.group(0)) if m else 0
            if year == 0:
                bank.dropped["td without year in url"] = bank.dropped.get("td without year in url", 0) + 1
                continue
            raw_opts = item.get("options") or []
            options = []
            for i, o in enumerate(raw_opts):
                letter = chr(ord("a") + i)
                if isinstance(o, dict):
                    text = strip_prefix(o.get("text") or "")
                else:
                    text = strip_prefix(str(o))
                options.append({"id": letter, "text": text})
            ok = bank.add(
                exam=exam,
                subject=subject,
                year=year,
                prompt=item.get("prompt") or item.get("question"),
                options=options,
                correct_option_id=(item.get("correctOptionId") or "").lower(),
                number=item.get("questionNumber") or added + 1,
                topic=item.get("topic"),
                explanation=item.get("explanation"),
                source=source,
                source_url=url or None,
                richness=2,
            )
            added += ok
        print(f"  {stem}: {len(items)} items -> {added} kept")


def load_sng(bank: Bank) -> None:
    """SchoolNGR format: lettered options + correctAnswer letter + year."""
    path = EXTRACTED / "sng_bst.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as fh:
        items = json.load(fh)
    added = 0
    for item in items:
        year = item.get("year") or 0
        parsed = parse_lettered_options(item.get("options") or [], item.get("correctAnswer") or "")
        if not parsed:
            bank.dropped["sng unresolved"] = bank.dropped.get("sng unresolved", 0) + 1
            continue
        options, correct = parsed
        ok = bank.add(
            exam="BECE",
            subject="Basic Science",
            year=year,
            prompt=item.get("question"),
            options=options,
            correct_option_id=correct,
            number=item.get("questionNumber") or added + 1,
            explanation=item.get("explanation"),
            source="SchoolNGR BECE past questions",
            source_url=item.get("sourceUrl"),
        )
        added += ok
    print(f"  sng_bst: {len(items)} items -> {added} kept")


def load_edupadi_jamb(bank: Bank) -> None:
    """EduPadi format: lettered options + correctAnswer + correctAnswerText."""
    added_total = 0
    for path in sorted(EXTRACTED.glob("jamb_*.json")):
        m = re.match(r"jamb_(.+)_(\d{4})\.json$", path.name)
        if not m:
            continue
        subject = SUBJECT_NAMES.get(m.group(1), m.group(1).replace("-", " ").title())
        year = int(m.group(2))
        with open(path, encoding="utf-8") as fh:
            items = json.load(fh)
        added = 0
        for item in items:
            parsed = parse_lettered_options(
                item.get("options") or [], item.get("correctAnswer") or ""
            )
            if not parsed:
                # Last resort: match the provided answer text against options.
                answer_text = norm(item.get("correctAnswerText") or "")
                opts = [
                    {"id": chr(ord("a") + i), "text": strip_prefix(o)}
                    for i, o in enumerate(item.get("options") or [])
                ]
                hit = next((o["id"] for o in opts if norm(o["text"]) == answer_text), None)
                parsed = (opts, hit) if hit else None
            if not parsed:
                bank.dropped["jamb unresolved"] = bank.dropped.get("jamb unresolved", 0) + 1
                continue
            options, correct = parsed
            ok = bank.add(
                exam="JAMB",
                subject=subject,
                year=year,
                prompt=item.get("question"),
                options=options,
                correct_option_id=correct,
                number=item.get("questionNumber") or added + 1,
                explanation=item.get("explanation"),
                source="EduPadi JAMB UTME past questions",
            )
            added += ok
        added_total += added
        print(f"  {path.name}: {len(items)} items -> {added} kept")
    if not added_total:
        print("  (no EduPadi JAMB files found)")


def build_subjects_meta(questions: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, str], set[str]] = {}
    for q in questions:
        by_key.setdefault((q["exam"], q["subject"]), set())
        if q.get("topic"):
            by_key[(q["exam"], q["subject"])].add(q["topic"])
    subjects = [
        {
            "id": f"{slug(exam)}-{slug(subject)}",
            "exam": exam,
            "name": subject,
            "topics": sorted(topics),
        }
        for (exam, subject), topics in sorted(by_key.items())
    ]
    return subjects


def main() -> int:
    if not EXTRACTED.exists():
        print(f"FAIL: {EXTRACTED} not found")
        return 1

    bank = Bank()
    print("Loading real past-question sources:")
    load_td(bank)
    load_sng(bank)
    load_edupadi_jamb(bank)

    # Deterministic order helps diffs and review.
    bank.questions.sort(key=lambda q: (q["exam"], q["subject"], q["year"], q["id"]))

    data = {
        "version": 2,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exams": EXAMS_META,
        "subjects": build_subjects_meta(bank.questions),
        "questions": bank.questions,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

    from collections import Counter

    per_exam = Counter(q["exam"] for q in bank.questions)
    per_subject = Counter(f"{q['exam']}/{q['subject']}" for q in bank.questions)
    size_mb = OUT.stat().st_size / 1024 / 1024

    print(f"\nWrote {len(bank.questions)} questions to {OUT} ({size_mb:.2f} MB)")
    print("Per exam:", dict(per_exam))
    for key, n in sorted(per_subject.items()):
        print(f"  {key}: {n}")
    if bank.dropped:
        print("Dropped:", dict(bank.dropped))
    print(f"Duplicates skipped: {bank.duplicates}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
