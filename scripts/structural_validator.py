#!/usr/bin/env python3
"""
Structural Validator for Superprof Translation Quality Review.

Parses per-notification CSVs (Sheet113-style: one notification, all countries,
France first as reference) and runs structural checks comparing each country's
translation against the French original.

Usage:
    python3 scripts/structural_validator.py --input samples/file.csv --output reports/structural_results.json

Stdlib only — no pip installs required.
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns for Superprof template syntax
# ---------------------------------------------------------------------------

# @TPL_VARIABLE@ — value insertion variables
RE_VALUE_VAR = re.compile(r'@TPL_[A-Z0-9_]+@')

# <TPL_IF_VAR>...</TPL_IF_VAR> — conditional IF blocks (opening tag only)
RE_IF_OPEN = re.compile(r'<TPL_IF_[A-Z0-9_]+>')
RE_IF_CLOSE = re.compile(r'</TPL_IF_[A-Z0-9_]+>')

# <TPL_ELSE_VAR>...</TPL_ELSE_VAR> — conditional ELSE blocks
RE_ELSE_OPEN = re.compile(r'<TPL_ELSE_[A-Z0-9_]+>')
RE_ELSE_CLOSE = re.compile(r'</TPL_ELSE_[A-Z0-9_]+>')

# <TPL_LOOP_VAR>...</TPL_LOOP_VAR> — loop/group blocks
RE_LOOP_OPEN = re.compile(r'<TPL_LOOP_[A-Z0-9_]+>')
RE_LOOP_CLOSE = re.compile(r'</TPL_LOOP_[A-Z0-9_]+>')

# Extract the variable name from a loop tag
RE_LOOP_NAME = re.compile(r'<TPL_LOOP_([A-Z0-9_]+)>')

# Extract the variable name from a conditional tag
RE_IF_NAME = re.compile(r'<TPL_IF_([A-Z0-9_]+)>')
RE_ELSE_NAME = re.compile(r'<TPL_ELSE_([A-Z0-9_]+)>')

# Custom markup: [LIEN]...[/LIEN], [TITRE]...[/TITRE], [BOUTON]...[/BOUTON], etc.
RE_CUSTOM_TAGS = re.compile(r'\[(LIEN|TITRE|BOUTON|LOGO_URL|FOND_JAUNE|SIG_EQUIPE)\]')
RE_CUSTOM_CLOSE = re.compile(r'\[/(LIEN|TITRE|BOUTON|LOGO_URL|FOND_JAUNE|SIG_EQUIPE)\]')

# URL_QUI_CONNECTE pattern inside links
RE_URL_CONNECTE = re.compile(r'URL_QUI_CONNECTE')

# HTML tags
RE_HTML_TAGS = re.compile(r'</?(?:b|i|u|mark|li|sup|a|A)\b[^>]*>', re.IGNORECASE)

# Subject-variable variants (for MINUS_SMART / FIRST_MAJUS_SMART rule enforcement)
# Order matters for regex alternation: longer/more specific names first so
# e.g. "MINUS_SMART" matches before "MINUS".
RE_SUBJECT_DE_MATIERE = re.compile(r'@TPL_MATIERE_DE_MATIERE@')
RE_SUBJECT_FIRST_MAJUS_SMART = re.compile(r'@TPL_MATIERE_FIRST_MAJUS_SMART@')
RE_SUBJECT_MINUS_SMART = re.compile(r'@TPL_MATIERE_MINUS_SMART@')
RE_SUBJECT_FIRST_MAJUS = re.compile(r'@TPL_MATIERE_FIRST_MAJUS(?!_SMART)@')
RE_SUBJECT_MINUS = re.compile(r'@TPL_MATIERE_MINUS(?!_SMART)@')
RE_SUBJECT_NOM = re.compile(r'@TPL_MATIERE_NOM@')

def is_emoji_char(char: str) -> bool:
    """Detect emoji using Unicode category data (auto-updates with Python version)."""
    if len(char) != 1:
        return False
    cat = unicodedata.category(char)
    # Symbol, Other covers the vast majority of emoji
    if cat == 'So':
        return True
    # Also catch specific codepoint ranges that unicodedata classifies differently
    cp = ord(char)
    # Regional indicator symbols (flags) — category 'So' on most Python versions
    if 0x1F1E0 <= cp <= 0x1F1FF:
        return True
    # Variation selectors and ZWJ used in emoji sequences
    if cp in (0x200D, 0xFE0F, 0xFE0E):
        return True
    return False


def extract_emoji(text: str) -> list[str]:
    """Extract all emoji characters from text using unicodedata."""
    return [ch for ch in text if is_emoji_char(ch)]

# Mojibake patterns (common UTF-8 misinterpretation sequences)
RE_MOJIBAKE = re.compile(
    r'Ã©|Ã¨|Ã |Ã¢|Ã®|Ã´|Ã»|Ã§|Ã‰|Ãˆ|Ã€|Ã¢|Ã¯|Ã¶|Ã¼|Ã±|'
    r'â€™|â€"|â€œ|â€\x9d|Â |Â«|Â»|â‚¬'
)


# ---------------------------------------------------------------------------
# CSV Parser — Sheet113-style (per-notification, all countries)
# ---------------------------------------------------------------------------

def parse_per_notification_csv(filepath: str) -> list[dict]:
    """
    Parse a per-notification CSV where each cell is a country block:
      - First line of cell: country name
      - Line with "Titre: ..."
      - Line(s) with "corps..." (the email body, can be multiline)

    The CSV may have multiple rows and multiple columns — each cell is one market.
    Returns a list of dicts: {country, titre, corps}
    """
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        cells = [cell for row in reader for cell in row if cell.strip()]

    entries = []
    for cell in cells:
        entry = parse_country_block(cell)
        if entry:
            entries.append(entry)

    return entries


def parse_country_block(block: str) -> dict | None:
    """Parse a single country block into {country, titre, corps}."""
    lines = block.strip().split('\n')
    if not lines:
        return None

    # First line: country name
    country = lines[0].strip().strip('"').strip(',').strip('"').strip()
    if not country:
        return None

    titre = ''
    corps = ''

    for i, line in enumerate(lines[1:], 1):
        stripped = line.strip()
        if stripped.startswith('Titre:'):
            titre = stripped[len('Titre:'):].strip()
        elif stripped.startswith('corps'):
            # Everything from 'corps' onward is the body
            corps_lines = [stripped[len('corps'):]] + lines[i+1:]
            corps = '\n'.join(corps_lines).strip()
            # Clean trailing quote+comma patterns
            corps = re.sub(r'"\s*,?\s*$', '', corps)
            break

    return {
        'country': country,
        'titre': titre,
        'corps': corps,
    }


# ---------------------------------------------------------------------------
# Structural Checks
# ---------------------------------------------------------------------------

def extract_value_variables(text: str) -> list[str]:
    """Extract all @TPL_*@ value variables from text."""
    return RE_VALUE_VAR.findall(text)


def extract_conditional_names(text: str) -> dict:
    """Extract all conditional block names and check they're properly closed."""
    if_opens = RE_IF_NAME.findall(text)
    if_closes = [m.group(1) for m in re.finditer(r'</TPL_IF_([A-Z0-9_]+)>', text)]
    else_opens = RE_ELSE_NAME.findall(text)
    else_closes = [m.group(1) for m in re.finditer(r'</TPL_ELSE_([A-Z0-9_]+)>', text)]
    return {
        'if_names': if_opens,
        'if_closes': if_closes,
        'else_names': else_opens,
        'else_closes': else_closes,
    }


def extract_emojis(text: str) -> list[str]:
    """Extract all emoji from text in order."""
    return extract_emoji(text)


def extract_custom_tags(text: str) -> dict:
    """Extract custom markup tag counts."""
    opens = RE_CUSTOM_TAGS.findall(text)
    closes = RE_CUSTOM_CLOSE.findall(text)
    return {'opens': opens, 'closes': closes}


def load_subject_variable_rules(config_dir: str) -> dict | None:
    """Load ``subject_variable_usage_rules`` from label_patterns.json (or None if missing)."""
    path = Path(config_dir) / 'label_patterns.json'
    if not path.exists():
        return None
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f'WARN: could not load subject variable rules: {exc}', file=sys.stderr)
        return None
    return cfg.get('subject_variable_usage_rules')


def load_block_scope_overrides(config_dir: str) -> dict | None:
    """Load ``block_scope_overrides`` from label_patterns.json (or None if missing)."""
    path = Path(config_dir) / 'label_patterns.json'
    if not path.exists():
        return None
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f'WARN: could not load block scope overrides: {exc}', file=sys.stderr)
        return None
    return cfg.get('block_scope_overrides')


def load_valid_variables(config_dir: str) -> dict[str, str] | None:
    """Load Variables.csv and return {variable_name: description}, or None if file missing."""
    path = Path(config_dir) / 'Variables.csv'
    if not path.exists():
        return None
    valid: dict[str, str] = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if row and row[0].startswith('@TPL_'):
                valid[row[0]] = row[1] if len(row) > 1 else ''
    print(f"Variables.csv: {len(valid)} variables loaded", file=sys.stderr)
    return valid


def check_variables(ref_entry: dict, entry: dict) -> list[dict]:
    """Check that all @TPL_*@ variables from the French reference exist in the translation."""
    issues = []
    ref_text = ref_entry['titre'] + ' ' + ref_entry['corps']
    trans_text = entry['titre'] + ' ' + entry['corps']

    ref_vars = set(extract_value_variables(ref_text))
    trans_vars = set(extract_value_variables(trans_text))

    # Missing variables (in French but not in translation)
    missing = ref_vars - trans_vars
    for var in sorted(missing):
        issues.append({
            'check': 'variable_missing',
            'severity': 'error',
            'category': 'label',
            'message': f'Variable {var} is in the French reference but missing from the translation',
            'variable': var,
        })

    # Extra variables (in translation but not in French)
    extra = trans_vars - ref_vars
    for var in sorted(extra):
        issues.append({
            'check': 'variable_extra',
            'severity': 'warning',
            'category': 'label',
            'message': f'Variable {var} is in the translation but not in the French reference',
            'variable': var,
        })

    return issues


def check_variables_catalogue(entry: dict, valid_variables: dict[str, str]) -> list[dict]:
    """Flag @TPL_*@ variables in the translation that don't exist in Variables.csv."""
    issues = []
    text = entry['titre'] + ' ' + entry['corps']
    trans_vars = set(extract_value_variables(text))
    for var in sorted(trans_vars):
        if var not in valid_variables:
            issues.append({
                'check': 'variable_undefined',
                'severity': 'warning',
                'category': 'label',
                'message': f'Variable {var} not found in Variables.csv — may be a typo or deprecated variable',
                'variable': var,
            })
    return issues


def check_conditionals(ref_entry: dict, entry: dict) -> list[dict]:
    """Check conditional blocks (TPL_IF/TPL_ELSE) are properly formed and match reference."""
    issues = []
    ref_text = ref_entry['titre'] + ' ' + ref_entry['corps']
    trans_text = entry['titre'] + ' ' + entry['corps']

    ref_conds = extract_conditional_names(ref_text)
    trans_conds = extract_conditional_names(trans_text)

    # Check IF blocks match reference
    ref_if_set = set(ref_conds['if_names'])
    trans_if_set = set(trans_conds['if_names'])

    missing_ifs = ref_if_set - trans_if_set
    for name in sorted(missing_ifs):
        issues.append({
            'check': 'conditional_missing',
            'severity': 'error',
            'category': 'label',
            'message': f'Conditional block <TPL_IF_{name}> is in French but missing from translation',
            'variable': f'TPL_IF_{name}',
        })

    extra_ifs = trans_if_set - ref_if_set
    for name in sorted(extra_ifs):
        issues.append({
            'check': 'conditional_extra',
            'severity': 'warning',
            'category': 'label',
            'message': f'Conditional block <TPL_IF_{name}> is in translation but not in French reference',
            'variable': f'TPL_IF_{name}',
        })

    # Check for unclosed conditionals in translation
    trans_if_opens = trans_conds['if_names']
    trans_if_closes = trans_conds['if_closes']
    if sorted(trans_if_opens) != sorted(trans_if_closes):
        unclosed = set(trans_if_opens) - set(trans_if_closes)
        for name in sorted(unclosed):
            issues.append({
                'check': 'conditional_unclosed',
                'severity': 'error',
                'category': 'label',
                'message': f'Conditional <TPL_IF_{name}> opened but never closed in translation',
                'variable': f'TPL_IF_{name}',
            })

    # Check ELSE blocks
    ref_else_set = set(ref_conds['else_names'])
    trans_else_set = set(trans_conds['else_names'])

    missing_elses = ref_else_set - trans_else_set
    for name in sorted(missing_elses):
        issues.append({
            'check': 'conditional_else_missing',
            'severity': 'error',
            'category': 'label',
            'message': f'Else block <TPL_ELSE_{name}> is in French but missing from translation',
            'variable': f'TPL_ELSE_{name}',
        })

    return issues


def check_emojis(ref_entry: dict, entry: dict) -> list[dict]:
    """Check emoji consistency between French reference and translation."""
    issues = []
    ref_text = ref_entry['titre'] + ' ' + ref_entry['corps']
    trans_text = entry['titre'] + ' ' + entry['corps']

    ref_emojis = extract_emojis(ref_text)
    trans_emojis = extract_emojis(trans_text)

    if ref_emojis != trans_emojis:
        ref_set = set(ref_emojis)
        trans_set = set(trans_emojis)

        missing = ref_set - trans_set
        extra = trans_set - ref_set

        if missing:
            issues.append({
                'check': 'emoji_missing',
                'severity': 'warning',
                'category': 'emoji',
                'message': f'Emoji from French reference missing in translation: {" ".join(missing)}',
                'detail': {'missing': list(missing)},
            })

        if extra:
            issues.append({
                'check': 'emoji_extra',
                'severity': 'warning',
                'category': 'emoji',
                'message': f'Extra emoji in translation not in French reference: {" ".join(extra)}',
                'detail': {'extra': list(extra)},
            })

        if not missing and not extra and ref_emojis != trans_emojis:
            issues.append({
                'check': 'emoji_order',
                'severity': 'info',
                'category': 'emoji',
                'message': 'Emoji are present but in a different order than the French reference',
                'detail': {'ref_order': ref_emojis, 'trans_order': trans_emojis},
            })

    return issues


def check_custom_markup(ref_entry: dict, entry: dict) -> list[dict]:
    """Check custom markup tags ([LIEN], [TITRE], [BOUTON], etc.) match reference."""
    issues = []
    ref_text = ref_entry['titre'] + ' ' + ref_entry['corps']
    trans_text = entry['titre'] + ' ' + entry['corps']

    ref_tags = extract_custom_tags(ref_text)
    trans_tags = extract_custom_tags(trans_text)

    # Compare open tag counts
    from collections import Counter
    ref_open_counts = Counter(ref_tags['opens'])
    trans_open_counts = Counter(trans_tags['opens'])

    for tag, count in ref_open_counts.items():
        trans_count = trans_open_counts.get(tag, 0)
        if trans_count < count:
            issues.append({
                'check': 'markup_missing',
                'severity': 'warning',
                'category': 'format',
                'message': f'Custom tag [{tag}] appears {count}x in French but {trans_count}x in translation',
                'detail': {'tag': tag, 'ref_count': count, 'trans_count': trans_count},
            })

    # Check for unclosed custom tags in translation
    trans_open_counts_all = Counter(trans_tags['opens'])
    trans_close_counts = Counter(trans_tags['closes'])
    for tag, count in trans_open_counts_all.items():
        close_count = trans_close_counts.get(tag, 0)
        if count != close_count:
            issues.append({
                'check': 'markup_unclosed',
                'severity': 'warning',
                'category': 'format',
                'message': f'Custom tag [{tag}] has {count} opens but {close_count} closes in translation',
                'detail': {'tag': tag, 'opens': count, 'closes': close_count},
            })

    return issues


def check_encoding(entry: dict) -> list[dict]:
    """Check for encoding issues (mojibake, control characters)."""
    issues = []
    text = entry['titre'] + ' ' + entry['corps']

    mojibake = RE_MOJIBAKE.findall(text)
    if mojibake:
        issues.append({
            'check': 'encoding_mojibake',
            'severity': 'error',
            'category': 'encoding',
            'message': f'Possible mojibake detected: {", ".join(set(mojibake[:5]))}',
            'detail': {'patterns': list(set(mojibake))},
        })

    # Control characters (except newline, tab)
    for ch in text:
        if unicodedata.category(ch) == 'Cc' and ch not in '\n\r\t':
            issues.append({
                'check': 'encoding_control_char',
                'severity': 'warning',
                'category': 'encoding',
                'message': f'Control character found: U+{ord(ch):04X}',
            })
            break  # Report once

    return issues


def check_empty_placeholder(ref_entry: dict, entry: dict) -> list[dict]:
    """Check for empty translations, copy-paste of French, or placeholder text."""
    issues = []
    ref_corps = ref_entry['corps'].strip()
    trans_corps = entry['corps'].strip()
    trans_titre = entry['titre'].strip()

    # Empty body
    if not trans_corps and ref_corps:
        issues.append({
            'check': 'empty_body',
            'severity': 'error',
            'category': 'empty',
            'message': 'Translation body is empty but French reference has content',
        })

    # Empty title (when French has one)
    ref_titre = ref_entry['titre'].strip()
    if not trans_titre and ref_titre:
        issues.append({
            'check': 'empty_title',
            'severity': 'error',
            'category': 'empty',
            'message': 'Translation title is empty but French reference has content',
        })

    # Identical to French (untranslated copy-paste) — only flag for non-French countries
    if trans_corps and trans_corps == ref_corps:
        issues.append({
            'check': 'untranslated_body',
            'severity': 'error',
            'category': 'empty',
            'message': 'Translation body is identical to French — likely untranslated copy-paste',
        })

    if trans_titre and trans_titre == ref_titre and ref_titre:
        # Title might legitimately be the same (e.g., brand names), so warning not error
        issues.append({
            'check': 'untranslated_title',
            'severity': 'warning',
            'category': 'empty',
            'message': 'Translation title is identical to French — may be untranslated',
        })

    # Placeholder patterns
    placeholder_patterns = ['TODO', 'TRANSLATE', 'XXX', 'FIXME', 'lorem ipsum', 'TBD']
    combined = trans_corps + ' ' + trans_titre
    for pattern in placeholder_patterns:
        if pattern in combined:
            issues.append({
                'check': 'placeholder_text',
                'severity': 'error',
                'category': 'empty',
                'message': f'Placeholder text detected: "{pattern}"',
            })

    return issues


def check_length_anomaly(ref_entry: dict, entry: dict, lang_ratios: dict = None) -> list[dict]:
    """Check for suspicious length differences between reference and translation."""
    issues = []
    ref_corps = ref_entry['corps']
    trans_corps = entry['corps']

    if not ref_corps or not trans_corps:
        return issues

    # Strip template variables and HTML for a fairer length comparison
    def strip_markup(text):
        text = RE_VALUE_VAR.sub('', text)
        text = RE_IF_OPEN.sub('', text)
        text = RE_IF_CLOSE.sub('', text)
        text = RE_ELSE_OPEN.sub('', text)
        text = RE_ELSE_CLOSE.sub('', text)
        text = RE_HTML_TAGS.sub('', text)
        text = RE_CUSTOM_TAGS.sub('', text)
        text = RE_CUSTOM_CLOSE.sub('', text)
        text = re.sub(r'URL_QUI_CONNECTE\|', '', text)
        return text.strip()

    ref_clean = strip_markup(ref_corps)
    trans_clean = strip_markup(trans_corps)

    if len(ref_clean) == 0:
        return issues

    ratio = len(trans_clean) / len(ref_clean)

    # Very short (less than 40% of reference)
    if ratio < 0.4:
        issues.append({
            'check': 'length_too_short',
            'severity': 'warning',
            'category': 'format',
            'message': f'Translation is unusually short ({ratio:.0%} of French reference length)',
            'detail': {'ratio': round(ratio, 2), 'ref_len': len(ref_clean), 'trans_len': len(trans_clean)},
        })

    # Very long (more than 250% of reference)
    if ratio > 2.5:
        issues.append({
            'check': 'length_too_long',
            'severity': 'warning',
            'category': 'format',
            'message': f'Translation is unusually long ({ratio:.0%} of French reference length)',
            'detail': {'ratio': round(ratio, 2), 'ref_len': len(ref_clean), 'trans_len': len(trans_clean)},
        })

    return issues


# ---------------------------------------------------------------------------
# Country → language code mapping (for subject-variable variant checks)
#
# CSV country cells are written in French. The mapping below returns the
# primary Superprof market language per country. Countries that have more
# than one plausible Superprof locale (Suisse, Luxembourg, Canada, etc.) map
# to None so the deterministic DE_MATIERE check stays conservative and
# defers ambiguous cases to the AI reviewer.
# ---------------------------------------------------------------------------

COUNTRY_TO_LANG: dict[str, str | None] = {
    # French — reference market
    'France': 'fr',
    'Wallonie': 'fr',
    'Sénégal': 'fr',
    'Cameroun': 'fr',
    # English-primary markets
    'Royaume-Uni': 'en',
    'États-Unis': 'en',
    'Australie': 'en',
    'Nouvelle-Zélande': 'en',
    'Irlande': 'en',
    'Nigéria': 'en',
    'Ghana': 'en',
    'Kenya': 'en',
    'Ouganda': 'en',
    'Tanzanie': 'en',
    'Pakistan': 'en',
    'Philippines': 'en',
    'Singapour': 'en',
    'Mauritius': 'en',
    'Jamaïque': 'en',
    'Malte': 'en',
    'Botswana': 'en',
    'Namibie': 'en',
    'Lesotho': 'en',
    'Belize': 'en',
    'Rwanda': 'en',
    'Brunei': 'en',
    # Spanish-primary markets
    'Espagne': 'es',
    'Mexique': 'es',
    'Argentine': 'es',
    'Chili': 'es',
    'Colombie': 'es',
    'Pérou': 'es',
    'Uruguay': 'es',
    'Paraguay': 'es',
    'Bolivie': 'es',
    'Équateur': 'es',
    'Panama': 'es',
    'Costa Rica': 'es',
    'Guatemala': 'es',
    'Honduras': 'es',
    'El Salvador': 'es',
    'Nicaragua': 'es',
    'République Dominicaine': 'es',
    'Puerto Rico': 'es',
    # Portuguese
    'Portugal': 'pt',
    'Brésil': 'pt',
    # Italian
    'Italie': 'it',
    # German-primary markets
    'Allemagne': 'de',
    'Autriche': 'de',
    # Dutch
    'Pays-Bas': 'nl',
    'Flandre': 'nl',
    # Nordic / Scandinavian
    'Suède': 'sv',
    'Norvège': 'no',
    'Danemark': 'da',
    'Finlande': 'fi',
    'Islande': 'is',
    # Slavic / Eastern European (declension — DE_MATIERE valid)
    'Pologne': 'pl',
    'Tchéquie': 'cs',
    'Slovaquie': 'sk',
    'Hongrie': 'hu',
    'Roumanie': 'ro',
    'Moldavie': 'ro',
    'Bulgarie': 'bg',
    'Croatie': 'hr',
    'Serbie': 'sr',
    'Slovénie': 'sl',
    'Russie': 'ru',
    'Ukraine': 'uk',
    'Kazakhstan': 'ru',
    'Lettonie': 'lv',
    'Lituanie': 'lt',
    'Estonie': 'et',
    # Greek
    'Grèce': 'el',
    'Chypre': 'el',
    # Turkish
    'Turquie': 'tr',
    # CJK
    'Japon': 'ja',
    'Corée du Sud': 'ko',
    'Taïwan': 'zh-TW',
    'Hong-Kong': 'zh-TW',
    # Southeast Asia
    'Thailand': 'th',
    'Vietnam': 'vi',
    'Indonésie': 'id',
    # Middle East / Arabic-primary
    'Bahreïn': 'ar',
    'Qatar': 'ar',
    'Oman': 'ar',
    'Émirats Arabes Unis': 'ar',
    # Hebrew
    'Israël': 'he',
    # Ambiguous / multi-lingual Superprof markets — defer to AI reviewer
    'Canada': None,
    'Suisse': None,
    'Schweiz': None,
    'Luxembourg': None,
    'Maroc': None,
    'Tunisie': None,
    'Afrique du Sud': None,
    'Inde': None,
    'Malaisie': None,
    'Bosnie-Herzégovine': None,
    'Monténégro': None,
    # Countries not (yet) covered by subject_variable_usage_rules
    'Albanie': None,
    'Cape Vert': None,
    'Timor oriental': None,
    'Mozambique': None,
}


# Trailing tags appended to country names in some CSV exports
RE_COUNTRY_TAG = re.compile(r'\[(?:Groupement|Référence)\]\s*$')


def normalize_country_name(country: str) -> str:
    """
    Strip [Groupement]/[Référence] suffixes and collapse doubled names
    (e.g. 'Afrique du Sud Afrique du Sud' -> 'Afrique du Sud').
    """
    name = (country or '').strip()
    # Strip repeating "[Tag]" suffixes
    while True:
        stripped = RE_COUNTRY_TAG.sub('', name).strip()
        if stripped == name:
            break
        name = stripped
    # Collapse a name that is literally repeated (separated by a space)
    if name:
        half = len(name) // 2
        if len(name) % 2 == 1 and name[half] == ' ' and name[:half] == name[half + 1:]:
            name = name[:half]
    return name


def get_language_code(country: str) -> str | None:
    """
    Return the primary Superprof market language for a country, or None
    for ambiguous / unknown countries. Lookup is done on the normalized
    country name.
    """
    return COUNTRY_TO_LANG.get(normalize_country_name(country))


# ---------------------------------------------------------------------------
# Subject-variable variant check (_SMART vs non-smart, DE_MATIERE validity,
# title/body consistency).
# ---------------------------------------------------------------------------

def _detect_subject_variable(text: str) -> str | None:
    """Return the subject variable variant name found in ``text`` (or None)."""
    if RE_SUBJECT_DE_MATIERE.search(text):
        return 'TPL_MATIERE_DE_MATIERE'
    if RE_SUBJECT_FIRST_MAJUS_SMART.search(text):
        return 'TPL_MATIERE_FIRST_MAJUS_SMART'
    if RE_SUBJECT_MINUS_SMART.search(text):
        return 'TPL_MATIERE_MINUS_SMART'
    if RE_SUBJECT_FIRST_MAJUS.search(text):
        return 'TPL_MATIERE_FIRST_MAJUS'
    if RE_SUBJECT_MINUS.search(text):
        return 'TPL_MATIERE_MINUS'
    if RE_SUBJECT_NOM.search(text):
        return 'TPL_MATIERE_NOM'
    return None


def check_subject_variable_variant(
    ref_entry: dict,
    entry: dict,
    subject_rules: dict | None,
) -> list[dict]:
    """
    Deterministic subject-variable checks aligned with
    config/label_patterns.json > subject_variable_usage_rules.

    Emits:
      - subject_variable_non_smart (warning) for @TPL_MATIERE_MINUS@,
        @TPL_MATIERE_FIRST_MAJUS@, @TPL_MATIERE_NOM@.
      - subject_variable_mismatch (error) when title and body use different
        subject variables.
      - subject_variable_de_matiere_wrong_language (error) when
        @TPL_MATIERE_DE_MATIERE@ appears in a language listed in
        subject_variable_usage_rules.TPL_MATIERE_DE_MATIERE.do_not_use_for.
    """
    issues: list[dict] = []
    titre = entry.get('titre', '') or ''
    corps = entry.get('corps', '') or ''
    combined = f'{titre}\n{corps}'

    # 1. Non-smart variant warnings — universal (no language required).
    non_smart_hits: list[str] = []
    if RE_SUBJECT_MINUS.search(combined):
        non_smart_hits.append('@TPL_MATIERE_MINUS@')
    if RE_SUBJECT_FIRST_MAJUS.search(combined):
        non_smart_hits.append('@TPL_MATIERE_FIRST_MAJUS@')
    if RE_SUBJECT_NOM.search(combined):
        non_smart_hits.append('@TPL_MATIERE_NOM@')
    for var in non_smart_hits:
        issues.append({
            'check': 'subject_variable_non_smart',
            'severity': 'warning',
            'category': 'label',
            'message': (
                f'{var} used — prefer the _SMART variant '
                '(@TPL_MATIERE_MINUS_SMART@ or @TPL_MATIERE_FIRST_MAJUS_SMART@) '
                'so acronyms like ESOL stay uppercase.'
            ),
            'variable': var.strip('@'),
        })

    # 2. Title/body consistency — error on mismatch within the same cell.
    title_var = _detect_subject_variable(titre)
    body_var = _detect_subject_variable(corps)
    if title_var and body_var and title_var != body_var:
        issues.append({
            'check': 'subject_variable_mismatch',
            'severity': 'error',
            'category': 'label',
            'message': (
                f'Title uses @{title_var}@ but body uses @{body_var}@ — '
                'title and body must use the same subject variable.'
            ),
            'detail': {'title_var': title_var, 'body_var': body_var},
        })

    # 3. Variant used in a do_not_use_for language — error only when the
    #    country resolves to an unambiguous language code.
    if subject_rules:
        lang = get_language_code(entry.get('country', ''))
        if lang:
            if RE_SUBJECT_DE_MATIERE.search(combined):
                de_rule = subject_rules.get('TPL_MATIERE_DE_MATIERE', {})
                if lang in set(de_rule.get('do_not_use_for', [])):
                    issues.append({
                        'check': 'subject_variable_de_matiere_wrong_language',
                        'severity': 'error',
                        'category': 'label',
                        'message': (
                            f'@TPL_MATIERE_DE_MATIERE@ is not valid for {lang} — '
                            f'use @TPL_MATIERE_FIRST_MAJUS_SMART@ or '
                            f'@TPL_MATIERE_MINUS_SMART@ instead.'
                        ),
                        'variable': 'TPL_MATIERE_DE_MATIERE',
                        'detail': {'language': lang},
                    })
            if RE_SUBJECT_FIRST_MAJUS_SMART.search(combined):
                fms_rule = subject_rules.get('TPL_MATIERE_FIRST_MAJUS_SMART', {})
                if lang in set(fms_rule.get('do_not_use_for', [])):
                    issues.append({
                        'check': 'subject_variable_first_majus_smart_wrong_language',
                        'severity': 'error',
                        'category': 'label',
                        'message': (
                            f'@TPL_MATIERE_FIRST_MAJUS_SMART@ is not valid for '
                            f'{lang} — subject names are written lowercase '
                            f'mid-sentence. Use @TPL_MATIERE_MINUS_SMART@ instead.'
                        ),
                        'variable': 'TPL_MATIERE_FIRST_MAJUS_SMART',
                        'detail': {'language': lang},
                    })

    return issues


def check_html_balance(entry: dict) -> list[dict]:
    """Check that HTML tags are properly balanced in the translation."""
    issues = []
    text = entry['corps']

    # Check <b>...</b>, <mark>...</mark>, <i>...</i>, <u>...</u>
    for tag in ['b', 'mark', 'i', 'u']:
        opens = len(re.findall(f'<{tag}>', text, re.IGNORECASE))
        closes = len(re.findall(f'</{tag}>', text, re.IGNORECASE))
        if opens != closes:
            issues.append({
                'check': 'html_unbalanced',
                'severity': 'warning',
                'category': 'format',
                'message': f'Unbalanced HTML: {opens}x <{tag}> but {closes}x </{tag}>',
                'detail': {'tag': tag, 'opens': opens, 'closes': closes},
            })

    return issues


# ---------------------------------------------------------------------------
# Main Validation Pipeline
# ---------------------------------------------------------------------------

def validate_entry(
    ref_entry: dict,
    entry: dict,
    valid_variables: dict[str, str] | None = None,
    subject_rules: dict | None = None,
) -> list[dict]:
    """Run all structural checks on a single country entry against the French reference."""
    all_issues = []

    all_issues.extend(check_variables(ref_entry, entry))
    all_issues.extend(check_variables_catalogue(entry, valid_variables or {}))
    all_issues.extend(check_conditionals(ref_entry, entry))
    all_issues.extend(check_emojis(ref_entry, entry))
    all_issues.extend(check_custom_markup(ref_entry, entry))
    all_issues.extend(check_encoding(entry))
    all_issues.extend(check_empty_placeholder(ref_entry, entry))
    all_issues.extend(check_length_anomaly(ref_entry, entry))
    all_issues.extend(check_html_balance(entry))
    all_issues.extend(check_subject_variable_variant(ref_entry, entry, subject_rules))

    # Tag each issue with the country
    for issue in all_issues:
        issue['country'] = entry['country']

    return all_issues


def run_validation(filepath: str, config_dir: str = 'config') -> dict:
    """Parse the CSV and run all structural checks."""
    valid_variables = load_valid_variables(config_dir)
    if valid_variables is None:
        print("ABORT: Variables.csv not found in config/. Cannot validate variables.", file=sys.stderr)
        sys.exit(1)
    subject_rules = load_subject_variable_rules(config_dir)
    entries = parse_per_notification_csv(filepath)

    if not entries:
        return {
            'error': 'No country entries found in the CSV file',
            'summary': {'total': 0, 'errors': 0, 'warnings': 0, 'info': 0},
            'issues': [],
            'metadata': {'file': filepath, 'countries': [], 'reference': None},
        }

    # Find France reference row by content (country name or language code), not position
    ref_entry = None
    for entry in entries:
        country_val = entry.get('country', '').strip().lower()
        if country_val == 'france' or country_val == 'fr':
            ref_entry = entry
            break

    if ref_entry is None:
        print(
            "ERROR: No France/fr reference row found in CSV. "
            "The structural validator requires a French reference row to compare against.",
            file=sys.stderr,
        )
        sys.exit(1)

    other_entries = [e for e in entries if e is not ref_entry]

    all_issues = []
    countries_reviewed = []

    for entry in other_entries:
        country = entry['country']
        countries_reviewed.append(country)
        issues = validate_entry(ref_entry, entry, valid_variables, subject_rules)
        all_issues.extend(issues)

    # Summary
    error_count = sum(1 for i in all_issues if i['severity'] == 'error')
    warning_count = sum(1 for i in all_issues if i['severity'] == 'warning')
    info_count = sum(1 for i in all_issues if i['severity'] == 'info')

    # Group by country for summary
    by_country = defaultdict(lambda: {'errors': 0, 'warnings': 0, 'infos': 0})
    for issue in all_issues:
        severity_key = issue['severity'] + 's' if issue['severity'] != 'info' else 'infos'
        by_country[issue['country']][severity_key] += 1

    return {
        'summary': {
            'total': len(all_issues),
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'countries_reviewed': len(countries_reviewed),
            'by_country': dict(by_country),
        },
        'issues': all_issues,
        'metadata': {
            'file': str(filepath),
            'reference_country': ref_entry['country'],
            'countries': countries_reviewed,
            'reference_titre': ref_entry['titre'],
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Structural validation for Superprof translation CSVs'
    )
    parser.add_argument('--input', '-i', required=True, help='Path to CSV file')
    parser.add_argument('--output', '-o', help='Path for JSON output (default: stdout)')
    parser.add_argument('--config-dir', default='config', help='Path to config directory containing Variables.csv (default: config)')
    parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON output')
    parser.add_argument('--summary', action='store_true',
        help='Print compact market/count table to stdout instead of full JSON')

    args = parser.parse_args()

    filepath = Path(args.input)
    if not filepath.exists():
        print(f'Error: File not found: {filepath}', file=sys.stderr)
        sys.exit(1)

    results = run_validation(str(filepath), config_dir=args.config_dir)

    json_output = json.dumps(results, ensure_ascii=False, indent=2 if args.pretty else None)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding='utf-8')
        # Print summary to stderr (existing behavior, unchanged)
        s = results['summary']
        print(
            f"Structural validation complete: {s['errors']} errors, "
            f"{s['warnings']} warnings, {s['info']} info — "
            f"{s['countries_reviewed']} countries reviewed",
            file=sys.stderr
        )

    if args.summary:
        # Compact table to stdout — replaces full JSON when used without --output
        by_country = results['summary'].get('by_country', {})
        header = f"{'Market':<30} {'Errors':>6} {'Warnings':>8} {'Info':>5}"
        print(header)
        print('-' * len(header))
        for country, counts in sorted(by_country.items()):
            print(f"{country:<30} {counts.get('errors', 0):>6} {counts.get('warnings', 0):>8} {counts.get('infos', 0):>5}")
        s = results['summary']
        print('-' * len(header))
        print(f"{'TOTAL':<30} {s['errors']:>6} {s['warnings']:>8} {s['info']:>5}")
    elif not args.output:
        # Default: full JSON to stdout (unchanged behavior)
        print(json_output)


if __name__ == '__main__':
    main()
