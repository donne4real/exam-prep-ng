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
    # ── WAEC SSCE sciences & social sciences ─────────────────────────────
    ("WAEC", "Biology"): [
        ("Health & Diseases", _rx(r"\bdisease\b|\bmalaria\b|\bplasmodium\b|\bpathogen\b|\bimmun|\bvaccin\b|\bantibod|\bantigen\b|\bAIDS\b|\bHIV\b|\bcholera\b|\btyphoid\b|\btuberculosis\b|\bmeasles\b|\bringworm\b|\bhygiene\b|\bdrug abuse\b|\bmosquito\b")),
        ("Genetics & Heredity", _rx(r"\bgene\b|\bgenetic\b|\bchromosome\b|\bDNA\b|\bMendel\b|\bheredit|\ballel|\bdominan|\brecessiv|\bgenotype\b|\bphenotype\b|\bsickle cell\b|\bhaemophilia\b|\bcolour blindness\b|\bsex-linked\b|\bmutation\b|\bhybrid\b|\bsegregation\b|\btest cross\b")),
        ("Evolution & Adaptation", _rx(r"\bevolut|\badapt(ation|ed)\b|\bnatural selection\b|\bLamarck\b|\bDarwin\b|\bspeciation\b|\bfossil\b|\bvariation\b|\bprotective coloration\b|\bmimicry\b")),
        ("Ecology & Ecosystem", _rx(r"\becolog|\becosystem\b|\bhabitat\b|\bniche\b|\bfood chain\b|\bfood web\b|\btrophic\b|\bpyramid of\b|\bsymbio|\bcommensal|\bmutualis|\bparasitism\b|\bpredat|\bconservation\b|\bpollution\b|\bdeforestation\b|\bbiome\b|\bsavanna\b|\bpopulation (growth|density|census)\b")),
        ("Nervous & Hormonal Control", _rx(r"\bneurone\b|\bnerve\b|\breflex\b|\bbrain\b|\bspinal cord\b|\bsynapse\b|\binsulin\b|\badrenal|\bhormone\b|\breceptor\b|\beye\b|\bear\b|\bmuscle contraction\b|\bcoordination\b")),
        ("Locomotion & Support", _rx(r"\bskeleton\b|\bbone\b|\bjoint\b|\bmuscle\b|\blocomot|\bflagell|\bcilia\b|\bpseudopod|\bvertebral\b|\bappendage\b|\bribcage\b")),
        ("Reproduction", _rx(r"\breproduct|\bgamete\b|\bsperm\b|\bovum\b|\bpollinat|\bfertiliz|\bseed\b|\bgerminat|\bmenstrual\b|\bpregnan|\bplacenta\b|\bovulat|\bconjugat|\bspore\b|\bbinary fission\b|\bbudding\b|\bflower\b|\bfruit\b|\bpuberty\b")),
        ("Excretion", _rx(r"\bexcret|\bkidney\b|\bnephron\b|\bliver\b|\burea\b|\burine\b|\bsweat\b|\bflame cell\b|\bammontelism\b|\buricotelism\b")),
        ("Respiration & Gaseous Exchange", _rx(r"\brespirat|\bglycolysis\b|\bkrebs\b|\banaerobic\b|\baerobic\b|\bgaseous exchange\b|\blung\b|\btrachea\b|\bbreathing\b|\bstomata\b|\blenticel\b")),
        ("Transport Systems", _rx(r"\bheart\b|\bblood\b|\bcirculat|\bvein\b|\barte|\bcapillar|\btranspiration\b|\btranslocation\b|\bxylem\b|\bphloem\b|\broot (hair|pressure)\b|\blymph\b|\bplatelet\b|\bplasma\b|\bmycorrhiza\b")),
        ("Nutrition", _rx(r"\bnutrition\b|\bphotosynthes|\benzyme\b|\bdigest|\bfood (class|test)\b|\bcarbohydrate\b|\bprotein\b|\bfat\b|\bvitamin\b|\bmineral salt\b|\bbalanced diet\b|\bautotroph|\bheterotroph|\bsaprophyt|\bholozoic\b|\bfeeding\b|\bmouth\b|\bdentition\b")),
        ("Cell Structure & Organisation", _rx(r"\bcell\b|\borganelle\b|\bmitochondr|\bnucleus\b|\bchloroplast\b|\bmembrane\b|\btissue\b|\bplasmolysis\b|\bosmosis\b|\bdiffusion\b|\bprokaryot|\beukaryot|\bmicroscope\b|\bvacuole\b|\bribosome\b")),
        ("Classification & Diversity", _rx(r"\bclassif|\bkingdom\b|\bphylum\b|\bspecies\b|\bgenus\b|\bbinomial\b|\bvertebrat|\binvertebrat|\bmammal\b|\breptile\b|\bamphibian\b|\binsect\b|\bfungi\b|\bbacterium\b|\bbacteria\b|\bvirus\b|\bprotozoa\b|\balgae\b|\bfern\b|\bmoss\b|\bbryophyt|\bpteridophyt")),
    ],
    ("WAEC", "Chemistry"): [
        ("Atomic Structure & Periodicity", _rx(r"\batom\b|\bproton\b|\bneutron\b|\belectron (shell|configuration|arrangement)\b|\batomic number\b|\bmass number\b|\bisotope\b|\bperiodic (table|law)\b|\btransition element\b|\bionization energy\b|\batomic radius\b|\belectronegativ|\bgroup (1|2|7|17|18|0)\b")),
        ("Chemical Bonding", _rx(r"\bbond\b|\bionic\b|\bcovalent\b|\bmetallic bond\b|\bdative\b|\bhydrogen bond\b|\bvan der Waals\b|\blattice\b|\bmolecule (shape|shape)\b|\bVSEPR\b|\bintermolecular\b")),
        ("Electrochemistry & Redox", _rx(r"\belectroly|\belectrode\b|\banode\b|\bcathode\b|\belectroplating\b|\bFaraday\b|\bcorrosion\b|\brust\b|\boxidation\b|\breduction\b|\bredox\b|\boxidation number\b|\bdisplacement\b|\bhalf-cell\b")),
        ("Acids, Bases & Salts", _rx(r"\bacid\b|\bacidic\b|\bbase\b|\balkali\b|\bsalt\b|\bpH\b|\bneutrali[sz]\b|\btitration\b|\bhydrolysis\b|\bbuffer\b|\bindicator\b|\bdeliquescent\b|\befflorescent\b")),
        ("Stoichiometry & Mole Concept", _rx(r"\bmole\b|\bAvogadro\b|\bmolar (mass|volume|solution)\b|\bstoichiometr|\bempirical formula\b|\bmolecular formula\b|\bpercentage (composition|purity)\b|\byield\b|\blimiting reactant\b|\bstandard solution\b")),
        ("States of Matter & Gas Laws", _rx(r"\bgas law|\bBoyle\b|\bCharles\b|\bideal gas\b|\bstates of matter\b|\bmelting\b|\bboiling\b|\bsublimation\b|\beffusion\b|\bkinetic theory\b|\bvapour\b|\bdiffusion\b|\bpressure\b")),
        ("Energy, Rates & Equilibrium", _rx(r"\bexothermic\b|\bendothermic\b|\benthalpy\b|\bactivation energy\b|\brate of reaction\b|\bcatalyst\b|\bequilibrium\b|\bLe Chatelier\b|\breversible reaction\b|\bcollision theory\b")),
        ("Organic Chemistry", _rx(r"\balkane\b|\balkene\b|\balkyne\b|\balcohol\b|\balkanol\b|\balkanoic\b|\bester\b|\bether\b|\baldehyde\b|\bketone\b|\bhydrocarbon\b|\bhomologous series\b|\bisomer\b|\bcracking\b|\bpolymer\b|\bfermentation\b|\bsaponification\b|\bbenzene\b|\bpetroleum\b|\bcrude oil\b|\bsoap\b|\bfat and oil\b")),
        ("Metals & Their Compounds", _rx(r"\bmetal\b|\balloy\b|\bextraction\b|\bblast furnace\b|\bore\b|\bsodium\b|\bpotassium\b|\bcalcium\b|\baluminium\b|\biron\b|\bcopper\b|\bzinc\b|\btin\b|\blead\b|\bsilver\b|\bgold\b|\blimestone\b|\bcement\b|\bglass\b|\braw material")),
        ("Non-metals & Their Compounds", _rx(r"\bhydrogen\b|\boxygen\b|\bchlorine\b|\bnitrogen\b|\bsulphur\b|\bsulfur\b|\bammonia\b|\bwater\b|\bair\b|\bhalogen\b|\bnitrogen cycle\b|\binert gas\b|\bnoble gas\b|\bcarbon (monoxide|dioxide)\b")),
        ("Solutions & Solubility", _rx(r"\bsolution\b|\bsolubility\b|\bsaturated\b|\bconcentration\b|\bsolvent\b|\bsolute\b|\bcolloid\b|\bsuspension\b|\bhard water\b|\bwater treatment\b")),
        ("Laboratory Practice & Analysis", _rx(r"\blaboratory\b|\bapparatus\b|\bburette\b|\bpipette\b|\bflame test\b|\btest for\b|\bqualitative analysis\b|\bprecipitate\b|\bdrying\b|\bfunnel\b")),
    ],
    ("WAEC", "Physics"): [
        ("Measurement & Units", _rx(r"\bmeasurement\b|\bunit\b|\bdimension\b|\bvernier\b|\bmicrometer screw\b|\bpendulum\b|\baccuracy\b|\bprecision\b|\bsignificant figure\b|\bstopwatch\b")),
        ("Modern Physics", _rx(r"\bradioact|\bnuclear\b|\bfusion\b|\bfission\b|\bphotoelectric\b|\bx-ray\b|\bquantum\b|\bhalf-life\b|\benergy level\b|\bnucleus\b|\bradiation\b")),
        ("Electronics", _rx(r"\bsemiconductor\b|\bdiode\b|\btransistor\b|\brectif|\bamplifier\b|\blogic gate\b|\bthermionic\b|\bvalve\b|\bnpn\b|\bpnp\b")),
        ("Magnetism & Electromagnetism", _rx(r"\bmagnet\b|\bmagnetic field\b|\belectromagnet\b|\binduction\b|\btransformer\b|\bgenerator\b|\bdynamo\b|\bmotor\b|\bsolenoid\b|\bcompass\b|\bLenz\b|\bFleming\b")),
        ("Electricity", _rx(r"\bcurrent\b|\bvoltage\b|\bpotential difference\b|\bresistance\b|\bOhm\b|\bcircuit\b|\bseries\b|\bparallel\b|\bammeter\b|\bvoltmeter\b|\bbattery\b|\be\.m\.f\b|\bresistivity\b|\bcapacitor\b|\bcharge\b|\bfuse\b|\bearth(ing)?\b")),
        ("Waves, Light & Sound", _rx(r"\bwave\b|\blight\b|\breflection\b|\brefraction\b|\blens\b|\bmirror\b|\bimage\b|\bfocal\b|\bdispersion\b|\bspectrum\b|\bcolour\b|\bsound\b|\becho\b|\bresonance\b|\bvibration\b|\bfrequency\b|\bpitch\b|\bdoppler\b|\binterference\b|\bdiffraction\b|\bwavelength\b")),
        ("Heat & Temperature", _rx(r"\bheat\b|\btemperature\b|\bthermometer\b|\bexpansion\b|\bspecific heat\b|\blatent heat\b|\bconduction\b|\bconvection\b|\bradiation\b|\bcelsius\b|\bkelvin\b|\bcalorimet")),
        ("Pressure & Density", _rx(r"\bpressure\b|\bdensity\b|\bupthrust\b|\bArchimedes\b|\bfloat|\bPascal\b|\bmanometer\b|\bbarometer\b|\bhydraulic\b|\batmospheric pressure\b|\bboyle")),
        ("Gravitation & Space", _rx(r"\bgravitat|\bweightlessness\b|\bsatellite\b|\borbit\b|\bescape velocity\b|\bmoon\b|\bplanet\b")),
        ("Circular Motion", _rx(r"\bcircular motion\b|\bcentripetal\b|\bcentrifugal\b|\bangular (velocity|speed|acceleration)\b|\bradian\b")),
        ("Force & Dynamics", _rx(r"\bforce\b|\bNewton\b|\bfriction\b|\bmoment\b|\bmomentum\b|\bimpulse\b|\bcollision\b|\bequilibrium\b|\bresultant\b|\bcentre of gravity\b|\bstability\b|\bacceleration\b")),
        ("Motion & Kinematics", _rx(r"\bmotion\b|\bvelocity\b|\bdisplacement\b|\bspeed\b|\bprojectile\b|\bfree fall\b|\bretardation\b|\buniform\b")),
        ("Work, Energy & Power & Machines", _rx(r"\bwork\b|\benergy\b|\bpower\b|\bkinetic\b|\bpotential\b|\bmachine\b|\befficiency\b|\blever\b|\bpulley\b|\binclined plane\b|\bscrew\b|\bwheel\b|\bgear\b|\bvelocity ratio\b|\bmechanical advantage\b")),
    ],
    ("WAEC", "Economics"): [
        ("International Trade & Finance", _rx(r"\btrade\b|\bimport\b|\bexport\b|\bbalance of (payment|trade)\b|\bcomparative advantage\b|\babsolute advantage\b|\btariff\b|\bquota\b|\bprotection|\bdevaluation\b|\bexchange rate\b|\bforeign exchange\b|\bIMF\b|\bWorld Bank\b|\bECOWAS\b|\bglobali[sz]ation\b|\bterms of trade\b")),
        ("Money, Banking & Finance", _rx(r"\bmoney\b|\bbank\b|\bcentral bank\b|\bcommercial bank\b|\bmonetary policy\b|\bcredit\b|\binflation\b|\bdeflation\b|\bcurrency\b|\bnaira\b|\bfinancial institution\b|\bstock exchange\b|\bmoney market\b|\bcapital market\b|\bnote issuance\b")),
        ("Public Finance & Taxation", _rx(r"\btaxation\b|\btax\b|\bpublic finance\b|\bbudget\b|\bfiscal policy\b|\bgovernment expenditure\b|\brevenue\b|\bnational debt\b|\bsubsid\b|\bdeficit\b")),
        ("National Income & Accounting", _rx(r"\bnational income\b|\bGDP\b|\bGNP\b|\bper capita\b|\bincome accounting\b|\bcircular flow\b|\baggregate demand\b|\baggregate supply\b|\bstandard of living\b")),
        ("Population, Labour & Development", _rx(r"\bpopulation\b|\bcensus\b|\bgrowth rate\b|\bmigration\b|\bunemployment\b|\bemployment\b|\bdevelopment\b|\bunderdevelopment\b|\bpoverty\b|\bhuman capital\b|\boverpopulation\b|\blabour force\b")),
        ("Market Structures", _rx(r"\bperfect competition\b|\bmonopoly\b|\boligopoly\b|\bmonopolistic\b|\bmarket structure\b|\bprice (discrimination|leader|maker|taker)\b")),
        ("Business Organisations", _rx(r"\bsole (proprietorship|trader)\b|\bpartnership\b|\bjoint stock\b|\bcompany\b|\bpublic (corporation|enterprise)\b|\bprivati[sz]\b|\bcooperative\b|\bbusiness organisation\b|\bshareholder\b")),
        ("Agriculture & Industry in Nigeria", _rx(r"\bagricultur|\bcocoa\b|\bgroundnut\b|\bcrude oil\b|\bpetroleum\b|\bmining\b|\bmanufactur|\bSME\b|\bindustriali[sz]\b|\bNNPC\b|\bresource curse\b")),
        ("Demand, Supply & Price", _rx(r"\bdemand\b|\bsupply\b|\bequilibrium price\b|\bquantity demanded\b|\bquantity supplied\b|\bmarket price\b|\bprice mechanism\b|\bcommodity\b")),
        ("Elasticity", _rx(r"\belasticit|\binelastic\b")),
        ("Theory of Consumer Behaviour", _rx(r"\butility\b|\bindifference curve\b|\bconsumer surplus\b|\bbudget line\b|\bmarginal utility\b|\bconsumer behaviour\b|\bconsumer sovereignty\b")),
        ("Production, Cost & Factors", _rx(r"\bproduction\b|\bcost\b|\breturns to scale\b|\beconomies of scale\b|\bdiseconomies\b|\bproduction possibility\b|\bproductivity\b|\bfactor of production\b|\bland\b|\blabour\b|\bcapital\b|\bentrepreneur\b|\bwage\b|\brent\b|\binterest\b|\bprofit\b|\btrade union\b|\bdivision of labour\b|\bspeciali[sz]ation\b")),
        ("Economic Systems & Planning", _rx(r"\beconomic system\b|\bcapitalism\b|\bsocialism\b|\bmixed economy\b|\bcommand economy\b|\bfree enterprise\b|\blaissez|\beconomic planning\b|\brolling plan\b|\bprice control\b")),
        ("Basic Economic Concepts", _rx(r"\bscarcity\b|\bchoice\b|\bopportunity cost\b|\bscale of preference\b|\bwants\b|\bresources\b|\beconomics as a\b|\bdefinition of economics\b|\bbasic economic\b")),
    ],
    ("WAEC", "Government"): [
        ("Pressure Groups & Public Opinion", _rx(r"\bpressure group\b|\binterest group\b|\blobby|\bpublic opinion\b|\bpropaganda\b|\bmass media\b|\bcivil society\b|\bNLC\b|\bNMA\b|\bASUU\b")),
        ("Political Parties & Elections", _rx(r"\bpolitical party\b|\bparty system\b|\bone-?party\b|\btwo-?party\b|\bmulti-?party\b|\belection\b|\belectoral (commission|act|malpractice)\b|\bINEC\b|\bFEDECO\b|\bNECON\b|\bfranchise\b|\bsuffrage\b|\bballot\b|\brigging\b|\bcampaign\b|\bprimaries\b|\bconstituency\b")),
        ("Foreign Policy & International Relations", _rx(r"\bforeign policy\b|\bcentrepiece\b|\bnon-?alignment\b|\bECOWAS\b|\bOAU\b|\bAfrican Union\b|\b\bUN\b|\bUNO\b|\bCommonwealth\b|\bdiplomacy\b|\bdiplomatic\b|\binternational relation\b|\btreaty\b|\bregional integration\b|\bAfrocentric")),
        ("Nigerian Political History", _rx(r"\bFirst Republic\b|\bSecond Republic\b|\bThird Republic\b|\bmilitary (rule|regime|government)\b|\bcoup\b|\bcivil war\b|\bBiafra\b|\bNCNC\b|\bNPC\b|\b\bAG\b|\bNPN\b|\bUPN\b|\bNPP\b|\bPRP\b|\bGNPP\b|\bSDP\b|\bNRC\b|\btransition\b|\bhandover\b|\bAguiyi\b|\bGowon\b|\bMurtala\b|\bObasanjo\b|\bShagari\b|\bBuhari\b|\bBabangida\b|\bAbacha\b|\bAbdulsalami\b")),
        ("Colonialism & Nationalism", _rx(r"\bcolonial|\bindirect rule\b|\bassimilation\b|\bnationalism\b|\bnationalist\b|\bindependence\b|\bamalgamation\b|\bprotectorate\b|\bself-?government\b|\bdecoli[sz]|\bMacaulay\b|\bAzikiwe\b|\bAwolowo\b|\bAhmadu Bello\b|\bLugard\b|\bClifford\b|\bMacpherson\b|\bRichards\b|\bLyttleton\b")),
        ("Constitutions & Constitutional Development", _rx(r"\bconstitution\b|\bRichard\b|\bMacpherson\b|\bClifford\b|\bLyttleton\b|\bindependence constitution\b|\brepublican constitution\b|\b1979\b|\b1999\b|\bamendment\b|\bwritten (constitution)?\b|\bunwritten\b|\brigid\b|\bflexible\b")),
        ("Organs of Government", _rx(r"\blegislature\b|\bexecutive\b|\bjudiciary\b|\bparliament\b|\bcongress\b|\bcourt\b|\bsupreme court\b|\blegislation\b|\bbill\b|\bveto\b|\bimpeach|\bjudicial review\b|\bseparation of powers\b|\bchecks and balances\b|\bcabinet\b|\bquorum\b")),
        ("Federalism & Power Allocation", _rx(r"\bfederalism\b|\bfederal (system|character|government)\b|\bunitary\b|\bconfederation\b|\bdevolution\b|\brevenue allocation\b|\bstate creation\b|\bexclusive list\b|\bconcurrent list\b|\bresidual\b|\blocal government\b|\bFCT\b")),
        ("Citizenship & Rights", _rx(r"\bcitizenship\b|\bnationali[sz]ation\b|\balien\b|\bfundamental human rights\b|\brights\b|\bobligation\b|\bdual citizenship\b|\brule of law\b|\bconstitutionalsim\b|\bconstitutionality\b")),
        ("Public Administration & Civil Service", _rx(r"\bcivil service\b|\bcivil servant\b|\bpublic (corporation|service|office)\b|\bparastatal\b|\bbureaucra|\bombudsman\b|\bcommission\b|\baccountability\b|\bprobity\b")),
        ("Basic Political Concepts", _rx(r"\bstate\b|\bsovereignty\b|\bpower\b|\bauthority\b|\blegitimacy\b|\bpolitical culture\b|\bpolitical sociali[sz]ation\b|\bdemocracy\b|\bgovernment\b|\bnation\b|\bsociety\b|\bideology\b|\bcapitalism\b|\bsocialism\b|\bcommunism\b|\bfascism\b|\bwelfare state\b|\bliberali[sz]|")),
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


# Questions that reference a diagram/figure we cannot ship are unanswerable
# in text-only form ("the part labelled I is..."). Dropped at build time.
DIAGRAM_RE = re.compile(r"\b(labelled|labeled)\b|\bdiagram\b|\bfigure\b", re.IGNORECASE)


def load_tdw(bank: Bank) -> None:
    """TestDriller WAEC files: tdw_{subject}_{year}.json, one paper each."""
    paths = sorted(EXTRACTED.glob("tdw_*.json"))
    if not paths:
        return
    for path in paths:
        m = re.match(r"tdw_(.+)_(\d{4})\.json$", path.name)
        if not m:
            continue
        subject = SUBJECT_NAMES.get(m.group(1), m.group(1).replace("-", " ").title())
        with open(path, encoding="utf-8") as fh:
            items = json.load(fh)
        added = 0
        for item in items:
            if DIAGRAM_RE.search(item.get("prompt") or ""):
                bank.dropped["diagram-dependent"] = bank.dropped.get("diagram-dependent", 0) + 1
                continue
            raw_opts = item.get("options") or []
            options = [{"id": o["id"], "text": strip_prefix(o.get("text") or "")} for o in raw_opts if isinstance(o, dict)]
            ok = bank.add(
                exam="WAEC",
                subject=subject,
                year=item.get("year") or int(m.group(2)),
                prompt=item.get("prompt"),
                options=options,
                correct_option_id=(item.get("correctOptionId") or "").lower(),
                number=item.get("questionNumber") or added + 1,
                explanation=item.get("explanation"),
                source="TestDriller WAEC past questions",
                source_url=item.get("sourceUrl"),
            )
            added += ok
    total = sum(1 for p in paths)
    print(f"  tdw_*: {total} files -> {total} papers processed")


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
    load_tdw(bank)
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
