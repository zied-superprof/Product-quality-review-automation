# Superprof Translation Review Rules

## Subject variable rules

**`@TPL_MATIERE_DE_MATIERE@`** — article + subject compound (e.g. "d'histoire", "de matemáticas")
- Valid for: `fr es pt it ar pl sk cs ro ru uk bg sr hr sl el hu lt lv et`
- Do NOT use for: `en de nl sv no da fi tr ko ja zh zh-TW th vi id ms he`
- Flag as **error** only if the language is in the do-not-use list, OR if the variable appears inside `<TPL_LOOP_ANNONCES>` (wrong structural position — should be `@TPL_ANNONCE_AFFICHE_QUI_CONNECTE@` there)

**`@TPL_MATIERE_FIRST_MAJUS_SMART@`** — capitalized subject name (smart variant)
- Preferred for: `en de nl sv no da fi tr ko ja zh zh-TW id ms he`
- Flag `@TPL_MATIERE_FIRST_MAJUS@` (non-smart) as a **warning** for any market — SMART variant is preferred

**`@TPL_MATIERE_MINUS_SMART@`** — lowercase subject name (smart variant)
- Preferred for standalone subject (no article compound) in: `pl sk cs ro ru uk bg sr hr sl el hu lt lv et`
- Flag `@TPL_MATIERE_MINUS@` or `@TPL_MATIERE_NOM@` as a **warning** — SMART variant is preferred
- `@TPL_MATIERE_NOM@` is **deprecated** — always flag as warning

## Consistency rule

The same subject variable must be used in both title and body. Mismatches (e.g. `@TPL_MATIERE_MINUS_SMART@` in title but `@TPL_MATIERE_NOM@` in body) are an **error**.

## Formality rules

**Formal address required** — flag informal address as error:
`fr pt pl cs sk bg tr uk ja ko zh zh-TW ar th vi ms hi bn ca eu af`

**Informal address is brand standard** — do NOT flag:
`sv no da fi he de it nl ru ro sr bs hr sl el hu id es`
- `es_AR`: uses Rioplatense "vos" — confirmed brand standard, never flag

**Neutral** (no distinction):
`en ga sw`

## General variable rules

- All `@TPL_*@` variables from the French source must be preserved exactly (names must not be translated)
- `[BOUTON]`, `[LIEN]`, `[TITRE]` custom markup must be balanced and count-matched with French
- Conditionals `<TPL_IF_*>...</TPL_IF_*>` must have matching closing tags
- URL variables must not be modified

## Common errors to flag

| Issue | Severity |
|-------|----------|
| `@TPL_MATIERE_DE_MATIERE@` in English/German/Dutch/CJK/Nordic market | Error |
| Title/body use different subject variables | Error |
| Empty translation (title and body both blank) | Error |
| `@TPL_MATIERE_NOM@` anywhere | Warning |
| `@TPL_MATIERE_FIRST_MAJUS@` (non-smart) | Warning |
| `@TPL_MATIERE_MINUS@` for declension markets | Warning |
| Missing 💛 emoji when French source has it | Warning |
| Extra text outside template structure (e.g. "Atentamente, Equipo Superprof.") | Warning |
| Malformed CSS: `style=";text-align:…"` (leading semicolon) | Warning |
| `sus necesidades` used with informal greeting in Spanish | Warning |
| Typo in Russian: "В аш" (split word), "здвёзд" → "звёзд" | Warning |
