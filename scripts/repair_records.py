#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'

MINISTRY_PATTERNS = [
    r'([가-힣A-Za-z·]+부)',
    r'([가-힣A-Za-z·]+청)',
    r'([가-힣A-Za-z·]+처)',
    r'([가-힣A-Za-z·]+위원회)',
    r'([가-힣A-Za-z·]+원)',
    r'([가-힣A-Za-z·]+실)',
]


def normalize_text(value: str) -> str:
    value = html.unescape(value or '')
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def slugify(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r'[^0-9A-Za-z가-힣]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('_')
    return value[:80] or 'untitled'


def infer_ministry(title: str, body: str) -> str:
    for pattern in MINISTRY_PATTERNS:
        m = re.search(pattern, title)
        if m:
            return m.group(1)
    for line in body.splitlines()[:12]:
        line = normalize_text(line)
        if not line:
            continue
        for pattern in MINISTRY_PATTERNS:
            m = re.search(pattern, line)
            if m:
                return m.group(1)
    return ''


def parse_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, text
    meta = {}
    body_start = 0
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == '---':
            body_start = i + 1
            break
        if ': ' in line:
            k, v = line.split(': ', 1)
            meta[k.strip()] = v.strip().strip('"')
    body = '\n'.join(lines[body_start:])
    return meta, body


def rebuild(meta: dict, body: str) -> str:
    ordered = [
        'title', 'ministry', 'approve_date', 'news_item_id',
        'grouping_code', 'original_url', 'attachment_count', 'source'
    ]
    lines = ['---']
    for key in ordered:
        if key not in meta:
            continue
        val = str(meta[key])
        if key == 'attachment_count' and val.isdigit():
            lines.append(f'{key}: {val}')
        else:
            lines.append(f'{key}: "{val.replace(chr(34), chr(39))}"')
    lines += ['---', '', body.strip(), '']
    return '\n'.join(lines)


def main():
    updated = 0
    renamed = 0
    for path in sorted(DATA_DIR.rglob('*.md')):
        if path.name == 'README.md':
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        meta, body = parse_frontmatter(text)
        if not meta:
            continue
        title = normalize_text(meta.get('title', ''))
        ministry = normalize_text(meta.get('ministry', ''))
        body = body.replace('&#xFF62;', '｢').replace('&#xFF63;', '｣')
        body = html.unescape(body)
        inferred = infer_ministry(title, body)
        display_ministry = ministry or inferred or '미분류'
        changed = False
        if meta.get('title', '') != title:
            meta['title'] = title
            changed = True
        if meta.get('ministry', '') != display_ministry:
            meta['ministry'] = display_ministry
            changed = True
        new_text = rebuild(meta, body)
        if changed or new_text != text:
            path.write_text(new_text, encoding='utf-8')
            updated += 1
        prefix = path.stem.split('_', 1)[0]
        new_name = f"{prefix}_{slugify(display_ministry)}_{slugify(title)}.md"
        if path.name != new_name:
            target = path.with_name(new_name)
            if not target.exists():
                path.rename(target)
                renamed += 1
    print(f'UPDATED {updated}')
    print(f'RENAMED {renamed}')


if __name__ == '__main__':
    main()
