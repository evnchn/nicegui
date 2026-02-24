#!/usr/bin/env python3
"""Fix backtick count mismatches in translation CSVs.

Strategy:
- For ``code`` (RST) vs `code` (markdown) mismatches: match backtick style to English
- For translations with 0 backticks where English has many: fall back to English text
- For translations with extra backticks: remove extraneous backticks to match English style
"""
import csv
import re
import sys
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent / 'website' / 'translations'


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return {row['sha256']: row['text'] for row in csv.DictReader(f) if row.get('sha256')}


def read_en_csv():
    en_file = TRANSLATIONS_DIR / 'en.csv'
    with en_file.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return [(row['sha256'], row['text']) for row in reader if row.get('sha256') and row.get('text')]


def save_csv(lang, translations, en_entries):
    lang_file = TRANSLATIONS_DIR / f'{lang}.csv'
    with lang_file.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sha256', 'text'])
        writer.writeheader()
        for h, _ in en_entries:
            writer.writerow({'sha256': h, 'text': translations.get(h, '')})


# Extract backtick-delimited tokens with their positions and style
_BACKTICK_TOKEN_RE = re.compile(r'(`{1,3})([^`]+?)\1')


def extract_backtick_tokens(text):
    """Extract all backtick-delimited tokens: [(start, end, backtick_count, content), ...]"""
    tokens = []
    for m in _BACKTICK_TOKEN_RE.finditer(text):
        tokens.append((m.start(), m.end(), len(m.group(1)), m.group(2)))
    return tokens


def fix_backtick_style(en_text, tr_text):
    """Fix backtick style in translation to match English.

    Handles:
    - RST ``code`` in English → `code` in translation (needs to become ``code``)
    - `code` in English → ``code`` in translation (needs to become `code`)
    - Extra backtick-wrapped tokens that shouldn't be wrapped
    - Missing backtick-wrapped tokens
    """
    en_count = en_text.count('`')
    tr_count = tr_text.count('`')

    if en_count == tr_count:
        return tr_text

    # If translation has 0 backticks and English has many, fallback to English
    if tr_count == 0 and en_count > 0:
        return en_text

    # Extract tokens from both
    en_tokens = extract_backtick_tokens(en_text)
    tr_tokens = extract_backtick_tokens(tr_text)

    if not en_tokens or not tr_tokens:
        # Can't match tokens, fallback to English if very different
        if abs(en_count - tr_count) > en_count * 0.5:
            return en_text
        return tr_text

    # Build a map of content -> backtick style from English
    en_style = {}
    for _, _, bt_count, content in en_tokens:
        en_style[content.strip()] = bt_count

    # Fix each token in translation to match English style
    result = tr_text
    replacements = []
    for start, end, tr_bt_count, content in reversed(tr_tokens):
        content_key = content.strip()
        if content_key in en_style:
            en_bt_count = en_style[content_key]
            if en_bt_count != tr_bt_count:
                old = '`' * tr_bt_count + content + '`' * tr_bt_count
                new = '`' * en_bt_count + content + '`' * en_bt_count
                result = result[:start] + new + result[end:]

    # Check if we fixed it
    if result.count('`') == en_count:
        return result

    # If still not matching, try a different approach:
    # Look for content that should have backticks but doesn't, or vice versa
    en_contents = {content.strip() for _, _, _, content in en_tokens}
    tr_contents = {content.strip() for _, _, _, content in extract_backtick_tokens(result)}

    # If we're close enough and the fix made progress, accept it
    if abs(result.count('`') - en_count) < abs(tr_count - en_count):
        return result

    # For remaining cases where we couldn't fix it, if the difference is large,
    # fall back to English
    if abs(result.count('`') - en_count) > 4:
        return en_text

    return result


def main():
    en_entries = read_en_csv()
    en_dict = dict(en_entries)

    for lang in ['de', 'ko']:
        translations = read_csv(TRANSLATIONS_DIR / f'{lang}.csv')
        fixed = 0

        for h, en_text in en_entries:
            tr_text = translations.get(h, '')
            if not tr_text.strip():
                continue

            en_count = en_text.count('`')
            tr_count = tr_text.count('`')

            if en_count == 0 or en_count == tr_count:
                continue

            new_text = fix_backtick_style(en_text, tr_text)
            if new_text != tr_text:
                new_count = new_text.count('`')
                if new_count == en_count:
                    translations[h] = new_text
                    fixed += 1
                    print(f'  FIXED {h[:12]} {lang}: {tr_count} -> {en_count} backticks')
                else:
                    print(f'  PARTIAL {h[:12]} {lang}: {tr_count} -> {new_count} (need {en_count})')

        if fixed:
            save_csv(lang, translations, en_entries)
            print(f'{lang}: fixed {fixed} entries')
        else:
            print(f'{lang}: no fixes needed')


if __name__ == '__main__':
    main()
