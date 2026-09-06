#!/usr/bin/env python3
"""Validate the question bank: strict gate that runs in CI.

Default mode (no arguments) validates the split layout:
  public/data/index.json  +  every public/data/banks/<subject>.json it points to.

  python scripts/validate_questions.py

Legacy mode validates a single monolithic QuestionsFile JSON:

  python scripts/validate_questions.py path/to/questions.json

Checks (errors fail the build):
  - schema: required fields and their types on every question
  - ids: present, non-empty, globally unique across ALL banks
  - options: 2-6 per question, unique ids, non-empty texts
  - answer key: correctOptionId must be one of the option ids
  - option text must not embed its own label prefix ("A) ...", "b. ...")
  - explanation: if present, non-blank and not a known filler pattern
  - duplicates: no repeated question within an exam+subject, and the same
    question must never appear under two different exams
  - index cross-checks (default mode): every subject's declared
    questionCount / years / yearCounts / topics match its bank file exactly

Warnings (do not fail the build) are printed for review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).parent.parent / "public" / "data"
DEFAULT_INDEX = DEFAULT_DATA_DIR / "index.json"

OPTION_PREFIX_RE = re.compile(r"^\(?([A-Ea-e])[\)\].:\-]\s+")

# Fillers produced by earlier bulk-generation runs; none of these help a student.
JUNK_EXPLANATION_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"No official explanation", re.IGNORECASE),
    re.compile(r"\bsee page\b", re.IGNORECASE),
    re.compile(r"is the correct answer based on", re.IGNORECASE),
    # "X is the correct option for this question based on standard <subject>
    # curriculum." and "X is the correct answer to the question about this
    # <subject> concept." — templated fillers, never real explanations.
    re.compile(
        r"is the correct (?:answer|option) (?:for this question|to the question)",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:[IVXivx]+\s*(?:and|,|only)?\s*)+$"),
]

MAX_PROMPT_LEN = 6000  # JAMB English comprehension passages live in the prompt
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


class QuestionChecks:
    """Per-question checks shared by both validation modes."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.seen_ids: dict[str, str] = {}  # id -> bank/ctx label
        self.seen_fingerprints: dict[str, str] = {}  # exam|subject|fp -> id
        self.cross_exam: dict[str, str] = {}  # fp -> exam

    def check_bank(
        self,
        questions: list,
        label: str,
        *,
        expected_exam: str | None = None,
        expected_subject: str | None = None,
    ) -> None:
        for i, q in enumerate(questions):
            ctx = f"{label}[{i}]"

            def err(msg: str) -> None:
                self.errors.append(f"{ctx}: {msg}")

            if not isinstance(q, dict):
                err("not an object")
                continue
            qid = q.get("id")
            ctx = f"{qid or ctx}"

            if not qid or not isinstance(qid, str):
                err("missing or non-string 'id'")
            elif qid in self.seen_ids:
                err(f"duplicate id (also in {self.seen_ids[qid]})")
            else:
                self.seen_ids[qid] = label

            exam = q.get("exam")
            if expected_exam is not None and exam != expected_exam:
                err(f"'exam' {exam!r} != bank subject exam {expected_exam!r}")
            subject = q.get("subject")
            if expected_subject is not None and subject != expected_subject:
                err(f"'subject' {subject!r} != bank subject name {expected_subject!r}")

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
                got = len(options) if isinstance(options, list) else type(options).__name__
                err(f"'options' must be a list of 2-6 entries, got {got}")
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
                key = f"{exam}|{subject}|{fp}"
                if key in self.seen_fingerprints:
                    err(f"duplicate of question id {self.seen_fingerprints[key]} within {exam}/{subject}")
                else:
                    self.seen_fingerprints[key] = str(qid)
                if fp in self.cross_exam and self.cross_exam[fp] != exam:
                    err(
                        f"same question appears under exams {self.cross_exam[fp]!r} and {exam!r}"
                    )
                else:
                    self.cross_exam[fp] = exam


def check_exams_meta(exams: list, errors: list[str]) -> None:
    if not isinstance(exams, list) or not exams:
        errors.append("exams: must be a non-empty list")
        return
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


def validate_index_and_banks(index_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {index_path}: {exc}"], []

    if not isinstance(index.get("version"), int):
        errors.append("index: 'version' must be an integer")
    check_exams_meta(index.get("exams") or [], errors)
    exam_ids = [e.get("id") for e in index.get("exams", []) if isinstance(e, dict)]
    subjects = index.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        errors.append("index: 'subjects' must be a non-empty list")
        return errors, warnings

    subject_ids = [s.get("id") for s in subjects if isinstance(s, dict)]
    if len(subject_ids) != len(set(subject_ids)):
        errors.append("index: duplicate subject ids")

    checks = QuestionChecks()
    per_exam_counts: Counter = Counter()

    for s in subjects:
        sid = s.get("id") if isinstance(s, dict) else None
        label = f"subjects[{sid!r}]"
        if not sid:
            errors.append(f"{label}: missing 'id'")
            continue
        for field in ("exam", "name", "file"):
            if not s.get(field):
                errors.append(f"{label}: missing '{field}'")
        if s.get("exam") not in exam_ids:
            errors.append(f"{label}: exam {s.get('exam')!r} not declared in exams[]")
        years = s.get("years")
        if not isinstance(years, list) or not years or not all(
            isinstance(y, int) and y in VALID_YEARS for y in years
        ):
            errors.append(f"{label}: 'years' must be a non-empty list of valid years")
        if years != sorted(years, reverse=True):
            errors.append(f"{label}: 'years' must be sorted newest-first")

        bank_path = index_path.parent / s.get("file", "")
        if not bank_path.exists():
            errors.append(f"{label}: bank file {s.get('file')!r} not found")
            continue
        try:
            with open(bank_path, encoding="utf-8") as fh:
                bank = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: cannot read bank file: {exc}")
            continue

        questions = bank.get("questions")
        if not isinstance(questions, list) or not questions:
            errors.append(f"{label}: bank file has no questions")
            continue

        checks.check_bank(questions, str(bank_path.relative_to(index_path.parent.parent)), expected_exam=s.get("exam"), expected_subject=s.get("name"))

        # Cross-check the index metadata against the bank contents.
        if s.get("questionCount") != len(questions):
            errors.append(
                f"{label}: questionCount {s.get('questionCount')} != {len(questions)} in bank"
            )
        actual_years = Counter(q.get("year") for q in questions)
        if sorted(actual_years, reverse=True) != s.get("years"):
            errors.append(f"{label}: 'years' does not match bank contents")
        year_counts = {str(y): n for y, n in year_int_keys(actual_years).items()}
        if year_counts != s.get("yearCounts"):
            errors.append(f"{label}: 'yearCounts' does not match bank contents")
        actual_topics = sorted({q.get("topic") for q in questions if q.get("topic")})
        if actual_topics != (s.get("topics") or []):
            errors.append(f"{label}: 'topics' does not match bank contents")

        per_exam_counts[s.get("exam", "?")] += len(questions)

    for exam_id in exam_ids:
        if per_exam_counts.get(exam_id, 0) == 0:
            warnings.append(f"exam {exam_id!r} is declared but has no questions (scaffold only)")

    return errors + checks.errors, warnings + checks.warnings


def year_int_keys(counter: Counter) -> Counter:
    out = Counter()
    for y, n in counter.items():
        if isinstance(y, int):
            out[y] = n
    return out


def validate_single_file(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {path}: {exc}"], []

    if not isinstance(data.get("version"), int):
        errors.append("top-level: 'version' must be an integer")
    check_exams_meta(data.get("exams") or [], errors)
    subjects = data.get("subjects")
    if not isinstance(subjects, list):
        errors.append("top-level: 'subjects' must be a list")
        subjects = []
    declared = {(s.get("exam"), s.get("name")) for s in subjects if isinstance(s, dict)}
    exam_ids = [e.get("id") for e in data.get("exams", []) if isinstance(e, dict)]

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("top-level: 'questions' must be a non-empty list")
        questions = []

    checks = QuestionChecks()
    checks.check_bank(questions, str(path))
    errors.extend(checks.errors)

    for q in questions:
        if isinstance(q, dict) and (q.get("exam"), q.get("subject")) not in declared:
            if q.get("exam") in exam_ids:
                errors.append(
                    f"{q.get('id')}: subject {q.get('subject')!r} for exam {q.get('exam')!r} not declared in subjects[]"
                )

    per_exam = Counter(q.get("exam") for q in questions if isinstance(q, dict))
    for exam_id in exam_ids:
        if per_exam.get(exam_id, 0) == 0:
            warnings.append(f"exam {exam_id!r} is declared but has no questions (scaffold only)")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="a monolithic questions JSON file (omit to validate index + banks)",
    )
    parser.add_argument("--max-show", type=int, default=10)
    args = parser.parse_args()

    if args.path is not None:
        errors, warnings = validate_single_file(args.path)
        total = sum(1 for _ in open(args.path, encoding="utf-8"))  # cheap presence marker
        print(f"Validated {args.path}")
    else:
        if not DEFAULT_INDEX.exists():
            print(f"FAIL: {DEFAULT_INDEX} not found — run scripts/build_bank.py first")
            return 1
        errors, warnings = validate_index_and_banks(DEFAULT_INDEX)
        with open(DEFAULT_INDEX, encoding="utf-8") as fh:
            index = json.load(fh)
        total = sum(s.get("questionCount", 0) for s in index.get("subjects", []))
        bank_files = len(index.get("subjects", []))
        print(f"Validated {DEFAULT_INDEX} + {bank_files} bank files ({total} questions)")

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
