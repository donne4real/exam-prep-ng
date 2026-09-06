#!/usr/bin/env python3
"""Strict validator for public/data/questions.json.

Run locally:  python scripts/validate_questions.py [path]
Run in CI:    exits non-zero if any error is found, so bad data can never ship.

Checks (errors fail the build):
  - schema: required fields and their types on every question
  - ids: present, non-empty, globally unique
  - options: 2-6 per question, unique ids, non-empty texts
  - answer key: correctOptionId must be one of the option ids
  - option text must not embed its own label prefix ("A) ...", "b. ...")
  - explanation: if present, non-blank and not a known filler pattern
  - duplicates: no repeated question within an exam+subject
  - cross-exam duplicates: same question under two exams is an error
  - metadata: exams/subjects arrays well-formed, every question's
    exam and subject are declared

Warnings (do not fail the build) are printed for review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent / "public" / "data" / "questions.json"

OPTION_PREFIX_RE = re.compile(r"^\(?([A-Ea-e])[\)\].:\-]\s+")

# Fillers produced by earlier bulk-generation runs; none of these help a student.
JUNK_EXPLANATION_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"No official explanation", re.IGNORECASE),
    re.compile(r"\bsee page\b", re.IGNORECASE),
    re.compile(r"is the correct answer based on", re.IGNORECASE),
    re.compile(r"^(?:[IVXivx]+\s*(?:and|,|only)?\s*)+$"),
]

# JAMB English comprehension passages are embedded in the prompt, so allow
# generous length; anything beyond this is a scrape artifact.
MAX_PROMPT_LEN = 6000
MAX_OPTION_LEN = 500
VALID_YEARS = range(1990, 2036)


def is_junk_explanation(text: str | None) -> bool:
    if not text:
        return False  # absent explanation is allowed; junk text is not
    return any(p.search(text) for p in JUNK_EXPLANATION_PATTERNS)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def fingerprint(prompt: str, option_texts: list[str]) -> str:
    return norm(prompt) + "||" + "|".join(sorted(norm(t) for t in option_texts))


def validate(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    exams = data.get("exams")
    subjects = data.get("subjects")
    questions = data.get("questions")

    # ---- top level ----
    if not isinstance(data.get("version"), int):
        errors.append("top-level: 'version' must be an integer")
    if not isinstance(exams, list) or not exams:
        errors.append("top-level: 'exams' must be a non-empty list")
        exams = []
    if not isinstance(subjects, list):
        errors.append("top-level: 'subjects' must be a list")
        subjects = []
    if not isinstance(questions, list) or not questions:
        errors.append("top-level: 'questions' must be a non-empty list")
        questions = []

    exam_ids = [e.get("id") for e in exams if isinstance(e, dict)]
    if len(exam_ids) != len(set(exam_ids)):
        errors.append("exams: duplicate exam ids")
    for e in exams:
        if not isinstance(e, dict):
            errors.append("exams: entry is not an object")
            continue
        for field in ("id", "name", "fullName", "description"):
            if not e.get(field):
                errors.append(f"exams: {e.get('id', '?')} missing '{field}'")
        if not isinstance(e.get("durationMinutes"), (int, float)) or e.get("durationMinutes", 0) <= 0:
            errors.append(f"exams: {e.get('id', '?')} has invalid 'durationMinutes'")

    subject_ids = [s.get("id") for s in subjects if isinstance(s, dict)]
    if len(subject_ids) != len(set(subject_ids)):
        errors.append("subjects: duplicate subject ids")
    declared = {(s.get("exam"), s.get("name")) for s in subjects if isinstance(s, dict)}

    # ---- questions ----
    seen_ids: dict[str, int] = {}
    seen_fingerprints: dict[str, str] = {}  # fingerprint -> question id (within exam+subject)
    cross_exam: dict[str, str] = {}  # fingerprint -> exam

    stats = {"total": len(questions), "dropped_fields": 0}

    for i, q in enumerate(questions):
        ctx = f"questions[{i}]"

        def err(msg: str) -> None:
            errors.append(f"{ctx}: {msg}")

        if not isinstance(q, dict):
            err("not an object")
            continue
        qid = q.get("id")
        ctx = f"{qid or ctx}"

        if not qid or not isinstance(qid, str):
            err("missing or non-string 'id'")
        elif qid in seen_ids:
            err(f"duplicate id (also question #{seen_ids[qid]})")
        else:
            seen_ids[qid] = i

        exam = q.get("exam")
        if exam not in exam_ids:
            err(f"'exam' {exam!r} not declared in exams[]")

        subject = q.get("subject")
        if not subject or not isinstance(subject, str):
            err("missing 'subject'")
        elif (exam, subject) not in declared:
            errors.append(f"{ctx}: subject {subject!r} for exam {exam!r} not declared in subjects[]")

        year = q.get("year")
        if not isinstance(year, int) or year not in VALID_YEARS:
            err(f"'year' {year!r} invalid (expected int in {VALID_YEARS.start}-{VALID_YEARS.stop - 1})")

        prompt = q.get("prompt")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            err("missing or empty 'prompt'")
        elif len(prompt) > MAX_PROMPT_LEN:
            err(f"prompt too long ({len(prompt)} chars)")

        options = q.get("options")
        if not isinstance(options, list) or not (2 <= len(options) <= 6):
            err(f"'options' must be a list of 2-6 entries, got {len(options) if isinstance(options, list) else type(options).__name__}")
            options = []
        else:
            opt_ids: set[str] = set()
            opt_texts: list[str] = []
            for j, o in enumerate(options):
                if not isinstance(o, dict) or not o.get("id") or not o.get("text"):
                    err(f"option[{j}] must be an object with 'id' and 'text'")
                    continue
                if o["id"] in opt_ids:
                    err(f"option[{j}] duplicate option id {o['id']!r}")
                opt_ids.add(o["id"])
                text = o["text"]
                if not text.strip():
                    err(f"option[{j}] empty text")
                if len(text) > MAX_OPTION_LEN:
                    err(f"option[{j}] text too long ({len(text)} chars)")
                if OPTION_PREFIX_RE.match(text):
                    err(f"option[{j}] embeds label prefix: {text[:40]!r}")
                opt_texts.append(text)

            correct = q.get("correctOptionId")
            if correct not in opt_ids:
                err(f"'correctOptionId' {correct!r} not among option ids {sorted(opt_ids)}")

        explanation = q.get("explanation")
        if explanation is not None:
            if not isinstance(explanation, str):
                err("'explanation' must be a string when present")
            elif is_junk_explanation(explanation):
                err(f"filler explanation: {explanation[:60]!r}")

        if prompt and options:
            texts = [o.get("text", "") for o in options if isinstance(o, dict)]
            fp = fingerprint(prompt, texts)
            scope = f"{exam}|{subject}"
            key = f"{scope}|{fp}"
            if key in seen_fingerprints:
                err(f"duplicate of question id {seen_fingerprints[key]} within {exam}/{subject}")
            else:
                seen_fingerprints[key] = str(qid)
            if fp in cross_exam and cross_exam[fp] != exam:
                err(f"same question appears under exams {cross_exam[fp]!r} and {exam!r}")
            else:
                cross_exam[fp] = exam

    stats["dropped_fields"] = 0
    if stats["total"] == 0:
        errors.append("no questions found")

    # ---- summary warnings ----
    per_exam: dict[str, int] = {}
    for q in questions:
        if isinstance(q, dict):
            per_exam[q.get("exam", "?")] = per_exam.get(q.get("exam", "?"), 0) + 1
    for exam_id in exam_ids:
        n = per_exam.get(exam_id, 0)
        if n == 0:
            warnings.append(f"exam {exam_id!r} is declared but has no questions (scaffold only)")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--max-show", type=int, default=10, help="max examples per category to print")
    args = parser.parse_args()

    try:
        with open(args.path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read {args.path}: {exc}")
        return 1

    errors, warnings = validate(data)

    n_questions = len(data.get("questions", []))
    print(f"Validated {args.path}: {n_questions} questions")
    for w in warnings:
        print(f"  WARN: {w}")

    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors[: args.max_show]:
            print(f"  - {e}")
        if len(errors) > args.max_show:
            print(f"  ... and {len(errors) - args.max_show} more")
        return 1

    print("OK: no errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
