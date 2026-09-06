#!/usr/bin/env python3
"""Rebuild the question bank from REAL extracted past questions only.

Content policy (v3 bank):
  INCLUDE  td_*.*   TestDriller Nigerian BECE objective past questions
  INCLUDE  sng_bst  SchoolNGR.com BECE past questions
  INCLUDE  jamb_*   EduPadi JAMB UTME past questions
  EXCLUDE  bece_*   Kuulchat.com GHANA BECE papers (not Nigerian; keep for a
                    possible Ghana edition later)
  EXCLUDE  ms_*     MySchool.ng forum-recalled questions (unverified keys)
  EXCLUDE  curriculum_*  AI-generated practice items (not past questions)

Output layout (loaded on demand by the app):
  public/data/index.json             — exams + per-subject metadata + counts
  public/data/banks/<subject-id>.json — questions for one subject only

Every shipped question carries a source label; TestDriller/SchoolNGR items
also carry their sourceUrl. Fill-in-the-blank letter prefixes ("A) ...") are
stripped from option texts because the app renders its own option letters.
Duplicate questions within an exam+subject are dropped. Filler explanations
are removed. Questions are tagged with syllabus topics via keyword rules
(first match wins; heuristic, to be refined by teacher review).

Run:  python scripts/build_bank.py
Then: python scripts/validate_questions.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from validate_questions import OPTION_PREFIX_RE, is_junk_explanation

ROOT = Path(__file__).parent.parent
EXTRACTED = ROOT / "data" / "extracted"
DATA_DIR = ROOT / "public" / "data"
BANKS_DIR = DATA_DIR / "banks"
INDEX_PATH = DATA_DIR / "index.json"
LEGACY_MONOLITH = DATA_DIR / "questions.json"

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

# ── Syllabus topic tagging (heuristic; first match wins) ─────────────────
# Specific topics are listed before broad ones so that e.g. "circumference
# of a circle" matches Mensuration rather than Geometry.


def _rx(pattern: str):
    return re.compile(pattern, re.IGNORECASE)


MATH_TOPICS = [
    ("Number Bases", _rx(r"\bbase (two|2|five|5|eight|8|ten|10)\b|\bbinary\b|\bternary\b|convert.*to base")),
    ("Sets & Venn Diagrams", _rx(r"\bset(s)?\b|\bvenn\b|\bunion\b|\bintersection\b|\bsubset\b|\buniversal set\b|\belements of\b")),
    ("Matrices & Determinants", _rx(r"\bmatrix\b|\bmatrices\b|\bdeterminant\b|\bcross product\b")),
    ("Calculus", _rx(r"\bdifferentiat|\bderivative\b|\bintegrat|\bdy/dx\b|d/dx|\blimit\b|\brate of change\b|\bmaximum (point|value)\b|\bminimum (point|value)\b")),
    ("Sequences & Series", _rx(r"\bsequence\b|\bseries\b|\barithmetic progression\b|\bgeometric progression\b|\bAP\b|\bGP\b|\bnth term\b|\bnext (number|term)\b|\bprogression\b")),
    ("Indices & Logarithms", _rx(r"\bindices\b|\bindex\b|\bpower(s)? of\b|\blogarithm\b|\blog\b|\bstandard form\b|\bsurd\b|\bsquare root\b|\bcube root\b|√")),
    ("Variation", _rx(r"\bvaries\b|\bvariation\b|\bdirect (variation|proportion)\b|\binverse\b|\bjoint(ly)? (variation|proportion)\b|\bpartial variation\b")),
    ("Trigonometry", _rx(r"\bsin(e|us)?\b|\bcos(ine)?\b|\btan(gent)?\b|\btrigonometr|\bhypotenuse\b|\bangle of (elevation|depression)\b|\bpythagoras\b|\bbearing\b")),
    ("Mensuration", _rx(r"\barea\b|\bperimeter\b|\bvolume\b|\bsurface area\b|\bcapacity\b|\blitre\b|\bcuboid\b|\bcylinder\b|\bcone\b|\bsphere\b|\bcircumference\b|\bprism\b")),
    ("Probability", _rx(r"\bprobabilit|\bchance\b|\blikely\b|\boutcome\b|\bdice\b|\bcoin\b|\bdie is (thrown|rolled|tossed)\b|\bpack of cards\b")),
    ("Statistics", _rx(r"\bmean\b|\bmedian\b|\bmode\b|\brange\b|\baverage\b|\bfrequency\b|\bbar chart\b|\bpie chart\b|\bhistogram\b|\btally\b|\bdata\b|\bamplitude\b|\bdeviation\b")),
    ("Graphs & Coordinates", _rx(r"\bcoordinate\b|\baxes\b|\bx-axis\b|\by-axis\b|\bplot\b|\bgradient\b|\bintercept\b|\borigin\b|\bgraph\b")),
    ("Ratio & Proportion", _rx(r"\bratio\b|\bproportion\b|\bdivide.*among\b|\bshare(s)?\b.*\bequal|\brate\b")),
    ("Percentages", _rx(r"\bpercent\b|%|\bpercentage\b")),
    ("Financial Arithmetic", _rx(r"\bprofit\b|\bloss\b|\bdiscount\b|\binterest\b|\btax\b|\bsalary\b|\bwages\b|\bcommission\b|\bcost price\b|\bselling price\b|\bmarked price\b|\bbought\b|\bsold\b|\btrading\b|\bVAT\b|\bhire purchase\b")),
    ("Fractions & Decimals", _rx(r"\bfraction\b|\bdecimal\b|\bnumerator\b|\bdenominator\b|\bvulgar\b|\bproper fraction\b|\bimproper\b|\bmixed number\b")),
    ("Algebra", _rx(r"\bsolve for\b|\bsimplify\b|\bexpand\b|\bfactori|\bequation\b|\bexpression\b|\binequalit|\bsimultaneous\b|\bsubstitut|\bcoefficient\b|\blike terms\b|\bbrackets\b|=\s*\?|\bfind x\b|\bvalue of x\b")),
    ("Geometry", _rx(r"\bangle\b|\btriangle\b|\bpolygon\b|\bquadri|\bparallel\b|\bperpendicular\b|\bcircle\b|\bchord\b|\bradius\b|\bdiameter\b|\bsimilar (shapes|triangles)\b|\bcongruent\b|\bvertic(ally|es)\b|\bhorizontal\b|\bpoints? (lie|lies)\b")),
]

TOPIC_MAPS: dict[tuple[str, str], list[tuple[str, re.Pattern]]] = {
    ("BECE", "Mathematics"): MATH_TOPICS,
    ("JAMB", "Mathematics"): MATH_TOPICS,
    ("BECE", "Basic Science"): [
        ("Drugs & Substance Abuse", _rx(r"\bdrug\b|\balcohol\b|\btobacco\b|\bsmoking\b|\bnarcotic\b|\bsubstance abuse\b")),
        ("Light & Sound", _rx(r"\blight\b|\breflection\b|\brefraction\b|\bshadow\b|\bmirror\b|\blens\b|\bsound\b|\becho\b|\bwave\b")),
        ("Electricity & Magnetism", _rx(r"\belectric|\bcurrent\b|\bcircuit\b|\bmagnet|\bfuse\b|\bconductor\b|\binsulator\b|\bvoltage\b|\bbattery\b")),
        ("Heat", _rx(r"\bheat\b|\btemperature\b|\bthermometer\b|\bconduction\b|\bconvection\b|\bradiation\b|\bevaporation\b|\bboiling\b|\bmelting\b")),
        ("Force, Motion & Energy", _rx(r"\bforce\b|\bmotion\b|\bspeed\b|\bvelocity\b|\benergy\b|\bwork\b|\bmachine\b|\bfriction\b|\bgravity\b|\bweight\b|\bbalance\b|\bpush\b|\bpull\b")),
        ("Ecology & Environment", _rx(r"\becolog|\benvironment\b|\becosystem\b|\bfood chain\b|\bhabitat\b|\bpollution\b|\bconservation\b|\bdeforestation\b|\bclimat\b|\bweather\b|\brenewable\b")),
        ("Earth & Space", _rx(r"\bearth\b|\bspace\b|\bplanet\b|\bsolar system\b|\bmoon\b|\bsun\b|\bstar\b|\beclipse\b|\bseason\b|\borbit\b")),
        ("Matter & Materials", _rx(r"\bmatter\b|\belement\b|\bcompound\b|\bmixture\b|\batom\b|\bmolecule\b|\bacid\b|\balkali\b|\bbase\b|\bsalt\b|\bmetal\b|\brust\b|\bchemical\b|\bphysical change\b|\bstate of matter\b")),
        ("Human Body & Health", _rx(r"\bhuman body\b|\bdigest|\bskeleton\b|\bbone\b|\bmuscle\b|\bheart\b|\bblood\b|\blung\b|\bkidney\b|\bbrain\b|\bsense organ\b|\bdisease\b|\bimmuni|\bvaccin\b|\bhealth\b|\bmalnutrition\b|\bhygiene\b")),
        ("Living Things", _rx(r"\bliving thing\b|\bclassif|\bvertebrate\b|\binvertebrate\b|\bmammal\b|\breptile\b|\bplant\b|\banimal\b|\bphotosynthes|\brespiration\b|\bexcretion\b|\breproduction\b|\bcell\b|\bgrowth\b")),
    ],
    ("BECE", "Agricultural Science"): [
        ("Fisheries", _rx(r"\bfish\b|\baquaculture\b|\bpond\b")),
        ("Forestry & Wildlife", _rx(r"\bforest\b|\bdeforestation\b|\bafforestation\b|\btimber\b|\bwildlife\b|\bgame reserve\b")),
        ("Farm Tools & Machinery", _rx(r"\btool\b|\bimplement\b|\bmachinery\b|\btractor\b|\bplough\b|\bhoe\b|\bcutlass\b|\bsprayer\b|\bharvester\b|\bsickle\b")),
        ("Pest & Disease Control", _rx(r"\bpest\b|\bdisease\b|\binsect\b|\bfungus\b|\bfungal\b|\bpesticide\b|\binsecticide\b|\bherbicide\b|\bweedic|\bpathogen\b|\bparasite\b")),
        ("Soil Science", _rx(r"\bsoil\b|\bclay\b|\bloam\b|\bsandy\b|\bfertilit|\bmanure\b|\bcompost\b|\bhumus\b|\berosion\b|\bfallow\b|\bmulch")),
        ("Farm Management & Marketing", _rx(r"\brecord\b|\bfarm planning\b|\bbudget\b|\bmarketing\b|\bcooperative\b|\bextension\b|\bsubsid\b|\bcredit\b|\bagricultural bank\b|\bfarm account")),
        ("Farming Systems", _rx(r"\bfarming system\b|\bshifting cultivation\b|\bcrop rotation\b|\bmixed farming\b|\bsubsis?tence\b|\bcommercial farming\b|\birrigation\b|\bdrainage\b|\bland tenure\b|\bplantation\b|\bterracing\b")),
        ("Animal Husbandry", _rx(r"\banimal\b|\bcattle\b|\bgoat\b|\bsheep\b|\bpoultry\b|\bchicken\b|\bbird\b|\blivestock\b|\bfeed(ing)?\b|\bbreed\b|\begg\b|\bdairy\b|\bmilk\b|\bbeef\b|\bruminant\b|\bhive\b|\bbee\b|\bpig\b|\brabbit\b")),
        ("Crop Production", _rx(r"\bcrop\b|\bmaize\b|\bcassava\b|\byam\b|\brice\b|\bcocoa\b|\bgroundnut\b|\bcotton\b|\bpalm\b|\bplanting\b|\bseed\b|\bnursery\b|\bweed(ing)?\b|\bharvest\b|\bpropagat\b|\bgerminat\b|\bfertiliz(er|ation)\b|\bnursery\b|\bstore?d? (produce|grain)\b")),
    ],
    ("BECE", "Civic Education"): [
        ("Law Enforcement Agencies", _rx(r"\bNDLEA\b|\bNAFDAC\b|\bpolice\b|\bEFCC\b|\bICPC\b|\bcustoms\b|\bimmigration\b|\bprison\b|\bcorrectional\b|\bfire service\b|\bagency\b|\bsecurity\b")),
        ("Constitution & Rule of Law", _rx(r"\bconstitution\b|\brule of law\b|\bseparation of powers\b|\barm(s)? of government\b|\blegislature\b|\bjudiciary\b|\bexecutive\b|\bimpeach\b|\bsection \d|\bchapter\b|\bamendment\b|\bfederal character\b|\bsupremacy\b|\bprivatization\b|\bnational assembly\b|\bsenate\b|\bhouse of (assembly|representatives)\b")),
        ("Democracy & Elections", _rx(r"\belect\b|\bvote\b|\bINEC\b|\bballot\b|\bdemocra\b|\bconstituency\b|\bcampaign\b|\bfranchise\b|\breferendum\b|\bprimaries\b|\bpolitical part")),
        ("Human Rights", _rx(r"\brights?\b|\bliberty\b|\bfreedom of\b|\bhabeas corpus\b|\bdiscriminat\b|\bdignity\b")),
        ("National Unity & Symbols", _rx(r"\bnation(al)? (unity|consciousness|anthem|flag|pledge|symbol|colour)\b|\banthem\b|\bflag\b|\bmotto\b|\bpledge\b|\bcoat of arms\b|\bpatriotis|\btribalis|\bethnic\b|\bnationalis|\bsecession\b|\bNYSC\b|\bmotto\b")),
        ("Drug Abuse & Social Vices", _rx(r"\bdrug\b|\bnarcotic\b|\balcohol\b|\btrafficking\b|\bkidnapp\b|\bcultism\b|\bHIV\b|\bSTD\b|\bexamination malpractice\b|\briot\b|\bvandalism\b")),
        ("Family & Child Development", _rx(r"\bfamily\b|\bmarriage\b|\bchild(ren)?'s? right\b|\bChild's Rights\b|\borphan\b|\bguardian\b|\bparent\b|\badolesc\w+|\bpeer\b|\bpopulation\b|\bfertility rate\b|\bfamily life\b")),
        ("Public Service & Institutions", _rx(r"\bpublic service\b|\bcivil service\b|\bparastatal\b|\bministry\b|\blocal government\b|\bcouncil\b|\btraditional ruler\b|\bemir\b|\boba\b|\bchieftaincy\b|\bpublic corporation\b")),
        ("Values & Good Citizenship", _rx(r"\bvalue\b|\bhonesty\b|\bintegrity\b|\bdiscipline\b|\bcorrupt\b|\bcontentment\b|\bcourage\b|\bempathy\b|\bself-relian|\bduties\b|\bobligation\b|\bcitizenship\b|\bcitizen\b|\bnational consciousness\b")),
    ],
    ("BECE", "History"): [
        ("Sources of History", _rx(r"\bsource(s)? of history\b|\boral tradition\b|\barchaeolog\b|\bartifact\b|\bexcavat\b|\bcarbon dating\b|\bwritten source\b|\bhistorian\b")),
        ("Early States & Empires", _rx(r"\bKanem(-| )?Bornu\b|\bHausa\b|\bOyo\b|\bBenin (Empire|Kingdom)\b|\bNupe\b|\bIgbo-?Ukwu\b|\bNok\b|\bIfe\b|\bSokoto\b|\bcaliphate\b|\bjihad\b|\bdan Fodio\b|\bempire\b|\bkingdom\b|\bcity-?state\b|\bGhana (Empire|empire)\b|\bMali\b|\bSonghai\b|\bKanuri\b|\bTiv\b|\bIbibio\b|\bEfik\b")),
        ("Trans-Saharan & Slave Trade", _rx(r"\btrans-?saharan\b|\bsaharan trade\b|\bslave trade\b|\btrans-?atlantic\b|\bmiddle passage\b|\babolition\b|\btriangular trade\b|\bslaves?\b")),
        ("Colonial Rule", _rx(r"\bcolonial\b|\bBritish\b|\bprotectorate\b|\bindirect rule\b|\bLugard\b|\bamalgamation\b|\bmissionar\b|\bpacification\b|\bannexed\b|\bcolon(ial|y|ization)\b|\bresidence\b")),
        ("Nationalism & Independence", _rx(r"\bnationalis\b|\bindependen\b|\bAzikiwe\b|\bAwolowo\b|\bAhmadu Bello\b|\bMacaulay\b|\bself-?government\b|\bself rule\b|\brepublic\b|\b1 October 1960\b|\bconstitution( of)? 19(5|6)\d\b|\bconferences?\b")),
        ("Post-Independence Nigeria", _rx(r"\bcoup\b|\bcivil war\b|\bBiafra\b|\bmilitary (rule|regime|government)\b|\boil boom\b|\bSecond Republic\b|\btransition\b|\b1999\b|\bdemocratic rule\b|\bShagari\b|\bObasanjo\b|\bAbacha\b|\bBabangida\b|\bGowon\b|\bIronsi\b")),
        ("People, Culture & Economy", _rx(r"\bculture\b|\btradition\b|\bfestival\b|\breligion\b|\bindigenous\b|\bpre-?colonial\b|\btrade route\b|\beconomy\b|\bbarter\b|\bsmith\b|\bweav(e|ing)\b|\bsculpture\b")),
    ],
    ("BECE", "Home Economics"): [
        ("Clothing & Textiles", _rx(r"\bclothing\b|\bfabric\b|\btextile\b|\bsew|\bstitch\b|\bgarment\b|\bwardrobe\b|\bfashion\b|\bfibre\b|\bfiber\b|\byarn\b|\bweav(e|ing)\b|\btie-?dye\b")),
        ("Food & Nutrition", _rx(r"\bfood\b|\bnutrient\b|\bprotein\b|\bcarbohydrate\b|\bvitamin\b|\bmineral\b|\bdiet\b|\bmeal\b|\bcook|\brecipe\b|\bkitchen\b|\bfood poisoning\b|\bbalanced\b|\bflour\b|\bbak(e|ing)\b|\bmenu\b")),
        ("Home Management & Housing", _rx(r"\bhome management\b|\bhouse(hold|ing)?\b|\bclean(ing|liness)\b|\bfurniture\b|\blaundry\b|\blinen\b|\bfamily resource\b|\bbudget(ing)?\b|\bhousekeep|\bsitting room\b|\bbedroom\b|\bkitchen layout\b|\bventilation\b")),
        ("Family Living & Child Care", _rx(r"\bfamily\b|\bmarriage\b|\bparenting\b|\bchild (development|care)\b|\badolesc|\bpeer\b|\bpregnan\b|\bbab(y|ies)\b")),
        ("Consumer Education", _rx(r"\bconsumer\b|\bbuying\b|\badulterat\b|\bshopping\b|\blabel\b|\bexpiration\b|\bmarket\b|\bmoney\b")),
        ("Personal Health & Hygiene", _rx(r"\bhygiene\b|\bcleanliness\b|\btoilet\b|\bsleep\b|\bexercise\b|\bposture\b|\bgrooming\b|\bself-care\b")),
    ],
    ("JAMB", "English Language"): [
        ("Phonetics", _rx(r"\bvowel\b|\bconsonant\b|\bdiphthong\b|\bsyllable\b|\bstress\b|\btranscription\b|\bphoneme\b|\brhyme\b|\bsilent (letter|consonant)\b|\bpronounced\b|\bphonetic\b|/əʊ/|/uː/|/ɪ/|/æ/|/θ/|/ð/")),
        ("Idioms & Figurative Language", _rx(r"\bidiom\b|\bfigurative\b|\bmetaphor\b|\bsimile\b|\bpersonification\b|\bhyperbole\b|\bparadox\b|\boxymoron\b|\birony\b|\bonomatopoeia\b|\balliteration\b|\banalogy\b")),
        ("Register & Written Communication", _rx(r"\bregister\b|\bformal letter\b|\binformal letter\b|\bessay\b|\bthesis\b|\bparagraph\b|\btopic sentence\b|\bcitation\b|\bstyle guide\b|\bcollocation\b|\bdiaspora\b|\bcode-?switching\b")),
        ("Lexis & Vocabulary", _rx(r"\bclosest in meaning\b|\bopposite in meaning\b|\bsynonym\b|\bantonym\b|\bmeaning of the (word|phrase|expression)\b|\bchoose the word\b|\bnearest in meaning\b|\bfill in the gap\b|\blexical\b")),
        ("Grammar", _rx(r"\btense\b|\bverb\b|\bnoun\b|\bpronoun\b|\bpreposition\b|\barticle\b|\bconcord\b|\bsubject-?verb\b|\badverb\b|\badjective\b|\bplural\b|\bsingular\b|\bclause\b|\bphrase\b|\bpassive\b|\bactive voice\b|\breported speech\b|\bdirect speech\b|\bquestion tag\b|\bmodal\b|\bconditional\b")),
        ("Sentence Structure & Punctuation", _rx(r"\bsentence (type|structure)\b|\bsimple sentence\b|\bcompound sentence\b|\bcomplex sentence\b|\bpunctuation\b|\bsemicolon\b|\bcomma\b|\bfull stop\b|\bspelling\b|\barrange.*sentence|\bdangling\b|\bcleft\b")),
    ],
}

COMPREHENSION_MIN_LEN = 600  # JAMB English passage prompts exceed this


def tag_topic(exam: str, subject: str, prompt: str, option_texts: list[str]) -> str | None:
    if (exam, subject) == ("JAMB", "English Language") and len(prompt) >= COMPREHENSION_MIN_LEN:
        return "Comprehension"
    rules = TOPIC_MAPS.get((exam, subject))
    if not rules:
        return None
    text = prompt + " | " + " | ".join(option_texts)
    for topic, rx in rules:
        if rx.search(text):
            return topic
    return None


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
        if topic and topic.lower() not in TOPIC_BLACKLIST:
            question["topic"] = topic
        if source:
            question["source"] = source
        if source_url:
            question["sourceUrl"] = source_url
        self.seen[key] = qid
        self.questions.append(question)
        return True

    def apply_topic_tags(self) -> dict[tuple[str, str], int]:
        """Tag questions with syllabus topics; returns tagging stats."""
        tagged = 0
        for q in self.questions:
            topic = tag_topic(
                q["exam"],
                q["subject"],
                q["prompt"],
                [o["text"] for o in q["options"]],
            )
            if topic:
                q["topic"] = topic
                tagged += 1
            elif "topic" in q:
                del q["topic"]
        return {("tagged", f"{tagged}/{len(self.questions)}"): tagged}


def load_td(bank: Bank) -> None:
    """TestDriller format: already close to app schema, carries sourceUrl."""
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
                if isinstance(o, dict):
                    text = strip_prefix(o.get("text") or "")
                else:
                    text = strip_prefix(str(o))
                options.append({"id": chr(ord("a") + i), "text": text})
            ok = bank.add(
                exam=exam,
                subject=subject,
                year=year,
                prompt=item.get("prompt") or item.get("question"),
                options=options,
                correct_option_id=(item.get("correctOptionId") or "").lower(),
                number=item.get("questionNumber") or added + 1,
                explanation=item.get("explanation"),
                source=source,
                source_url=url or None,
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


def emit(bank: Bank) -> None:
    """Write public/data/index.json + public/data/banks/<subject>.json."""
    if BANKS_DIR.exists():
        for old in BANKS_DIR.glob("*.json"):
            old.unlink()
    BANKS_DIR.mkdir(parents=True, exist_ok=True)

    subjects_meta: list[dict] = []
    by_key: dict[tuple[str, str], list[dict]] = {}
    for q in bank.questions:
        by_key.setdefault((q["exam"], q["subject"]), []).append(q)

    for (exam, subject), questions in sorted(by_key.items()):
        sid = f"{slug(exam)}-{slug(subject)}"
        years = Counter(q["year"] for q in questions)
        topics = sorted({q["topic"] for q in questions if q.get("topic")})
        subjects_meta.append(
            {
                "id": sid,
                "exam": exam,
                "name": subject,
                "topics": topics,
                "questionCount": len(questions),
                "years": sorted(years, reverse=True),
                "yearCounts": {str(y): n for y, n in sorted(years.items())},
                "file": f"banks/{sid}.json",
            }
        )
        bank_file = {
            "subject": {"id": sid, "exam": exam, "name": subject},
            "questions": questions,
        }
        with open(BANKS_DIR / f"{sid}.json", "w", encoding="utf-8") as fh:
            json.dump(bank_file, fh, ensure_ascii=False, separators=(",", ":"))

    index = {
        "version": 3,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exams": EXAMS_META,
        "subjects": subjects_meta,
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, separators=(",", ":"))

    # The monolithic bank is superseded by the split layout.
    if LEGACY_MONOLITH.exists():
        LEGACY_MONOLITH.unlink()


def main() -> int:
    if not EXTRACTED.exists():
        print(f"FAIL: {EXTRACTED} not found")
        return 1

    bank = Bank()
    print("Loading real past-question sources:")
    load_td(bank)
    load_sng(bank)
    load_edupadi_jamb(bank)

    bank.apply_topic_tags()

    # Deterministic order helps diffs and review.
    bank.questions.sort(key=lambda q: (q["exam"], q["subject"], q["year"], q["id"]))

    emit(bank)

    per_exam = Counter(q["exam"] for q in bank.questions)
    topic_counts = Counter(q.get("topic") for q in bank.questions if q.get("topic"))
    index_size = INDEX_PATH.stat().st_size / 1024

    print(f"\nWrote index + {len(by_key_len(bank))} subject banks to public/data/")
    print(f"  {len(bank.questions)} questions | index.json {index_size:.1f} KB")
    print("Per exam:", dict(per_exam))
    tagged = sum(1 for q in bank.questions if q.get("topic"))
    print(f"Topic-tagged: {tagged}/{len(bank.questions)}")
    print("Top topics:", topic_counts.most_common(8))
    if bank.dropped:
        print("Dropped:", dict(bank.dropped))
    print(f"Duplicates skipped: {bank.duplicates}")
    return 0


def by_key_len(bank: Bank) -> dict:
    keys = {(q["exam"], q["subject"]) for q in bank.questions}
    return keys


if __name__ == "__main__":
    sys.exit(main())
