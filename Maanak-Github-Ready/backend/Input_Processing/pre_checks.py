import re
import unicodedata
from typing import Dict, Any, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Layer 0.3: PII Scrubber
# ─────────────────────────────────────────────────────────────────────────────
PII_PATTERNS = [
    # Indian Mobile: 10 digits starting with 6-9, optionally prefixed by +91.
    # Must NOT be preceded by letter/digit (serial number contexts like SN9876543210)
    # Must NOT be preceded by "No" (batch/serial label like "Batch No 9812340001")
    # Handles spaced format like "98765 43210" with optional single middle space
    (re.compile(
        r'(?<![A-Za-z\d])'                      # Not preceded by letter or digit
        r'(?<!No\s)'                             # Not preceded by "No " (batch/serial labels)
        r'(?:\+?91[\s\-]?)?'                     # Optional +91 prefix
        r'[6-9]\d{4}'                            # First 5 digits
        r'[\s]?'                                 # Optional single space (spaced format)
        r'\d{5}'                                 # Last 5 digits
        r'(?!\d)',                               # Not followed by digit
    ), '[REDACTED_PHONE]'),

    # 12-digit Aadhaar: bare unspaced form AND formatted form XXXX-XXXX-XXXX or XXXX XXXX XXXX
    (re.compile(r'(?<![A-Za-z\d])\d{12}(?!\d)'), '[REDACTED_AADHAAR]'),
    (re.compile(r'(?<![A-Za-z\d])\d{4}[\s\-]\d{4}[\s\-]\d{4}(?!\d)'), '[REDACTED_AADHAAR]'),

    # Standard Email
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED_EMAIL]'),
]

# ─────────────────────────────────────────────────────────────────────────────
# Layer 0.4: IS Code Regex
# KEY DESIGN DECISIONS:
# 1. `(?<![a-zA-Z])(?:IS)(?=[/\s:.\-\d])` — IS must be preceded by a non-letter
#    AND followed by a separator or digit. This prevents "this is 500" from matching
#    because "is" in that context is surrounded by letters/spaces with no IS-style separator.
# 2. IS/IEC and IS/ISO listed BEFORE bare IS (longest-match first within alternation).
# 3. Part/Sec regex handles: " Part 2", "-2", "(Part 2/Sec 3)", "Part 2 Section 3"
# ─────────────────────────────────────────────────────────────────────────────
IS_CODE_REGEX = re.compile(
    r'(?<![a-zA-Z])'                                    # Not preceded by a letter
    r'(?:IS/IEC|IS/ISO|IS)'                             # Uppercase IS prefix ONLY — no IGNORECASE flag
    r'(?=[/\s:.\-\d])'                                  # Must be followed by separator or digit
    r'[\s:.\-/]*'                                       # Flexible separator
    r'(\d{3,5})'                                        # Base standard number — 3 to 5 digits
    r'(?:[\s:.\-]*(\d{4}))?'                            # Optional year — 4 digits
    r'(?:'                                              # Optional Part block
        r'[\s(\-/]*'
        r'(?:(?i:Part)\s*|(?i:P)\.\s*)?'               # "Part" keyword — inline case-insensitive
        r'(\d{1,4})'                                    # Part number
        r'\)?'
        r'(?:'                                          # Optional Section block
            r'[\s(/\-]*'
            r'(?:(?i:Sec)(?i:tion)?\s*)?'              # "Sec/Section" keyword — inline case-insensitive
            r'(\d{1,4})'                                # Section number
            r'\)?'
        r')?'
    r')?'
    # NO re.IGNORECASE — IS must be uppercase to prevent "the price is 500" from matching
)


def _disambiguate_year_part(base: str, year_grp: str, part_grp: str, sec_grp: str):
    """
    Heuristic to separate year captures from part number captures.
    Returns (year, part, sec) as strings or None.
    """
    year = year_grp.strip() if year_grp and year_grp.strip() else None
    part = part_grp.strip() if part_grp and part_grp.strip() else None
    sec = sec_grp.strip() if sec_grp and sec_grp.strip() else None

    if year:
        if 1950 <= int(year) <= 2030:
            pass  # Genuine year
        else:
            # Looks like a part number, not a year
            if not part:
                part = year
            year = None

    return year, part, sec


# ─────────────────────────────────────────────────────────────────────────────
# Product Aliases (multi-word checked first for priority)
# Includes Hindi/Telugu script variants for common BIS products
# ─────────────────────────────────────────────────────────────────────────────
PRODUCT_ALIASES = {
    # Multi-word — always check these first
    "electric iron": ("302", "2", "3"),
    "immersion rod": ("302", "2", "202"),
    "immersion heater": ("302", "2", "202"),
    "water heater": ("2082", None, None),
    "led bulb": ("16102", "1", None),
    "led lamp": ("16102", "1", None),
    "pvc cable": ("694", None, None),
    "packaged water": ("14543", None, None),
    "mineral water": ("13428", None, None),
    # Single-word
    "plug": ("1293", None, None),
    "socket": ("1293", None, None),
    "geyser": ("2082", None, None),
    "iron": ("302", "2", "3"),
    "led": ("16102", "1", None),
    "bulb": ("16102", "1", None),
    "cable": ("694", None, None),
    "wire": ("694", None, None),
    "switch": ("3854", None, None),
    # Transliterated variants (Romanized Indian languages)
    "gizer": ("2082", None, None),
    "gezer": ("2082", None, None),
    "bijli": ("302", None, None),
    # Hindi/Devanagari script variants (normalized text will contain these)
    "गीजर": ("2082", None, None),      # geyser in Hindi
    "एलईडी": ("16102", "1", None),    # LED in Hindi
    "प्लग": ("1293", None, None),      # plug in Hindi
    "केबल": ("694", None, None),       # cable in Hindi
    "बल्ब": ("16102", "1", None),      # bulb in Hindi
    # Telugu script variants
    "గీజర్": ("2082", None, None),     # geyser in Telugu
    "బల్బ్": ("16102", "1", None),    # bulb in Telugu
}

# ─────────────────────────────────────────────────────────────────────────────
# Indexed Standards in Pinecone (EXACT_ALLOWLIST)
# ─────────────────────────────────────────────────────────────────────────────
EXACT_ALLOWLIST = {
    ("10500", None, None), ("1293", None, None), ("13428", None, None),
    ("14543", None, None), ("2112", None, None), ("3854", None, None),
    ("694", None, None), ("15820", None, None), ("16102", "1", None),
    ("16102", "2", None), ("16280", None, None), ("16333", "3", None),
    ("2082", None, None), ("9968", "1", None), ("9968", "2", None),
    ("302", "2", "2"), ("302", "2", "4"), ("302", "2", "6"),
    ("302", "2", "7"), ("302", "2", "9"), ("302", "2", "11"),
    ("302", "2", "12"), ("302", "2", "14"), ("302", "2", "15"),
    ("302", "2", "23"), ("302", "2", "24"), ("302", "2", "25"),
    ("302", "2", "26"), ("302", "2", "31"), ("302", "2", "35"),
    ("302", "2", "45"), ("302", "2", "46"), ("302", "2", "76"),
    ("302", "2", "202"), ("302", "2", "204"), ("302", "2", "208")
}

BASE_ALLOWLIST = {t[0] for t in EXACT_ALLOWLIST}


def normalize_input(text: str) -> str:
    """Layer 0.1: Normalization — NFKC, strip Unicode Cf/Cc chars, convert Indic digits to ASCII."""
    if not text:
        return ""
    # NFKC handles fullwidth chars, ligatures (ﬁ→fi), composed forms
    text = unicodedata.normalize("NFKC", text)
    # Strip format chars (Cf: ZWS, ZWJ, soft-hyphen, RTL mark) and control chars (Cc)
    text = "".join(c for c in text if unicodedata.category(c) not in ["Cf", "Cc"])
    # Convert any Unicode decimal digit to ASCII (handles Telugu, Devanagari, Bengali, etc.)
    result = []
    for c in text:
        if unicodedata.category(c) == "Nd":
            result.append(str(unicodedata.digit(c)))
        else:
            result.append(c)
    return "".join(result).strip()


def scrub_pii(text: str) -> str:
    """Layer 0.3: Non-Terminal PII Scrubber"""
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def validate_code(base: str, part: str = None, sec: str = None) -> str:
    """3-Step Allowlist Validation"""
    if (base, part, sec) in EXACT_ALLOWLIST:
        return "EXACT_MATCH"
    elif base in BASE_ALLOWLIST:
        return "NEEDS_CLARIFICATION"
    else:
        return "OUT_OF_SCOPE"


def execute_layer_0(raw_text: str) -> Dict[str, Any]:
    """Executes all Layer 0 deterministic checks and returns annotated payload."""
    # 1. Normalize (Indic digits, NFKC, strip format chars)
    norm_text = normalize_input(raw_text)

    # 2. Length Check — 2500 allows audit report pastes
    if len(norm_text) > 2500:
        norm_text = norm_text[:2500] + " [TRUNCATED]"

    # 3. PII Scrub
    clean_text = scrub_pii(norm_text)

    # 4. Extract IS Codes using deterministic regex
    matches = IS_CODE_REGEX.findall(clean_text)
    extracted_codes = []
    out_of_scope_codes = []
    needs_clarification_codes = []
    seen_keys = set()

    for match in matches:
        base, year_grp, part_grp, sec_grp = match
        year, part, sec = _disambiguate_year_part(base, year_grp, part_grp, sec_grp)

        # Deduplicate
        key = (base, part, sec)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        status = validate_code(base, part, sec)
        code_obj = {"base": base, "part": part, "sec": sec, "year": year}

        if status == "EXACT_MATCH":
            extracted_codes.append(code_obj)
        elif status == "NEEDS_CLARIFICATION":
            needs_clarification_codes.append(code_obj)
        else:
            out_of_scope_codes.append(code_obj)

    # 5. Product Alias Fallback — only if zero IS codes found
    if not extracted_codes and not needs_clarification_codes and not out_of_scope_codes:
        # Check both normalized (for Indic script) and lowercased text
        text_lower = clean_text.lower()
        # Also check original normalized text for script aliases
        norm_lower = norm_text.lower()
        for alias, (b, p, s) in PRODUCT_ALIASES.items():
            if alias in text_lower or alias in norm_lower:
                extracted_codes.append({"base": b, "part": p, "sec": s, "year": None})
                break

    return {
        "processed_text": clean_text,
        "extracted_codes": extracted_codes,
        "needs_clarification_codes": needs_clarification_codes,
        "out_of_scope_codes": out_of_scope_codes
    }
