"""Build the Markdown report for avis_eleve_prof review."""
import json
from datetime import date
from collections import defaultdict

m = json.load(open('reports/_merged.json'))
all_countries = m['all_countries']
by_country = m['by_country']

# Load France reference cell from CSV (France is the reference, not in merged dict)
import csv
with open('samples/avis_eleve_prof.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        for cell in row:
            first = cell.split('\n', 1)[0].strip() if cell.strip() else ''
            if first == 'France':
                by_country['France'] = {'cell': cell, 'structural': [], 'ai': []}
                break
        if 'France' in by_country:
            break

# Parse cell into title + body
def split_cell(cell):
    """Split a market cell into (country, title, body)."""
    lines = cell.split('\n', 2)
    country = lines[0].strip()
    title = ""
    body = ""
    if len(lines) > 1:
        line2 = lines[1].strip()
        if line2.startswith("Titre:"):
            title = line2[len("Titre:"):].strip()
        else:
            body = line2
    if len(lines) > 2:
        rest = lines[2]
        # remove leading 'corps' if present
        if rest.startswith('corps'):
            body = rest[len('corps'):]
        else:
            body = rest
    return country, title, body

# Language code lookup (ISO 639-1 / extended) per country
LANG = {
    'France':'fr','Wallonie':'fr','Canada[Groupement]':'en','Suisse':'fr',
    'Luxembourg':'fr','États-Unis[Référence]':'en','Espagne':'es','Italie':'it',
    'Portugal':'pt','Royaume-Uni[Groupement]':'en','Brésil':'pt-BR','Allemagne':'de',
    'Mexique':'es-MX','Inde[Groupement]':'en','Chili':'es-CL','Argentine':'es-AR',
    'Colombie':'es-CO','Pays-Bas':'nl','Australie[Groupement]':'en','Indonésie':'id',
    'Japon':'ja','Turquie':'tr','Norvège':'no','Afrique du Sud[Groupement]':'en',
    'Suède':'sv','Nigéria[Groupement]':'en','Pologne':'pl','Corée du Sud':'ko',
    'Flandre':'nl-BE','Irlande[Groupement]':'en','Malaisie[Groupement]':'en',
    'Nouvelle-Zélande[Groupement]':'en','Autriche':'de-AT','Danemark':'da',
    'Finlande':'fi','Schweiz':'de-CH','Russie':'ru','Ukraine':'uk','Hongrie':'hu',
    'Pérou':'es-PE','Uruguay':'es-UY','Costa Rica':'es-CR','Israël':'he',
    'Singapour[Groupement]':'en','Taïwan':'zh-TW','Hong-Kong':'zh-TW',
    'Slovaquie':'sk','Tchéquie':'cs','Maroc':'fr','Grèce':'el','Croatie':'hr',
    'Slovénie':'sl','Estonie':'et','Lettonie':'lv','Serbie':'sr','Roumanie':'ro',
    'Lituanie':'lt','Bulgarie':'bg','Émirats Arabes Unis[Groupement]':'en',
    'Panama':'es-PA','Malte[Groupement]':'en','Ghana[Groupement]':'en',
    'République Dominicaine':'es-DO','Vietnam':'vi','Bosnie-Herzégovine':'bs',
    'Albanie':'sq','Sénégal':'fr','Nicaragua':'es-NI','Honduras':'es-HN',
    'Cameroun':'fr','Bolivie':'es-BO','El Salvador':'es-SV','Équateur':'es-EC',
    'Paraguay':'es-PY','Guatemala':'es-GT','Mozambique':'pt-MZ',
    'Cape Vert':'pt-CV','Philippines[Groupement]':'en','Lesotho[Groupement]':'en',
    'Qatar':'ar','Puerto Rico':'es-PR','Mauritius[Groupement]':'en',
    'Ouganda[Groupement]':'en','Tanzanie[Groupement]':'en','Botswana[Groupement]':'en',
    'Namibie[Groupement]':'en','Islande[Groupement]':'en','Brunei[Groupement]':'en',
    'Chypre':'el-CY','Moldavie':'ro-MD','Tunisie':'ar','Rwanda[Groupement]':'en',
    'Bahreïn':'ar','Oman':'ar','Jamaïque[Groupement]':'en','Timor oriental':'pt',
    'Monténégro':'sr','Kenya[Groupement]':'en','Pakistan[Groupement]':'en',
    'Belize[Groupement]':'en','Kazakhstan':'kk','Thailand':'th',
}

# Build summary table
struct_by = {c: by_country[c]['structural'] for c in all_countries}
ai_by = {c: by_country[c]['ai'] for c in all_countries}

def counts(c):
    e = sum(1 for x in struct_by[c] if x['severity']=='error')
    w = sum(1 for x in struct_by[c] if x['severity']=='warning')
    s = 0
    for x in ai_by[c]:
        sev = x.get('severity','warning')
        if sev=='error': e += 1
        elif sev=='warning': w += 1
        elif sev=='suggestion': s += 1
        else: w += 1
    return e, w, s

today = date.today().isoformat()
notif_id = "avis_eleve_prof"

lines = []
P = lines.append

P("# Translation Quality Review - By Country")
P(f"**Date**: {today} | **Input**: avis_eleve_prof.csv | **Notifications reviewed**: 1 ({notif_id})")
P("")
P("## Summary")
P("| Country | Language | Errors | Warnings | Suggestions |")
P("|---------|----------|--------|----------|-------------|")
for c in all_countries:
    e, w, s = counts(c)
    P(f"| {c} | {LANG.get(c,'?')} | {e} | {w} | {s} |")
P("")
P("---")
P("")

# French reference (always present)
fr_country, fr_title, fr_body = split_cell(by_country['France']['cell'])
P("## French reference (France)")
P(f"**Title**: {fr_title}")
P("")
P(f"**Body**:")
P("```")
P(fr_body)
P("```")
P("")
P("_French reference is clean — no typos, malformed variables, or grammar issues detected._")
P("")
P("---")
P("")

# Item counter
ITEM = [0]
def item():
    ITEM[0] += 1
    return ITEM[0]

# ============ GROUPED SECTIONS ============

# Group 1: Untranslated French copy
fr_copy_markets = ['Wallonie','Suisse','Luxembourg','Maroc','Sénégal','Cameroun']
n = item()
P(f"## French source copy (intentional for French-language markets) — {len(fr_copy_markets)} markets")
P(f"**Markets**: {', '.join(fr_copy_markets)}")
P("")
P("### Errors / Warnings / Suggestions")
P(f"**[#{n}]** **{notif_id}** — Empty/Untranslated (false positive)")
P("- **Issue**: Structural validator flagged title and body as identical to French reference (`untranslated_body` error + `untranslated_title` warning). However, all six markets are French-speaking territories where keeping the French source verbatim is the intentional, correct content (Wallonie, Suisse francophone, Luxembourg, and the three African Francophonie markets).")
P("- **Original (FR)**: French reference verbatim.")
P("- **Current**: Identical to French reference.")
P("- **Suggested fix**: No action — French is the canonical content for these markets. Optional: add these market codes to the validator's allow-list for `untranslated_body` so future reviews don't re-flag them.")
P("")
P(f"### Current text (representative — Wallonie)")
_, t, b = split_cell(by_country['Wallonie']['cell'])
P(f"**Title**: {t}")
P("")
P("**Body**:")
P("```")
P(b)
P("```")
P("")
P("### Proposed text")
P("_(no change required — current French content is correct for all markets in this group)_")
P("")
P("---")
P("")

# Group 2: VS-16 emoji variation selector
vs16_only = ['Canada[Groupement]','Royaume-Uni[Groupement]','Pays-Bas','Australie[Groupement]',
             'Suède','Schweiz','Slovaquie','Ghana[Groupement]','Lesotho[Groupement]',
             'Mauritius[Groupement]','Namibie[Groupement]','Islande[Groupement]','Pakistan[Groupement]']
n = item()
P(f"## Cosmetic ⭐️ emoji variation selector — {len(vs16_only)} markets")
P(f"**Markets**: {', '.join(vs16_only)}")
P("")
P("### Errors / Warnings / Suggestions")
P(f"**[#{n}]** **{notif_id}** — Emoji")
P("- **Issue**: Translation uses `⭐` followed by U+FE0F variation selector (rendered as `⭐️`) where French source has bare `⭐` (U+2B50). Visually near-identical on most platforms; flagged as `emoji_extra` warning.")
P("- **Original (FR)**: `⭐ Votre professeur ...`")
P("- **Current**: `⭐️ Your tutor ...` (or local equivalent)")
P("- **Suggested fix**: Cosmetic only — either strip the U+FE0F variation selector from these markets, or add it to the French source for consistency. No user-visible defect.")
P("")
P("### Current text (representative — Royaume-Uni[Groupement])")
_, t, b = split_cell(by_country['Royaume-Uni[Groupement]']['cell'])
P(f"**Title**: {t}")
P("")
P("**Body**:")
P("```")
P(b)
P("```")
P("")
P("### Proposed text")
P("_(no functional change — strip variation selector if perfect parity with French source is desired)_")
P("")
P("---")
P("")

# Group 3: Spanish "comentario bueno" — Pérou + Costa Rica
n = item()
P("## Spanish: \"comentario bueno\" adjective order — 2 markets")
P("**Markets**: Pérou, Costa Rica")
P("")
P("### Errors / Warnings / Suggestions")
P(f"**[#{n}]** **{notif_id}** — Grammar")
P("- **Issue**: \"un comentario bueno\" places the qualitative adjective post-nominally. In Spanish, descriptive adjectives of quality precede the noun in this register. Affects both `TPL_IF` and `TPL_ELSE` branches.")
P("- **Original (FR)**: `un sympathique commentaire sur vos cours`")
P("- **Current**: `un comentario bueno sobre su experiencia dándote clases`")
P("- **Suggested fix**: `un buen comentario sobre las clases contigo`")
P("")
P("### Current text (representative — Pérou)")
_, t, b = split_cell(by_country['Pérou']['cell'])
P(f"**Title**: {t}")
P("")
P("**Body**:")
P("```")
P(b)
P("```")
P("")
P("### Proposed text")
P(f"**Title**: {t}")
P("")
P("**Body** (changes: `comentario bueno` → `buen comentario` in IF branch):")
P("```")
P(b.replace("un comentario bueno", "un buen comentario"))
P("```")
P("*(identical fix applies to all markets in this group)*")
P("")
P("---")
P("")

# Group 4: Spanish "comentario bueno + perspective" — Bolivie + Équateur
n = item()
P("## Spanish: \"comentario bueno + perspective shift\" — 2 markets")
P("**Markets**: Bolivie, Équateur")
P("")
P("### Errors / Warnings / Suggestions")
P(f"**[#{n}]** **{notif_id}** — Grammar")
P("- **Issue**: IF branch combines two issues: (1) `un comentario bueno` (post-nominal adjective — same as Pérou/Costa Rica group), (2) `sobre su experiencia dándote clases` shifts perspective to the tutor's experience. French reference centres on the student's lessons (`sur vos cours`).")
P("- **Original (FR)**: `un joli commentaire sur vos cours`")
P("- **Current**: `un comentario bueno sobre su experiencia dándote clases`")
P("- **Suggested fix**: `un bonito comentario sobre tus clases`")
P("")
P("### Current text (representative — Bolivie)")
_, t, b = split_cell(by_country['Bolivie']['cell'])
P(f"**Title**: {t}")
P("")
P("**Body**:")
P("```")
P(b)
P("```")
P("")
P("### Proposed text")
P(f"**Title**: {t}")
P("")
P("**Body** (changes: rewrite IF-branch comment phrase to match French perspective):")
P("```")
P(b.replace("un comentario bueno sobre su experiencia dándote clases", "un bonito comentario sobre tus clases"))
P("```")
P("*(identical fix applies to all markets in this group)*")
P("")
P("---")
P("")

# Group 5: Missing comma after greeting — Irlande + Nouvelle-Zélande
n = item()
P("## English: missing comma after greeting — 2 markets")
P("**Markets**: Irlande[Groupement], Nouvelle-Zélande[Groupement]")
P("")
P("### Errors / Warnings / Suggestions")
P(f"**[#{n}]** **{notif_id}** — Grammar")
P("- **Issue**: Both branches open with `Hello <b>@TPL_MEMBRE_PRENOM@</b> @TPL_PROF_PRENOM@ has...` — missing the comma after the recipient's name in the salutation, breaking standard English greeting punctuation.")
P("- **Original (FR)**: `Bonjour <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ vous a laissé...`")
P("- **Current**: `Hello <b>@TPL_MEMBRE_PRENOM@</b> @TPL_PROF_PRENOM@ has...`")
P("- **Suggested fix**: `Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has...` (insert comma after `</b>`)")
P("")
P("### Current text (representative — Irlande[Groupement])")
_, t, b = split_cell(by_country['Irlande[Groupement]']['cell'])
P(f"**Title**: {t}")
P("")
P("**Body**:")
P("```")
P(b)
P("```")
P("")
P("### Proposed text")
P(f"**Title**: {t}")
P("")
P("**Body** (changes: add comma after `</b>` in both branches):")
P("```")
P(b.replace("</b> @TPL_PROF_PRENOM@", "</b>, @TPL_PROF_PRENOM@"))
P("```")
P("*(identical fix applies to all markets in this group)*")
P("")
P("---")
P("")

# Helper: build single-market section
def single_section(country, overview, items):
    """items is a list of dicts: {category, original_fr, current, fix, severity?, structural?}"""
    P(f"## {country} ({LANG.get(country,'?')})")
    P("")
    P("### Overview")
    P(overview)
    P("")
    P("### Errors / Warnings / Suggestions")
    for it in items:
        n = item()
        P(f"**[#{n}]** **{notif_id}** — {it['category']}")
        P(f"- **Issue**: {it['issue']}")
        if it.get('original_fr'):
            P(f"- **Original (FR)**: {it['original_fr']}")
        if it.get('current'):
            P(f"- **Current**: {it['current']}")
        if it.get('fix'):
            P(f"- **Suggested fix**: {it['fix']}")
        P("")
    # Structural errors block
    struct = struct_by[country]
    if struct:
        P("### Structural Errors")
        for s in struct:
            P(f"- [{s['severity']}] {s['check']}: {s.get('message','')}")
        P("")
    _, t, b = split_cell(by_country[country]['cell'])
    P("### Current text")
    P(f"**Title**: {t}")
    P("")
    P("**Body**:")
    P("```")
    P(b)
    P("```")
    P("")

# ============ SINGLE MARKETS ============
# Italie
single_section('Italie',
    "Italian translation has two structural defects: (1) the conditional block boundaries are wrong — the IF and ELSE branches are inverted relative to French (the IF body contains the comment-display text, the ELSE branch is mostly empty). The validator flags 5 `variable_block_mismatch` errors as a result. (2) An orphan `</a>` tag appears after `@TPL_PROF_PRENOM@`. Bracket-tag counts also diverge ([LIEN] 2/3, [BOUTON] 1/2).",
    [
        {"category":"Format","issue":"Stray `</a>` closing tag after `@TPL_PROF_PRENOM@` — no `<a>` is opened anywhere in the template. Render artifact.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé également un joli commentaire`",
         "current":"`@TPL_PROF_PRENOM@</a> ha lasciato un commento positivo`",
         "fix":"Remove `</a>`: `@TPL_PROF_PRENOM@ ha lasciato un commento positivo`"},
        {"category":"Format","issue":"Conditional block structure is broken. The translation places the comment-display body inside the *IF* branch but inside an empty `<TPL_IF_AVIS_DEPOSE></TPL_IF_AVIS_DEPOSE>` pair, then the same comment in the ELSE branch — the result is the French logic inverted. Variables `@TPL_PROF_PRENOM@`, `@TPL_AVIS_URL_REPONSE@`, `@TPL_PROF_PHOTO@`, `@TPL_MEMBRE_PRENOM@`, `@TPL_AVIS_COMMENTAIRE@` end up in the wrong block.",
         "original_fr":"French uses `<TPL_IF_AVIS_DEPOSE>...comment+dashboard button...</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...invitation to reply...</TPL_ELSE_AVIS_DEPOSE>`",
         "current":"Italian uses inverted/merged structure (see `current text` below)",
         "fix":"Rebuild branch boundaries to mirror French: IF branch shows the deposited comment + dashboard button; ELSE branch shows the invitation to reply with the response link. See proposed text below."},
        {"category":"Format","issue":"Custom tag `[LIEN]` appears 3× in French source but only 2× in Italian; `[BOUTON]` 2× in French but 1× in Italian. The reply-link [LIEN]...[/LIEN] in the ELSE branch is missing its second occurrence.",
         "original_fr":"French has 3 `[LIEN]...[/LIEN]` and 2 `[BOUTON]...[/BOUTON]` blocks total",
         "current":"Italian translation is missing one `[LIEN]` and one `[BOUTON]` block",
         "fix":"Add the missing tag pairs when rebuilding the conditional structure (see proposed text)."},
    ])
# Italie proposed
P("### Proposed text")
P("**Title**: ⭐ L'insegnante @TPL_PROF_PRENOM@ ti ha lasciato un commento")
P("")
P("**Body** (changes: rebuild conditional structure to mirror French; remove `</a>`; restore missing [LIEN]/[BOUTON] pair) `[verify]`:")
P("```")
P("<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Ciao <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ ha lasciato anche un bel commento sulla lezione svolta insieme: \"<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>\" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|La mia dashboard[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Ciao <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ ha lasciato un commento positivo sulla lezione svolta insieme. Ritagliati qualche minuto [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>per rispondere</u>[/LIEN]. @TPL_PROF_PRENOM@ è impaziente di ricevere una tua risposta. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Rispondi a @TPL_PROF_PRENOM@[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>")
P("```")
P("")
P("---")
P("")

# Portugal
single_section('Portugal',
    "Portugal's translation has a stray `</a>` artifact after `@TPL_PROF_PRENOM@`, plus a semantic issue in the ELSE branch where `também` (also) is used inappropriately — the ELSE branch fires when no review text exists yet, so 'also' doesn't make sense. The ELSE-branch text also incorrectly leads with the same 'also left an excellent comment' phrase before pivoting to the call-to-action.",
    [
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@` in IF branch — orphan tag.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé également un joli commentaire`",
         "current":"`@TPL_PROF_PRENOM@</a> também lhe deixou um excelente comentário`",
         "fix":"Remove `</a>`: `@TPL_PROF_PRENOM@ também lhe deixou um excelente comentário`"},
        {"category":"Grammar","issue":"In the ELSE branch (no review yet), the text says `também lhe deixou um excelente comentário sobre as suas aulas:` — but `também` (also) is semantically wrong here; the ELSE branch fires when there is no comment text. The full sentence is also a near-duplicate of the IF-branch opener instead of the French ELSE-branch invitation to reply.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé un sympathique commentaire sur vos cours.`",
         "current":"`@TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: Dedique alguns minutos`",
         "fix":"Rewrite to match French ELSE: `@TPL_PROF_PRENOM@ deixou-lhe um comentário simpático sobre as suas aulas. Dedique alguns minutos para lhe responder...`"},
        {"category":"Grammar","issue":"ELSE branch ends with a stray rogue character `”` (right curly quote) after `entusiasmo a sua resposta.`",
         "original_fr":"(no trailing quote in French ELSE)",
         "current":"`@TPL_PROF_PRENOM@ aguarda com entusiasmo a sua resposta.”`",
         "fix":"Remove the stray closing quote."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Professor(a) @TPL_PROF_PRENOM@ deixou-lhe um comentário")
P("")
P("**Body** (changes: remove `</a>`, rewrite ELSE branch to match French semantics, remove trailing curly quote) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|O meu painel de controlo[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ deixou-lhe um comentário simpático sobre as suas aulas. Dedique alguns minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para lhe responder</u>[/LIEN]. @TPL_PROF_PRENOM@ aguarda com entusiasmo a sua resposta. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver o comentário[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Brésil
single_section('Brésil',
    "Brazilian Portuguese has formatting noise inside `[LIEN]` and `[BOUTON]` tag delimiters in the IF branch (extra spaces around the pipe and inside the bracket pair), and a tone observation on the title using the clitic `te` — informal address is the brand standard for pt-BR so this is a tone note, not an error.",
    [
        {"category":"Format","issue":"Tag delimiters in the IF branch contain extra whitespace inside the brackets and around the pipe: `[LIEN] [URL_QUI_CONNECTE|...] | @TPL_PROF_PHOTO@ [/LIEN]`. Spaces inside template tag tokens can break parsing in the BO renderer.",
         "original_fr":"`[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN]`",
         "current":"`[LIEN] [URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@] | @TPL_PROF_PHOTO@ [/LIEN]`",
         "fix":"Strip all whitespace inside brackets and around the pipe — match the French token format exactly."},
        {"category":"Tone","issue":"Title uses the clitic `te` (`te deixou um comentário`). Informal address is the brand standard for Brazilian Portuguese (pt-BR is in `informal_standard_languages`), so this is informational, not an error. Keep current usage."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Seu professor @TPL_PROF_PRENOM@ te deixou um comentário")
P("")
P("**Body** (changes: strip whitespace inside `[LIEN]`/`[BOUTON]` tag tokens in IF branch):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também deixou um comentário legal sobre as aulas: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Meu painel de controle[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ deixou um comentário muito legal sobre as aulas. Por favor, reserve alguns minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para responder</u>[/LIEN]. @TPL_PROF_PRENOM@ já aguarda o seu feedback. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver o comentário[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Inde[Groupement]
single_section('Inde[Groupement]',
    "Indian English has only the stray `</a>` artifact in the IF branch (plus the cosmetic VS-16 emoji warning).",
    [
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@` in IF branch — orphan tag, no `<a>` opens.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé également un joli commentaire`",
         "current":"`@TPL_PROF_PRENOM@</a> has left a review of your lessons`",
         "fix":"Remove `</a>`: `@TPL_PROF_PRENOM@ has left a review of your lessons`"},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Your teacher @TPL_PROF_PRENOM@ has left you a review")
P("")
P("**Body** (changes: remove stray `</a>` in IF branch):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has left a review of your lessons: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|My dashboard[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has left a review of your lessons. Take a few minutes [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>to respond to them</u>[/LIEN]. @TPL_PROF_PRENOM@ is looking forward to your response. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|See the review[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Colombie
single_section('Colombie',
    "Colombian Spanish has the same `comentario bueno` / quality-adjective ordering issue as the LATAM group, plus a separate gendered-pronoun assumption (`encantado` masculine) in the ELSE branch.",
    [
        {"category":"Grammar","issue":"`un comentario bueno` — quality adjective placed post-nominally. Affects both branches.",
         "original_fr":"`un sympathique commentaire sur vos cours`",
         "current":"`@TPL_PROF_PRENOM@ también te ha dejado un comentario sobre tus clases` (IF) / `@TPL_PROF_PRENOM@ te ha dejado un comentario sobre tus clases` (ELSE) — note: the `bueno` issue actually does NOT appear in this market's text — Colombie's body uses 'comentario sobre tus clases' without 'bueno'. (Re-flagged finding superseded.)",
         "fix":"No change required for the `bueno` issue — it does not actually appear in Colombie's text. (The AI reviewer false-flagged this; verify against current text below.)"},
        {"category":"Suggestion","issue":"In the ELSE branch, `estará encantado de recibir tu respuesta` uses the masculine `encantado`, assuming the tutor is male. The tutor's gender is unknown at send time. Consider gender-neutral phrasing.",
         "original_fr":"`@TPL_PROF_PRENOM@ se fait déjà une joie de votre retour.`",
         "current":"`@TPL_PROF_PRENOM@ estará encantado de recibir tu respuesta.`",
         "fix":"Use a gender-neutral verb: `@TPL_PROF_PRENOM@ estará feliz de recibir tu respuesta.`"},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Tu profesor @TPL_PROF_PRENOM@ te dejó un comentario")
P("")
P("**Body** (changes: ELSE branch — `encantado` → `feliz` for gender-neutral phrasing) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hola <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ también te ha dejado un comentario sobre tus clases: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ir a mi panel[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hola <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ te ha dejado un comentario sobre tus clases. Tómate unos minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para responderle</u>[/LIEN]. @TPL_PROF_PRENOM@ estará feliz de recibir tu respuesta. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver el comentario[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Norvège
single_section('Norvège',
    "Norwegian has a stray `</a>` artifact plus a missing `<b>` wrapper around `@TPL_MEMBRE_PRENOM@` in the IF branch (the ELSE branch correctly bolds it). No subject-variable issues in this notification (the rule about `@TPL_MATIERE_*@` doesn't apply — there's no subject variable here).",
    [
        {"category":"Format","issue":"Stray `</a>` and spurious comma after `@TPL_PROF_PRENOM@` in the IF branch.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé également un joli commentaire`",
         "current":"`@TPL_PROF_PRENOM@</a>, har gitt deg en tilbakemelding`",
         "fix":"Remove `</a>` and the comma: `@TPL_PROF_PRENOM@ har gitt deg en tilbakemelding`"},
        {"category":"Format","issue":"In the IF branch, `@TPL_MEMBRE_PRENOM@` is not wrapped in `<b>...</b>` (it reads `Hei @TPL_MEMBRE_PRENOM@,`). The ELSE branch correctly uses `<b>@TPL_MEMBRE_PRENOM@</b>`.",
         "original_fr":"`Bonjour <b>@TPL_MEMBRE_PRENOM@</b>,`",
         "current":"`Hei @TPL_MEMBRE_PRENOM@,` (IF branch)",
         "fix":"Wrap in bold: `Hei <b>@TPL_MEMBRE_PRENOM@</b>,`"},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Læreren din @TPL_PROF_PRENOM@ har skrevet en tilbakemelding til deg")
P("")
P("**Body** (changes: remove `</a>`+comma in IF; bold `@TPL_MEMBRE_PRENOM@` in IF):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hei <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ har gitt deg en tilbakemelding: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Mitt dashbord[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hei <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ har gitt deg en hyggelig tilbakemelding. Bruk noen minutter på [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>å svare læreren din</u>[/LIEN]. @TPL_PROF_PRENOM@ blir glad for å høre din tilbakemelding. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Se tilbakemeldingen[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Pologne
single_section('Pologne',
    "Polish has multiple grammar issues (case-agreement errors in both branches) plus a tone-register concern (informal `Witaj`/`Twoją` whereas Polish is in `formal_vous_languages`). The structural validator's `conditional_extra` warning for `<TPL_IF_PROF_FEMININ>` is a false positive — Polish genuinely needs gender agreement on the past-tense verb (`zostawił/zostawiła`), so the extra conditional is correct localization.",
    [
        {"category":"Tone","issue":"Polish requires formal address (Pan/Pani forms). The translation uses informal register: `Witaj` (informal greeting), `Twoją` (informal possessive), `tobie/Ci` (informal pronouns).",
         "original_fr":"`Bonjour <b>@TPL_MEMBRE_PRENOM@</b>` ... `vous a laissé`",
         "current":"`Witaj <b>@TPL_MEMBRE_PRENOM@</b>` ... `Ci komentarz`",
         "fix":"Switch to formal greeting `Dzień dobry` and use Pan/Pani forms throughout. Example title: `⭐ Pana/Pani nauczyciel, @TPL_PROF_PRENOM@, zostawił/zostawiła Panu/Pani komentarz`"},
        {"category":"Grammar","issue":"IF branch: `opinie dotyczących Waszych lekcji` — case agreement error. `opinie` is nominative/accusative plural of `opinia` but `dotyczących` is a participle that doesn't agree with it; also `Waszych` is plural-second-person (`your-pl`) which is awkward in formal singular address.",
         "original_fr":"`vous a laissé également un joli commentaire sur vos cours`",
         "current":"`zostawił/a również opinie dotyczących Waszych lekcji`",
         "fix":"`zostawił/a również opinię dotyczącą Pana/Pani lekcji` (singular, formal)"},
        {"category":"Grammar","issue":"ELSE branch: `opinie dotyczący Waszych lekcji` — same case/gender agreement error.",
         "original_fr":"`vous a laissé un sympathique commentaire sur vos cours`",
         "current":"`zostawił/a opinie dotyczący Waszych lekcji`",
         "fix":"`zostawił/a opinię dotyczącą Pana/Pani lekcji`"},
        {"category":"Format","issue":"Validator flagged `<TPL_IF_PROF_FEMININ>` as `conditional_extra` (in translation but not in French). This is a FALSE POSITIVE — Polish needs gender agreement on past-tense verb forms. Keep the conditional.",
         "fix":"No action — gender conditional is required for correct Polish localization."},
    ])
P("### Proposed text")
P("**Title** (changes: switch to formal Pan/Pani forms) `[verify]`: ⭐ Pana/Pani nauczyciel, @TPL_PROF_PRENOM@, <TPL_IF_PROF_FEMININ>zostawiła</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>zostawił</TPL_ELSE_PROF_FEMININ> Panu/Pani komentarz")
P("")
P("**Body** (changes: switch greeting to `Dzień dobry`, fix case/gender agreement, switch to Pan/Pani forms throughout) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Dzień dobry <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ <TPL_IF_PROF_FEMININ>zostawiła</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>zostawił</TPL_ELSE_PROF_FEMININ> również opinię dotyczącą Pana/Pani lekcji: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Panel użytkownika[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Dzień dobry <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ <TPL_IF_PROF_FEMININ>zostawiła</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>zostawił</TPL_ELSE_PROF_FEMININ> opinię dotyczącą Pana/Pani lekcji. Proszę poświęcić kilka minut [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>aby odpowiedzieć</u>[/LIEN]. @TPL_PROF_PRENOM@ już czeka na Pana/Pani odpowiedź. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Zobacz komentarz[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Corée du Sud
single_section('Corée du Sud',
    "Korean cell contains TWO independent translations concatenated: a Korean-only rendering followed by a full English fallback (`Hello <b>@TPL_MEMBRE_PRENOM@</b>...`). The Korean section uses a custom `[TITRE]...[/TITRE]` block at the top of the body and skips the `<TPL_IF_AVIS_DEPOSE>/<TPL_ELSE_AVIS_DEPOSE>` conditionals entirely, putting all variables in the body without branch logic. All 5 `variable_block_mismatch` errors stem from this. Tone is acceptable for ko (formal `요`/`-ㅂ니다` register).",
    [
        {"category":"Format","issue":"Cell contains two concatenated translations (Korean + English fallback). The English block is residue from a translation handoff and should not ship.",
         "original_fr":"(single Korean translation expected)",
         "current":"`...Korean text... [LIEN]...|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@</a>, has left you a review for your lesson...`",
         "fix":"Remove the English fallback block entirely. The Korean translation must stand alone."},
        {"category":"Format","issue":"Korean version omits the `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>` branch structure. All variables sit in the unconditional body, so the same content is shown whether or not a comment exists. Result: 5 `variable_block_mismatch` errors and the `conditional_missing`/`conditional_else_missing` errors.",
         "original_fr":"French splits comment-display vs invitation-to-reply via the `AVIS_DEPOSE` conditional",
         "current":"Korean has no conditional — single body shown unconditionally",
         "fix":"Rebuild Korean translation around `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>` mirroring the French structure."},
        {"category":"Format","issue":"Custom `[TITRE]...[/TITRE]` tag at the start of the body is non-standard — titles belong in the `Titre:` field, not embedded in the body.",
         "current":"`[TITRE]@TPL_PROF_PRENOM@님이 후기를 남겼습니다[/TITRE]`",
         "fix":"Remove the `[TITRE]` block from the body — title is already in the `Titre:` field."},
        {"category":"Emoji","issue":"Title uses ✏️ where French has ⭐. Validator flagged emoji_missing (`⭐`) + emoji_extra (`️ ✍ 👍`).",
         "original_fr":"`⭐ Votre professeur ...`",
         "current":"`✏️ @TPL_PROF_PRENOM@ 튜터님이 새 후기를 남겼습니다`",
         "fix":"Replace ✏️ with ⭐ to match French source."},
    ])
P("### Proposed text")
P("**Title**: ⭐ @TPL_PROF_PRENOM@ 튜터님이 후기를 남겼습니다 `[verify]`")
P("")
P("**Body** (changes: rebuild around `AVIS_DEPOSE` conditional, remove embedded `[TITRE]`, drop English fallback block) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] 안녕하세요, <b>@TPL_MEMBRE_PRENOM@</b>님. @TPL_PROF_PRENOM@ 튜터님이 학생님과의 수업에 관한 후기를 남기셨습니다: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|대시보드 보기[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] 안녕하세요, <b>@TPL_MEMBRE_PRENOM@</b>님. @TPL_PROF_PRENOM@ 튜터님이 학생님과의 수업에 관한 후기를 남기셨습니다. 잠시 시간을 내어 [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>답글을 남겨</u>[/LIEN] 경험을 공유해 주세요. @TPL_PROF_PRENOM@ 튜터님이 답글을 기다리고 있습니다. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PRENOM@ 튜터님께 답글 남기기[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Flandre
single_section('Flandre',
    "Flemish (nl-BE) translation looks linguistically clean. Two structural warnings: (1) `<TPL_IF_PROF_FEMININ>` conditional flagged as extra by the validator — but Dutch genuinely needs `lerares`/`leraar` gender disambiguation, so this is a FALSE POSITIVE; (2) VS-16 `⭐️` emoji variation selector — cosmetic.",
    [
        {"category":"Format","issue":"Validator flagged `<TPL_IF_PROF_FEMININ>` as `conditional_extra`. FALSE POSITIVE — Dutch needs gender agreement (`lerares` feminine vs `leraar` masculine). Keep the conditional.",
         "fix":"No action — the gender conditional is correct localization."},
    ])
P("### Proposed text")
P("_(no functional change — current translation is correct; cosmetic VS-16 emoji + false-positive gender conditional)_")
P("")
P("---")
P("")

# Finlande
single_section('Finlande',
    "Finnish cell concatenates two separate body translations (no `<TPL_IF_AVIS_DEPOSE>`/`<TPL_ELSE_AVIS_DEPOSE>` block at all — both branches sit unconditionally one after the other). All 5 `variable_block_mismatch` errors stem from this. The Finnish text itself is OK; the structure must be rebuilt.",
    [
        {"category":"Format","issue":"Body concatenates IF-branch text and ELSE-branch text back-to-back with no conditional wrappers. Both will render simultaneously, so users always see the comment-display block AND the invitation-to-reply block.",
         "original_fr":"French wraps each variant in `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>`",
         "current":"`[LIEN]...[/LIEN] Hei @TPL_MEMBRE_PRENOM@, @TPL_PROF_PRENOM@ on jättänyt kommentin... [BOUTON]Hallintapaneelini[/BOUTON][LIEN]...[/LIEN] Hei @TPL_MEMBRE_PRENOM@, @TPL_PROF_PRENOM@ on jättänyt kivan kommentin... [BOUTON]Katso kommentti[/BOUTON]`",
         "fix":"Wrap the first half in `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE>` and the second half in `<TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>`. See proposed text."},
        {"category":"Format","issue":"In the IF-branch portion, `@TPL_MEMBRE_PRENOM@` is followed by an orphan `</a>` after `@TPL_PROF_PRENOM@`.",
         "current":"`@TPL_PROF_PRENOM@</a> on jättänyt kommentin oppitunnista`",
         "fix":"Remove `</a>`."},
    ])
P("### Proposed text")
P("**Title**: ⭐ Opettajasi @TPL_PROF_PRENOM@ jätti sinulle kommentin")
P("")
P("**Body** (changes: wrap in IF/ELSE conditionals; remove stray `</a>`) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hei <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ on jättänyt kommentin oppitunnista: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Hallintapaneelini[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hei <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ on jättänyt kivan kommentin oppitunnistanne. Ota muutama minuutti [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>vastataksesi</u>[/LIEN]. @TPL_PROF_PRENOM@ odottaa sitä jo innolla. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Katso kommentti[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Russie
single_section('Russie',
    "Russian translation has major structural issues (no `<TPL_IF_AVIS_DEPOSE>`/`<TPL_ELSE_AVIS_DEPOSE>` block — single unconditional body, missing one `[LIEN]`, missing `[BOUTON]`, missing ⭐, stray `</a>`) and a tone deviation (informal `вы` rather than formal capitalized `Вы` — Russian is in `formal_vous_languages`). Adds extra Superprof trust copy not in French source.",
    [
        {"category":"Format","issue":"Body has no conditional structure — single `[LIEN]...[/LIEN]` + `[BOUTON]...[/BOUTON]` shown unconditionally. Missing the second `[LIEN]` (reply-link) and the IF-branch `[BOUTON]` for `Мое информационное табло`.",
         "original_fr":"French has 3 `[LIEN]` and 2 `[BOUTON]` across IF/ELSE conditionals",
         "current":"Russian has 1 `[LIEN]` (in opening) + 1 `[LIEN]` (Отправьте) + 1 `[BOUTON]`",
         "fix":"Rebuild around `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>` and add the missing tag pairs."},
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@`.",
         "current":"`@TPL_PROF_PRENOM@</a> оставил(а) отзыв`",
         "fix":"Remove `</a>`."},
        {"category":"Tone","issue":"Russian is in `formal_vous_languages`. Current text uses lowercase `вы`/`ваши` — formal-respect convention in Russian written communication capitalizes `Вы`/`Ваш`/`Ваши` when addressing one person. Body capitalization is inconsistent.",
         "current":"`оставил(а) отзыв после занятия с вами` ... `ваши отзывы очень ценны для нас`",
         "fix":"Capitalize formal pronouns: `Вы`, `Ваши`, `Вам` etc. throughout."},
        {"category":"Grammar","issue":"Body adds `Superprof = доверие + безупречная репутация` and a closing `Большое спасибо!` — content not present in French source.",
         "original_fr":"(no Superprof trust statement in French)",
         "current":"`Superprof = доверие + безупречная репутация, поэтому ваши отзывы очень ценны для нас. Большое спасибо!`",
         "fix":"Remove the extra Superprof trust sentences — keep only what corresponds to French."},
        {"category":"Emoji","issue":"Title uses ✏️ — French source uses ⭐. Validator flagged `emoji_missing ⭐` and `emoji_extra ️ ✍`.",
         "current":"`✏️ @TPL_PROF_PRENOM@ оставил(а) вам отзыв`",
         "fix":"Replace ✏️ with ⭐."},
    ])
P("### Proposed text")
P("**Title** (changes: ✏️ → ⭐) `[verify]`: ⭐ @TPL_PROF_PRENOM@ оставил(а) Вам отзыв")
P("")
P("**Body** (changes: rebuild around AVIS_DEPOSE conditional; remove `</a>`; capitalize formal pronouns; drop extra Superprof copy) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Здравствуйте, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ оставил(а) Вам отзыв после занятия: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Моя панель[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Здравствуйте, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ оставил(а) Вам приятный отзыв после занятия. Уделите несколько минут, [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>чтобы ответить</u>[/LIEN]. @TPL_PROF_PRENOM@ уже ждёт Вашего ответа. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Посмотреть отзыв[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Taïwan
single_section('Taïwan',
    "Taiwanese Traditional Chinese cell concatenates two truncated bodies, plus a stray French `Bonjour` opener (mojibake-decoded as Chinese characters). All `variable_block_mismatch` errors stem from missing `<TPL_IF_AVIS_DEPOSE>` wrapper; only `<TPL_ELSE_AVIS_DEPOSE>` is present. Length flagged as 23% of French. Stray `</a>`. Title emoji ✏️ instead of ⭐.",
    [
        {"category":"Format","issue":"No `<TPL_IF_AVIS_DEPOSE>` block. Translation only wraps the ELSE branch and leaves the IF-branch content unconditional, so the `[BOUTON]` always renders without the dashboard button variant.",
         "original_fr":"French has both `<TPL_IF_AVIS_DEPOSE>...</TPL_IF_AVIS_DEPOSE>` and `<TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>`",
         "current":"`<TPL_IF_AVIS_DEPOSE></TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>...</TPL_ELSE_AVIS_DEPOSE>` — IF empty",
         "fix":"Add IF-branch content (greeting + comment-display + dashboard button)."},
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@`.",
         "current":"`@TPL_PROF_PRENOM@</a>，已經對您進行了評價`",
         "fix":"Remove `</a>`."},
        {"category":"Format","issue":"French opening `Bonjour <b>@TPL_MEMBRE_PRENOM@</b>` left untranslated — appears in Chinese cell as `Bonjour <b>@TPL_MEMBRE_PRENOM@</b>` mid-text.",
         "current":"`Bonjour <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@</a>`",
         "fix":"Replace with Chinese greeting: `<b>@TPL_MEMBRE_PRENOM@</b>，您好`"},
        {"category":"Emoji","issue":"Title uses ✏️ — French uses ⭐.",
         "current":"`✏️ 你的老師@TPL_PROF_PRENOM@給你評價了`",
         "fix":"Replace ✏️ with ⭐."},
        {"category":"Grammar","issue":"Length flagged at 23% of French — content truncated. Even after rebuilding IF branch, the ELSE branch is missing the `[BOUTON]` translation and the `[LIEN]` reply prompt is partial.",
         "fix":"Restore full content per French structure (see proposed text)."},
    ])
P("### Proposed text")
P("**Title** (changes: ✏️ → ⭐) `[verify]`: ⭐ 你的老師 @TPL_PROF_PRENOM@ 給你留下了評價")
P("")
P("**Body** (changes: rebuild IF branch; remove stray `</a>` and untranslated `Bonjour`; restore [BOUTON] in both branches) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <b>@TPL_MEMBRE_PRENOM@</b>，您好。@TPL_PROF_PRENOM@ 給你留下了關於課程的評價：「<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>」 [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|我的個人中心[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <b>@TPL_MEMBRE_PRENOM@</b>，您好。@TPL_PROF_PRENOM@ 已對你的課程留下了評價。花幾分鐘 [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>回覆他</u>[/LIEN]，@TPL_PROF_PRENOM@ 已經很期待你的回覆了。 [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|查看評價[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Hong-Kong
single_section('Hong-Kong',
    "Hong Kong Traditional Chinese has all the structural issues of Taïwan (no AVIS_DEPOSE conditional, missing tags, length 35%) plus inconsistent formality: title uses formal `您`, body switches to informal `你`. zh-TW is in `formal_vous_languages` so register should stay formal throughout. Body adds extra Superprof trust copy not in French source.",
    [
        {"category":"Format","issue":"No `<TPL_IF_AVIS_DEPOSE>`/`<TPL_ELSE_AVIS_DEPOSE>` blocks. Single unconditional body — both review-display and reply-invitation render simultaneously.",
         "original_fr":"French has both AVIS_DEPOSE branches",
         "current":"No conditional wrappers",
         "fix":"Wrap content in IF/ELSE conditionals matching French structure."},
        {"category":"Format","issue":"Missing one `[LIEN]` and one `[BOUTON]`. `[LIEN]` 2× in current vs 3× expected; `[BOUTON]` 1× in current vs 2× expected.",
         "fix":"Restore the IF-branch [BOUTON] (`我的個人中心`) and the ELSE-branch reply [LIEN]."},
        {"category":"Tone","issue":"Title uses formal `您` (`給您留言了`) but body uses informal `你` (`你好`, `給你的`, `你的意見`). zh-TW is in `formal_vous_languages` — the register must be formal end-to-end.",
         "current":"Title: `您的老師@TPL_PROF_PRENOM@給您留言了` / Body: `你好`, `給你的`, `你的意見`",
         "fix":"Use `您` consistently throughout the body."},
        {"category":"Grammar","issue":"Body adds `Superprof 非常重視用戶之間的信任，你的意見對我們非常有價值。先說一聲，非常感謝！` — Superprof trust statement and pre-emptive thank-you not in the French source.",
         "current":"`Superprof 非常重視用戶之間的信任，你的意見對我們非常有價值。先說一聲，非常感謝！`",
         "fix":"Remove the extra Superprof copy — keep only content that corresponds to the French template."},
        {"category":"Emoji","issue":"Title uses ✏️ — French uses ⭐.",
         "fix":"Replace ✏️ with ⭐."},
    ])
P("### Proposed text")
P("**Title** (changes: ✏️ → ⭐; consistent formal `您`) `[verify]`: ⭐ 您的老師 @TPL_PROF_PRENOM@ 給您留言了")
P("")
P("**Body** (changes: rebuild around AVIS_DEPOSE conditional; consistent formal `您`; drop extra Superprof copy; restore missing [LIEN]/[BOUTON]) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <b>@TPL_MEMBRE_PRENOM@</b>您好，@TPL_PROF_PRENOM@ 給您留下了關於課程的評價：「<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>」 [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|我的個人中心[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <b>@TPL_MEMBRE_PRENOM@</b>您好，@TPL_PROF_PRENOM@ 已對您的課程留下了評價。請花幾分鐘 [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>答覆 @TPL_PROF_PRENOM@</u>[/LIEN]，@TPL_PROF_PRENOM@ 已經很期待您的回覆了。 [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|查看評價[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Tchéquie
single_section('Tchéquie',
    "Czech (cs) is in `formal_vous_languages`. Title correctly capitalizes the formal pronoun `Vám`, but the body uses lowercase `vám`/`vašim` throughout — inconsistent formal register. Also a minor idiom suggestion in the ELSE branch.",
    [
        {"category":"Tone","issue":"Body uses lowercase `vám`/`vašim`/`vaší` while the title uses capitalized formal `Vám`. In Czech formal written communication, second-person pronouns are capitalized as a marker of respect.",
         "current":"`@TPL_PROF_PRENOM@ vám zanechal/a hezký komentář k vašim lekcím`",
         "fix":"Capitalize all formal second-person pronouns: `vám` → `Vám`, `vašim` → `Vašim`, `vaší` → `Vaší`."},
        {"category":"Suggestion","issue":"ELSE branch uses `Udělejte si pár minut` (literally 'make yourself a few minutes') — understandable but `Věnujte pár minut` ('devote/spare a few minutes') is more idiomatic.",
         "current":"`Udělejte si pár minut [LIEN]...|<u>abyste mu/ji odpověděli</u>[/LIEN]`",
         "fix":"`Věnujte pár minut [LIEN]...|<u>tomu, abyste mu/ji odpověděli</u>[/LIEN]`"},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Váš učitel @TPL_PROF_PRENOM@ Vám zanechal/a recenzi")
P("")
P("**Body** (changes: capitalize formal pronouns Vám/Vašim/Vaší; soften ELSE idiom):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Dobrý den <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ Vám zanechal/a hezký komentář k Vašim lekcím: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Moje nástěnka[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Dobrý den <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ Vám zanechal/a hezký komentář k Vašim lekcím. Věnujte pár minut [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>tomu, abyste mu/ji odpověděli</u>[/LIEN]. @TPL_PROF_PRENOM@ už se těší na Vaši odpověď. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Zobrazit komentář[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Grèce
single_section('Grèce',
    "Greek translation is linguistically clean. The single warning (`<TPL_IF_PROF_FEMININ>` conditional extra) is a FALSE POSITIVE — Greek uses the gender-disambiguated `Η Δασκάλα`/`Ο Δάσκαλος` correctly, mirroring how Polish and Slovenian use this pattern.",
    [
        {"category":"Format","issue":"Validator flagged `<TPL_IF_PROF_FEMININ>` as conditional_extra. FALSE POSITIVE — Greek requires gendered teacher noun (Η Δασκάλα fem. vs Ο Δάσκαλος masc.).",
         "fix":"No action — the gender conditional is correct localization."},
    ])
P("### Proposed text")
P("_(no change required — current translation is correct; gender conditional is a false-positive flag)_")
P("")
P("---")
P("")

# Croatie
single_section('Croatie',
    "Croatian translation has a spurious comma after `@TPL_PROF_PRENOM@` in the title plus a false-positive `conditional_extra` warning for `<TPL_IF_PROF_FEMININ>` (Croatian needs gender agreement on past participle `ostavila/ostavio`).",
    [
        {"category":"Grammar","issue":"Title has a spurious comma after `@TPL_PROF_PRENOM@`: `Vaš učitelj @TPL_PROF_PRENOM@, vam je [ostavila|ostavio] komentar`. In Croatian, no comma is required between subject (`@TPL_PROF_PRENOM@`) and the predicate (`vam je`).",
         "current":"`⭐ Vaš učitelj @TPL_PROF_PRENOM@, vam je <TPL_IF_PROF_FEMININ>ostavila</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>ostavio</TPL_ELSE_PROF_FEMININ> komentar`",
         "fix":"`⭐ Vaš učitelj @TPL_PROF_PRENOM@ vam je <TPL_IF_PROF_FEMININ>ostavila</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>ostavio</TPL_ELSE_PROF_FEMININ> komentar`"},
        {"category":"Format","issue":"`<TPL_IF_PROF_FEMININ>` flagged conditional_extra — FALSE POSITIVE, Croatian needs gender agreement.",
         "fix":"No action."},
    ])
P("### Proposed text")
P("**Title** (changes: remove comma after `@TPL_PROF_PRENOM@`): ⭐ Vaš učitelj @TPL_PROF_PRENOM@ vam je <TPL_IF_PROF_FEMININ>ostavila</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>ostavio</TPL_ELSE_PROF_FEMININ> komentar")
P("")
P("**Body** (no functional change required):")
_, t, b = split_cell(by_country['Croatie']['cell'])
P("```")
P(b)
P("```")
P("")
P("---")
P("")

# Slovénie
single_section('Slovénie',
    "Slovenian has a critical issue: the ELSE branch contains an untranslated French sentence (`@TPL_PROF_PRENOM@ vous a laissé un sympathique commentaire sur vos cours.`). Title is missing the gender conditional that the body uses (gendered greetings `Pozdravljen/Pozdravljena` are present in body but the noun `učitelj` in the title is locked masculine).",
    [
        {"category":"Grammar","issue":"ELSE branch leaks an untranslated French sentence: `@TPL_PROF_PRENOM@ vous a laissé un sympathique commentaire sur vos cours.` — appears verbatim before `Vzemite si nekaj minut`. This is a copy-paste artifact from the translation handoff.",
         "original_fr":"`@TPL_PROF_PRENOM@ vous a laissé un sympathique commentaire sur vos cours.`",
         "current":"Identical French left in Slovenian ELSE branch",
         "fix":"Replace with Slovenian: `@TPL_PROF_PRENOM@ vam je pustil/a komentar o vaših tečajih.`"},
        {"category":"Grammar","issue":"Title locks masculine `učitelj` and `pustil` while the body uses `Pozdravljen/Pozdravljena` gender conditional. Title should also disambiguate.",
         "current":"`⭐ Vaš učitelj @TPL_PROF_PRENOM@ vam je pustil komentar`",
         "fix":"Add gender conditional: `⭐ Vaš<TPL_IF_PROF_FEMININ>a učiteljica</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ> učitelj</TPL_ELSE_PROF_FEMININ> @TPL_PROF_PRENOM@ vam je <TPL_IF_PROF_FEMININ>pustila</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>pustil</TPL_ELSE_PROF_FEMININ> komentar`"},
        {"category":"Format","issue":"`<TPL_IF_PROF_FEMININ>` (in body) flagged conditional_extra — FALSE POSITIVE, Slovenian needs gender agreement.",
         "fix":"No action — keep the conditional."},
    ])
P("### Proposed text")
P("**Title** (changes: add gender conditional) `[verify]`: ⭐ Vaš<TPL_IF_PROF_FEMININ>a učiteljica</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ> učitelj</TPL_ELSE_PROF_FEMININ> @TPL_PROF_PRENOM@ vam je <TPL_IF_PROF_FEMININ>pustila</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>pustil</TPL_ELSE_PROF_FEMININ> komentar")
P("")
P("**Body** (changes: replace French sentence in ELSE branch with Slovenian) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <TPL_IF_PROF_FEMININ>Pozdravljena</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>Pozdravljen </TPL_ELSE_PROF_FEMININ> <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ vam je pustil/a komentar o vaših tečajih: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Moja nadzorna plošča[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] <TPL_IF_PROF_FEMININ>Pozdravljena</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>Pozdravljen </TPL_ELSE_PROF_FEMININ> <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ vam je pustil/a komentar o vaših tečajih. Vzemite si nekaj minut [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>, da odgovorite</u>[/LIEN]. @TPL_PROF_PRENOM@ se že veseli vašega odgovora. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Oglej si komentar[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Lettonie
single_section('Lettonie',
    "Latvian has only one issue: the ELSE branch is missing the `<b>...</b>` bold wrapper around `@TPL_MEMBRE_PRENOM@`. The IF branch has it correctly. False-positive `conditional_extra` for `<TPL_IF_PROF_FEMININ>` (Latvian uses `skolotāja/skolotājs` gender disambiguation correctly).",
    [
        {"category":"Format","issue":"ELSE branch is missing `<b>` markup on `@TPL_MEMBRE_PRENOM@`. IF branch uses `<b>@TPL_MEMBRE_PRENOM@</b>` correctly; ELSE branch reads `Sveiki, @TPL_MEMBRE_PRENOM@!` (no bold).",
         "current":"`Sveiki, @TPL_MEMBRE_PRENOM@!` (ELSE branch)",
         "fix":"Add bold tags: `Sveiki, <b>@TPL_MEMBRE_PRENOM@</b>!`"},
        {"category":"Format","issue":"`<TPL_IF_PROF_FEMININ>` flagged conditional_extra — FALSE POSITIVE, Latvian needs gender agreement on `skolotāja/skolotājs`.",
         "fix":"No action."},
    ])
P("### Proposed text")
P("**Title** (no change): ⭐ Jūsu <TPL_IF_PROF_FEMININ>skolotāja</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>skolotājs</TPL_ELSE_PROF_FEMININ> @TPL_PROF_PRENOM@ atstāja Jums komentāru")
P("")
P("**Body** (changes: bold `@TPL_MEMBRE_PRENOM@` in ELSE branch):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Sveiki, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ Jums atstāja jauku komentāru par Jūsu nodarbībām: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Mans vadības panelis[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Sveiki, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ atstāja jauku komentāru par Jūsu nodarbībām. Lūdzu, veltiet dažas minūtes, [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>lai atbildētu</u>[/LIEN]. @TPL_PROF_PRENOM@ jau gaida Jūsu atsauksmes. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Skatīt komentāru[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Émirats Arabes Unis
single_section('Émirats Arabes Unis[Groupement]',
    "UAE English has cosmetic spacing issues inside `[LIEN]` and `[BOUTON]` tag delimiters in both branches (extra spaces around the pipe and inside the bracket pair).",
    [
        {"category":"Format","issue":"Tag delimiters contain extra whitespace inside the brackets and around the pipe: `[LIEN] [URL_QUI_CONNECTE|...] | @TPL_PROF_PHOTO@ [/LIEN]`.",
         "original_fr":"`[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN]`",
         "current":"`[LIEN] [URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@] | @TPL_PROF_PHOTO@ [/LIEN]`",
         "fix":"Strip all whitespace inside brackets and around the pipe."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Your tutor @TPL_PROF_PRENOM@ has left you a review")
P("")
P("**Body** (changes: strip whitespace inside `[LIEN]`/`[BOUTON]` tag tokens):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ left you a nice review on your lessons: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|My dashboard[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ left you a nice comment about your lessons. Please take a few minutes [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>to reply</u>[/LIEN]. @TPL_PROF_PRENOM@ is already looking forward to your feedback. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|See the review[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Malte[Groupement]
single_section('Malte[Groupement]',
    "Malte's English has the recurring stray `</a>` tag plus an optional pronoun-style suggestion (`them` for the tutor — gender-neutral but inconsistent with shorter sister markets).",
    [
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@` in IF branch.",
         "current":"`@TPL_PROF_PRENOM@</a> has left a review of your lessons`",
         "fix":"Remove `</a>`."},
        {"category":"Suggestion","issue":"ELSE branch link text reads `to respond to them` — `them` is grammatically valid as a singular gender-neutral pronoun, but other sister markets use `to reply` for brevity.",
         "fix":"Optional: replace with `to reply`."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Your tutor, @TPL_PROF_PRENOM@, has left you a review")
P("")
P("**Body** (changes: remove `</a>`):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has left a review of your lessons: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|My dashboard[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has left a review of your lessons. Take a few minutes [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>to respond to them</u>[/LIEN]. @TPL_PROF_PRENOM@ is looking forward to your response. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|See the review[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Mozambique
single_section('Mozambique',
    "Mozambican Portuguese has multiple issues: stray `</a>`, missing `<TPL_IF_AVIS_DEPOSE>` block (only ELSE branch present), missing one `[LIEN]` and one `[BOUTON]`.",
    [
        {"category":"Format","issue":"No `<TPL_IF_AVIS_DEPOSE>` block. Translation has only `<TPL_ELSE_AVIS_DEPOSE>` — IF-branch path has no content.",
         "fix":"Add IF-branch with greeting + comment-display + dashboard `[BOUTON]`."},
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@`.",
         "current":"`@TPL_PROF_PRENOM@</a> também te deixou um comentário`",
         "fix":"Remove `</a>`."},
        {"category":"Format","issue":"Missing one `[LIEN]` (the tutor-photo link in the IF branch) and one `[BOUTON]` (the IF-branch dashboard button).",
         "fix":"Restore both when adding the IF branch."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ O seu professor @TPL_PROF_PRENOM@ deixou-lhe um comentário")
P("")
P("**Body** (changes: add IF-branch wrapper with greeting + dashboard button; remove `</a>`) `[verify]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também te deixou um comentário sobre as suas aulas: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|O meu painel de controlo[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também te deixou um comentário sobre as suas aulas. Por favor tire alguns minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para lhe responder</u>[/LIEN]. @TPL_PROF_PRENOM@ ficará certamente contente com o seu comentário. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver o comentário[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Cape Vert
single_section('Cape Vert',
    "Cape Verde Portuguese has the recurring stray `</a>` plus a stray closing `”` (right curly quote) at the end of the ELSE branch — both are copy-paste artifacts (same pattern as Portugal).",
    [
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@` in IF branch.",
         "current":"`@TPL_PROF_PRENOM@</a> também lhe deixou um excelente comentário`",
         "fix":"Remove `</a>`."},
        {"category":"Grammar","issue":"ELSE branch ends with a stray right curly quote `”`: `@TPL_PROF_PRENOM@ aguarda com entusiasmo a sua resposta.”`",
         "current":"`...a sua resposta.”`",
         "fix":"Remove the stray `”`."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Professor(a) @TPL_PROF_PRENOM@ deixou-lhe um comentário")
P("")
P("**Body** (changes: remove `</a>` and trailing `”`):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|O meu painel de controlo[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: Dedique alguns minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para lhe responder</u>[/LIEN]. @TPL_PROF_PRENOM@ aguarda com entusiasmo a sua resposta. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver o comentário[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Philippines
single_section('Philippines[Groupement]',
    "Philippines English has the stray `</a>` plus a critical translation defect: the ELSE branch opens with the untranslated French greeting `Bonjour <b>@TPL_MEMBRE_PRENOM@</b>` (the IF branch correctly uses `Hello`).",
    [
        {"category":"Format","issue":"Stray `</a>` and spurious comma after `@TPL_PROF_PRENOM@` in IF branch.",
         "current":"`@TPL_PROF_PRENOM@</a>, has left you a nice comment on your lesson`",
         "fix":"Remove both: `@TPL_PROF_PRENOM@ has left you a nice comment on your lessons`"},
        {"category":"Grammar","issue":"ELSE branch opens with untranslated French `Bonjour` while IF branch correctly uses `Hello`. Inconsistent greeting between branches.",
         "current":"`Bonjour <b>@TPL_MEMBRE_PRENOM@</b>` (ELSE branch)",
         "fix":"Replace with `Hello <b>@TPL_MEMBRE_PRENOM@</b>`."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Your tutor @TPL_PROF_PRENOM@ has left you a review")
P("")
P("**Body** (changes: remove `</a>`+comma in IF; translate `Bonjour` → `Hello` in ELSE):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ has left you a nice comment on your lesson: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|My dashboard[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Hello <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ left you a nice comment on your lesson. Take a few minutes [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>to respond to them</u>[/LIEN]. @TPL_PROF_PRENOM@ is looking forward to your response. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|See comment[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Chypre
single_section('Chypre',
    "Greek-Cyprus translation is essentially identical to Grèce. Same false-positive `<TPL_IF_PROF_FEMININ>` warning. Title uses ✏️ where French has ⭐ (also flagged by validator as `emoji_missing ⭐` + `emoji_extra ️ ✍`).",
    [
        {"category":"Emoji","issue":"Title uses ✏️ — French source uses ⭐.",
         "current":"`✏️ Η Δασκάλα/Ο Δάσκαλος σας, @TPL_PROF_PRENOM@, σάς άφησε ένα σχόλιο`",
         "fix":"Replace ✏️ with ⭐."},
        {"category":"Format","issue":"`<TPL_IF_PROF_FEMININ>` flagged conditional_extra — FALSE POSITIVE, Greek requires gender disambiguation.",
         "fix":"No action."},
    ])
P("### Proposed text")
P("**Title** (changes: ✏️ → ⭐): ⭐ <TPL_IF_PROF_FEMININ>Η Δασκάλα</TPL_IF_PROF_FEMININ><TPL_ELSE_PROF_FEMININ>Ο Δάσκαλος</TPL_ELSE_PROF_FEMININ> σας, @TPL_PROF_PRENOM@, σάς άφησε ένα σχόλιο")
P("")
P("**Body** (no functional change):")
_, t, b = split_cell(by_country['Chypre']['cell'])
P("```")
P(b)
P("```")
P("")
P("---")
P("")

# Rwanda
single_section('Rwanda[Groupement]',
    "Rwanda's title is broken: it uses `@TPL_MATIERE_FIRST_MAJUS_SMART@` (subject variable) where `@TPL_PROF_PRENOM@` (tutor first name) should be — wrong variable entirely. Body is fine.",
    [
        {"category":"Label","issue":"Title uses `@TPL_MATIERE_FIRST_MAJUS_SMART@` instead of `@TPL_PROF_PRENOM@`. The variable controls the **tutor's first name**; instead the title now reads `Your [Math] teacher left you a comment` — but `@TPL_MATIERE_FIRST_MAJUS_SMART@` outputs the subject the tutor teaches, not their name.",
         "original_fr":"`⭐ Votre professeur @TPL_PROF_PRENOM@ vous a laissé un commentaire`",
         "current":"`⭐ Your @TPL_MATIERE_FIRST_MAJUS_SMART@ teacher left you a comment`",
         "fix":"Replace `@TPL_MATIERE_FIRST_MAJUS_SMART@` with `@TPL_PROF_PRENOM@`: `⭐ Your tutor @TPL_PROF_PRENOM@ has left you a review`"},
        {"category":"Format","issue":"Body's `@TPL_PROF_PRENOM@` placement inside `<TPL_ELSE_AVIS_DEPOSE>` matches French — validator's `variable_block_mismatch` warning here is technically a false positive (the validator's evidence message is truncated mid-sentence).",
         "fix":"No action on body — verify validator interpretation."},
    ])
P("### Proposed text")
P("**Title** (changes: `@TPL_MATIERE_FIRST_MAJUS_SMART@` → `@TPL_PROF_PRENOM@`): ⭐ Your tutor @TPL_PROF_PRENOM@ has left you a review")
P("")
P("**Body** (no change):")
_, t, b = split_cell(by_country['Rwanda[Groupement]']['cell'])
P("```")
P(b)
P("```")
P("")
P("---")
P("")

# Jamaïque
single_section('Jamaïque[Groupement]',
    "Jamaican English title has unmatched appositive comma: `Your tutor, @TPL_PROF_PRENOM@ has left you a review` — opens an appositive with `,` after `tutor` but doesn't close it after the variable.",
    [
        {"category":"Suggestion","issue":"Title has unmatched appositive comma after `tutor` but no closing comma after `@TPL_PROF_PRENOM@`. Either add the closing comma or remove both.",
         "current":"`⭐️ Your tutor, @TPL_PROF_PRENOM@ has left you a review`",
         "fix":"Either: `⭐️ Your tutor, @TPL_PROF_PRENOM@, has left you a review` (with closing comma) — or: `⭐️ Your tutor @TPL_PROF_PRENOM@ has left you a review` (no commas, like sister markets)."},
    ])
P("### Proposed text")
P("**Title** (changes: balance commas — choose option A or B): ⭐️ Your tutor @TPL_PROF_PRENOM@ has left you a review")
P("")
P("**Body** (no change):")
_, t, b = split_cell(by_country['Jamaïque[Groupement]']['cell'])
P("```")
P(b)
P("```")
P("")
P("---")
P("")

# Timor oriental
single_section('Timor oriental',
    "Timor Portuguese has the same `</a>` artifact as Portugal/Cape Vert plus a stray closing `”` at the end of the ELSE branch.",
    [
        {"category":"Format","issue":"Stray `</a>` after `@TPL_PROF_PRENOM@` in IF branch.",
         "current":"`@TPL_PROF_PRENOM@</a> também lhe deixou um excelente comentário`",
         "fix":"Remove `</a>`."},
        {"category":"Grammar","issue":"ELSE branch ends with stray right curly quote `”`.",
         "current":"`...a sua resposta.”`",
         "fix":"Remove the stray `”`."},
    ])
P("### Proposed text")
P("**Title**: ⭐️ Professor(a) @TPL_PROF_PRENOM@ deixou-lhe um comentário")
P("")
P("**Body** (changes: remove `</a>` and trailing `”`):")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|O meu painel de controlo[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Olá <b>@TPL_MEMBRE_PRENOM@</b>, @TPL_PROF_PRENOM@ também lhe deixou um excelente comentário sobre as suas aulas: Dedique alguns minutos [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>para lhe responder</u>[/LIEN]. @TPL_PROF_PRENOM@ aguarda com entusiasmo a sua resposta. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Ver o comentário[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# Kazakhstan — empty translation
single_section('Kazakhstan',
    "Title and body are entirely empty. Per skill protocol, an AI translation is generated below from the French source for human review.",
    [
        {"category":"Empty","issue":"Both `Titre:` and `corps` fields are blank. All variables, conditionals, links, and emoji are missing.",
         "fix":"Provide a Kazakh translation matching the French structure (see proposed text below — AI-proposed)."},
    ])
P("### Proposed text")
P("> **MANDATORY — Empty translations**: Generated AI translation from French source. Every field marked for human review.")
P("")
P("**Title**: ⭐ Сіздің оқытушыңыз @TPL_PROF_PRENOM@ сізге пікір қалдырды `[AI-proposed — human review required]`")
P("")
P("**Body** `[AI-proposed — human review required]`:")
P("```")
P('<TPL_IF_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Сәлеметсіз бе, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ сабақтарыңыз туралы жақсы пікір қалдырды: "<i><b>@TPL_AVIS_COMMENTAIRE@</b></i>" [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Менің бақылау тақтасы[/BOUTON]</TPL_IF_AVIS_DEPOSE><TPL_ELSE_AVIS_DEPOSE>[LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|@TPL_PROF_PHOTO@[/LIEN] Сәлеметсіз бе, <b>@TPL_MEMBRE_PRENOM@</b>! @TPL_PROF_PRENOM@ сабақтарыңыз туралы жылы пікір қалдырды. Бірнеше минут уақыт бөліп, [LIEN][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|<u>оған жауап беріңіз</u>[/LIEN]. @TPL_PROF_PRENOM@ сіздің жауабыңызды күтуде. [BOUTON][URL_QUI_CONNECTE|@TPL_AVIS_URL_REPONSE@]|Пікірді қарау[/BOUTON]</TPL_ELSE_AVIS_DEPOSE>')
P("```")
P("")
P("---")
P("")

# ============ MARKETS WITH NO ISSUES ============
clean_markets = [c for c in all_countries if not struct_by[c] and not ai_by[c]]
P("## Markets with no issues")
if clean_markets:
    P(", ".join(clean_markets))
else:
    P("No issues found.")
P("")

# Write
out_path = f"reports/review-{notif_id}-{today}.md"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(lines))
print(f"Wrote {out_path}: {sum(len(l) for l in lines)} bytes, items={ITEM[0]}")
